export const runtime = 'edge';

import { NextResponse } from "next/server";

type Provider = "Moorcheh" | "Anthropic" | "Gemini" | "Nvidia" | "OpenAI" | "Custom";

type ModelConfig = {
  provider: Provider | string;
  model: string;
  apiKey?: string;
  baseUrl?: string;
};

type EvaluateRequestBody = {
  inference?: ModelConfig;
  judge?: ModelConfig;
  prompt?: string;
  agentId?: string;
  groundTruth?: string;
  dataset?: string;
};

type MoorchehSearchResult = {
  text?: string;
};

type MoorchehSearchResponse = {
  results?: MoorchehSearchResult[];
};

type Evaluation = {
  groundTruth?: string;
  score?: number;
  reasoning?: string;
};

type JudgeResponse = {
  score?: number;
  reasoning?: string;
};

function getProviderDefaultKey(provider: string | undefined, genericKey?: string) {
  if (provider === "Anthropic") return process.env.ANTHROPIC_API_KEY || genericKey;
  if (provider === "Gemini") return process.env.GEMINI_API_KEY || genericKey;
  if (provider === "Nvidia") return process.env.NVIDIA_API_KEY || genericKey;
  if (provider === "OpenAI") return process.env.OPENAI_API_KEY || genericKey;
  if (provider === "Moorcheh") return process.env.MOORCHEH_API_KEY || genericKey;
  if (provider === "Custom") return process.env.INFERENCE_API_KEY || genericKey;
  return genericKey;
}

export async function POST(req: Request) {
  try {
    const body = (await req.json()) as EvaluateRequestBody;
    const { inference, judge, prompt, agentId, groundTruth, dataset } = body;

    if (!inference || !prompt || !agentId) {
      return NextResponse.json(
        { error: "Missing required fields: inference, prompt, and agentId are required." },
        { status: 400 }
      );
    }

    // Resolve keys by provider to avoid sending secrets to the wrong API vendor.
    const inferenceDefaultKey = getProviderDefaultKey(
      inference?.provider,
      process.env.INFERENCE_API_KEY
    );
    const judgeDefaultKey = getProviderDefaultKey(
      judge?.provider,
      process.env.JUDGE_API_KEY
    );

    // Use user-provided keys if available, otherwise fall back to server environments
    const finalInferenceKey = inference?.apiKey || inferenceDefaultKey;
    const finalJudgeKey = judge?.apiKey || judgeDefaultKey;
    
    // Moorcheh search must only ever use a Moorcheh key.
    const moorchehSearchKey = process.env.MOORCHEH_API_KEY;
    const moorchehNamespace = `memanto_agent_${agentId}`;

    if (!finalInferenceKey) {
      return NextResponse.json(
        { error: "Inference API key is required." },
        { status: 400 }
      );
    }

    if (judge && !finalJudgeKey) {
      return NextResponse.json(
        { error: `Judge API key is required for provider: ${judge.provider}.` },
        { status: 400 }
      );
    }
    
    if (inference.provider !== "Moorcheh" && !moorchehSearchKey) {
      return NextResponse.json(
        { error: "A Moorcheh API Key is required to search the memory layer. Please set MOORCHEH_API_KEY." },
        { status: 400 }
      );
    }

    // 1. SEARCH MEMORY (RAG)
    // ONLY perform the vector search if we are NOT using Moorcheh for inference.
    // If we are using Moorcheh for inference, it handles its own RAG via the /answer endpoint automatically.
    let fullPrompt = prompt;
    let memories: MoorchehSearchResult[] = [];
    
    if (inference.provider !== "Moorcheh") {
      const searchRes = await fetch("https://api.moorcheh.ai/v1/search", {
        method: "POST",
        headers: {
          "x-api-key": moorchehSearchKey as string,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: prompt,
          namespaces: [moorchehNamespace], 
          top_k: 100,
          kiosk_mode: true,
          threshold: 0.05
        }),
      });

      if (!searchRes.ok) {
        const errData = await searchRes.text();
        console.error("Moorcheh Search Error:", errData);
        throw new Error(`Moorcheh Search failed: ${searchRes.statusText}`);
      }

      const searchData = (await searchRes.json()) as MoorchehSearchResponse;
      memories = searchData.results || [];
      
      let contextStr = "No relevant context found.";
      if (memories.length > 0) {
        // Map over the text results from Moorcheh
        contextStr = memories.map((m) => `- ${m.text ?? ""}`).join("\n");
      }

      // Determine the prompt header based on dataset
      const LONGMEM_HEADER = "You are a helpful assistant evaluating memories from a long-term session.";
      const LOCOMO_HEADER = "You are a helpful assistant evaluating events from a user's location and communication history.";
      const promptHeader = dataset === "longmem" ? LONGMEM_HEADER : LOCOMO_HEADER;
      
      fullPrompt = `${promptHeader}\n\n# CONTEXT:\n${contextStr}\n\n# QUESTION:\n${prompt}\n\n# ANSWER:`;
    }

    // 2. GENERATE ANSWER USING INFERENCE LLM
    let answer = "";
    
    if (inference.provider === "Moorcheh") {
      // If using Moorcheh for inference, we hit the /v1/answer endpoint as before
      // but we send the raw prompt (since Moorcheh /answer handles its own RAG if a namespace is provided)
      const response = await fetch("https://api.moorcheh.ai/v1/answer", {
        method: "POST",
        headers: {
          "x-api-key": finalInferenceKey,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: prompt,
          namespace: moorchehNamespace, 
        }),
      });

      if (!response.ok) {
        const errData = await response.text();
        throw new Error(`Inference (Moorcheh) API error: ${response.statusText} - ${errData}`);
      }
      const data = await response.json();
      answer = data.answer || "No answer generated.";
      
    } else if (inference.provider === "OpenAI" || inference.provider === "Custom" || inference.provider === "Nvidia") {
      // Example implementation for OpenAI or Custom OpenAI-compatible endpoints
      let baseUrl = inference.baseUrl || "https://api.openai.com/v1";
      if (inference.provider === "Nvidia") {
        baseUrl = "https://integrate.api.nvidia.com/v1";
      }
      const response = await fetch(`${baseUrl.replace(/\/$/, "")}/chat/completions`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${finalInferenceKey}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: inference.model,
          messages: [{ role: "user", content: fullPrompt }],
          temperature: 0,
        }),
      });
      
      if (!response.ok) {
        const errData = await response.text();
        throw new Error(`Inference (${inference.provider}) API error: ${response.statusText} - ${errData}`);
      }
      const data = await response.json();
      answer = data.choices?.[0]?.message?.content || "No answer generated.";
      
    } else if (inference.provider === "Anthropic") {
      const response = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: {
          "x-api-key": finalInferenceKey as string,
          "anthropic-version": "2023-06-01",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: inference.model,
          max_tokens: 1024,
          messages: [{ role: "user", content: fullPrompt }],
          temperature: 0,
        }),
      });
      
      if (!response.ok) {
        const errData = await response.text();
        throw new Error(`Inference (Anthropic) API error: ${response.statusText} - ${errData}`);
      }
      const data = await response.json();
      answer = data.content?.[0]?.text || "No answer generated.";

    } else if (inference.provider === "Gemini") {
      const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${inference.model}:generateContent?key=${finalInferenceKey}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          contents: [{ parts: [{ text: fullPrompt }] }],
          generationConfig: {
            temperature: 0,
          }
        }),
      });
      
      if (!response.ok) {
        const errData = await response.text();
        throw new Error(`Inference (Gemini) API error: ${response.statusText} - ${errData}`);
      }
      const data = await response.json();
      answer = data.candidates?.[0]?.content?.parts?.[0]?.text || "No answer generated.";

    } else {
      answer = `[Mock Inference] Using ${inference.provider} (${inference.model}). Evaluated on Agent: ${agentId}.\n\nContext found: ${memories.length} items.`;
    }

    // 3. EVALUATE ANSWER USING JUDGE LLM
    const evaluation: Evaluation = {};
    if (groundTruth) {
      evaluation.groundTruth = groundTruth;
    }

    // Only run the judge if a judge configuration was provided and we have an answer to evaluate
    if (judge && answer) {
      const judgePrompt = `You are an expert AI judge evaluating the accuracy of a generated answer against a known ground truth.

Evaluate the following generated answer to see if it correctly addresses the question and aligns with the ground truth.
If it is correct, output a score of 1. If it is incorrect or fails to answer the question, output a score of 0.

# Question:
${prompt}

# Ground Truth:
${groundTruth || "None provided"}

# Generated Answer:
${answer}

Analyze the response and state your reasoning, then output a final score. 
Output your response in valid JSON format ONLY, like this:
{ "score": 1, "reasoning": "your reasoning here" }`;

      let judgeResText = "";
      
      if (judge.provider === "Moorcheh") {
         // Use the /v1/answer endpoint but without a namespace (raw LLM generation)
         const judgeRes = await fetch("https://api.moorcheh.ai/v1/answer", {
            method: "POST",
            headers: {
              "x-api-key": finalJudgeKey as string,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              query: judgePrompt,
              namespace: "", // Empty namespace for direct LLM pass-through
            }),
          });
          
          if (judgeRes.ok) {
            const judgeData = await judgeRes.json();
            judgeResText = judgeData.answer || "";
          } else {
             console.error("Moorcheh Judge failed:", await judgeRes.text());
          }
      } else if (judge.provider === "OpenAI" || judge.provider === "Custom" || judge.provider === "Nvidia") {
         let baseUrl = judge.baseUrl || "https://api.openai.com/v1";
         if (judge.provider === "Nvidia") baseUrl = "https://integrate.api.nvidia.com/v1";
         
         const judgeRes = await fetch(`${baseUrl.replace(/\/$/, "")}/chat/completions`, {
            method: "POST",
            headers: {
              "Authorization": `Bearer ${finalJudgeKey}`,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              model: judge.model,
              messages: [{ role: "user", content: judgePrompt }],
              temperature: 0,
              response_format: { type: "json_object" } // Force JSON output if supported
            }),
          });
          
          if (judgeRes.ok) {
             const data = await judgeRes.json();
             judgeResText = data.choices?.[0]?.message?.content || "";
          } else {
             console.error(`${judge.provider} Judge failed:`, await judgeRes.text());
          }
      } else if (judge.provider === "Anthropic") {
          const response = await fetch("https://api.anthropic.com/v1/messages", {
            method: "POST",
            headers: {
              "x-api-key": finalJudgeKey as string,
              "anthropic-version": "2023-06-01",
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              model: judge.model,
              max_tokens: 1024,
              messages: [{ role: "user", content: judgePrompt }],
              temperature: 0,
            }),
          });
          
          if (response.ok) {
            const data = await response.json();
            judgeResText = data.content?.[0]?.text || "";
          } else {
             console.error("Anthropic Judge failed:", await response.text());
          }
      } else if (judge.provider === "Gemini") {
          const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${judge.model}:generateContent?key=${finalJudgeKey}`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              contents: [{ parts: [{ text: judgePrompt }] }],
              generationConfig: { temperature: 0, responseMimeType: "application/json" }
            }),
          });
          
          if (response.ok) {
            const data = await response.json();
            judgeResText = data.candidates?.[0]?.content?.parts?.[0]?.text || "";
          } else {
             console.error("Gemini Judge failed:", await response.text());
          }
      } else {
         evaluation.score = 1;
         evaluation.reasoning = `[Mock Judge] Actual API call logic for ${judge.provider} (${judge.model}) needs to be implemented.`;
      }
      
      // Parse the JSON output from whichever LLM ran
      if (judgeResText) {
          try {
           const parsed = JSON.parse(judgeResText.replace(/```json|```/g, "").trim()) as JudgeResponse;
           if (typeof parsed.score === "number") {
            evaluation.score = parsed.score;
           }
           if (typeof parsed.reasoning === "string") {
            evaluation.reasoning = parsed.reasoning;
           }
         } catch {
             evaluation.score = 0;
             evaluation.reasoning = `Failed to parse judge output as JSON. Output was: ${judgeResText}`;
          }
      }
    }

    return NextResponse.json({ 
      answer,
      evaluation: Object.keys(evaluation).length > 0 ? evaluation : undefined 
    });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "Internal Server Error";
    console.error("Evaluation API Error:", error);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
