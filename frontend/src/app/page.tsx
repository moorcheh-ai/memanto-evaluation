"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Send, Gavel, Cpu, BookOpen } from "lucide-react";

// Model mappings based on interactive_benchmark.py
const MODELS_BY_PROVIDER: Record<string, string[]> = {
  Moorcheh: [
    "anthropic.claude-sonnet-4-6",
    "anthropic.claude-opus-4-6-v1",
    "meta.llama4-maverick-17b-instruct-v1:0",
    "amazon.nova-pro-v1:0",
    "deepseek.r1-v1:0",
    "deepseek.v3.2",
    "openai.gpt-oss-120b-1:0",
    "qwen.qwen3-32b-v1:0",
    "qwen.qwen3-next-80b-a3b"
  ],
  Anthropic: [
    "claude-4-6-sonnet-latest", 
    "claude-4-6-opus-latest", 
    "claude-4-5-sonnet-latest",
    "claude-3-7-sonnet-20250219",
    "claude-3-5-sonnet-latest",
    "claude-3-5-haiku-latest",
    "claude-3-opus-latest"
  ],
  Gemini: [
    "gemini-3.1-pro-preview",
    "gemini-3-pro-preview", 
    "gemini-3-flash-preview",
    "gemini-2.5-pro", 
    "gemini-2.5-flash",
    "gemini-2.0-pro-exp",
    "gemini-1.5-pro",
    "gemini-1.5-flash"
  ],
  OpenAI: [
    "gpt-5", 
    "gpt-5-mini",
    "gpt-4.5-preview", 
    "o3-mini", 
    "o1", 
    "o1-mini",
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo"
  ],
  Nvidia: [
    "meta/llama-4-maverick-17b-instruct", 
    "meta/llama-3.3-70b-instruct", 
    "meta/llama3-70b-instruct",
    "deepseek-ai/deepseek-r1",
    "deepseek-ai/deepseek-v3",
    "mistralai/mixtral-8x22b-instruct",
    "mistralai/mistral-large",
    "nvidia/nemotron-4-340b-instruct"
  ],
  Custom: []
};

type LongMemItem = { question_id: string; question: string; answer: string; question_date?: string };
type LoCoMoItem = { sample_id: string; user_id: string; qa: { question: string; answer: string; category: number }[] };
type Evaluation = { score?: number; reasoning?: string; groundTruth?: string };
type ChatMessage = { role: string; content: string; eval?: Evaluation };

export default function Home() {
  // Inference LLM State
  const [provider, setProvider] = useState("Moorcheh");
  const [modelDropdown, setModelDropdown] = useState(MODELS_BY_PROVIDER["Moorcheh"][0]);
  const [customModel, setCustomModel] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [customBaseUrl, setCustomBaseUrl] = useState("");

  // Judge LLM State
  const [useSameJudge, setUseSameJudge] = useState(true);
  const [judgeProvider, setJudgeProvider] = useState("Moorcheh");
  const [judgeModelDropdown, setJudgeModelDropdown] = useState(MODELS_BY_PROVIDER["Moorcheh"][0]);
  const [judgeCustomModel, setJudgeCustomModel] = useState("");
  const [judgeApiKey, setJudgeApiKey] = useState("");
  const [judgeCustomBaseUrl, setJudgeCustomBaseUrl] = useState("");

  // Context / Dataset State
  const [datasetType, setDatasetType] = useState<"locomo" | "longmem">("longmem");
  const [longmemData, setLongmemData] = useState<LongMemItem[]>([]);
  const [locomoData, setLocomoData] = useState<LoCoMoItem[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  
  // Selected context item
  const [selectedLongmemId, setSelectedLongmemId] = useState<string>("");
  const [selectedLocomoSampleId, setSelectedLocomoSampleId] = useState<string>("");
  const [selectedLocomoQuestionIdx, setSelectedLocomoQuestionIdx] = useState<string>("");

  const [prompt, setPrompt] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const getLocomoQuestion = (sampleId: string, questionIdx: string) => {
    const sample = locomoData.find((d) => d.sample_id === sampleId);
    const idx = Number(questionIdx);
    return sample?.qa[idx]?.question || "";
  };

  // Fetch datasets on mount
  useEffect(() => {
    fetch("/longmemeval_s_cleaned.json")
      .then(res => res.json())
      .then((data: LongMemItem[]) => {
        setLongmemData(data);
        if (data.length > 0) {
          setSelectedLongmemId(data[0].question_id);
          if (datasetType === "longmem") {
            setPrompt(data[0].question);
          }
        }
      })
      .catch(err => console.error("Failed to load LongMem data:", err));

    fetch("/locomo10.json")
      .then(res => res.json())
      .then((data: LoCoMoItem[]) => {
        setLocomoData(data);
        if (data.length > 0) {
          setSelectedLocomoSampleId(data[0].sample_id);
          setSelectedLocomoQuestionIdx("0");
          if (datasetType === "locomo") {
            setPrompt(data[0].qa[0]?.question || "");
          }
        }
      })
      .catch(err => console.error("Failed to load LoCoMo data:", err));
  }, [datasetType]);

  const handleClearKey = () => {
    setApiKey("");
    setCustomBaseUrl("");
  };

  const handleClearJudgeKey = () => {
    setJudgeApiKey("");
    setJudgeCustomBaseUrl("");
  };

  // Filter longmem data based on search query
  const filteredLongmemData = longmemData.filter(d => 
    d.question.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    const userMessage = { role: "user", content: prompt };
    setMessages((prev) => [...prev, userMessage]);
    setPrompt("");
    setIsLoading(true);

    // Determine final model strings based on custom dropdown selections
    const finalModel = modelDropdown === "custom" || provider === "Custom" ? customModel : modelDropdown;
    const finalJudgeModel = judgeModelDropdown === "custom" || judgeProvider === "Custom" ? judgeCustomModel : judgeModelDropdown;

    // Determine Agent ID based on selection
    const agentId = datasetType === "longmem" 
      ? `longmem_eval_${selectedLongmemId}` 
      : `locomo_eval_${selectedLocomoSampleId}`;
      
    // Get Ground Truth for the Judge
    // Only pass ground truth if the prompt exactly matches the benchmark question
    let groundTruth = "";
    if (datasetType === "longmem") {
      const item = longmemData.find(d => d.question_id === selectedLongmemId);
      if (item && item.question === userMessage.content) {
        groundTruth = item.answer;
      }
    } else {
      const sample = locomoData.find(d => d.sample_id === selectedLocomoSampleId);
      if (sample && sample.qa[parseInt(selectedLocomoQuestionIdx)]) {
        if (sample.qa[parseInt(selectedLocomoQuestionIdx)].question === userMessage.content) {
          groundTruth = sample.qa[parseInt(selectedLocomoQuestionIdx)].answer;
        }
      }
    }

    try {
      const response = await fetch("/api/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          inference: {
            provider,
            model: finalModel,
            apiKey: apiKey || undefined,
            baseUrl: provider === "Custom" ? customBaseUrl : undefined
          },
          judge: {
            provider: useSameJudge ? provider : judgeProvider,
            model: useSameJudge ? finalModel : finalJudgeModel,
            apiKey: useSameJudge ? (apiKey || undefined) : (judgeApiKey || undefined),
            baseUrl: useSameJudge 
              ? (provider === "Custom" ? customBaseUrl : undefined) 
              : (judgeProvider === "Custom" ? judgeCustomBaseUrl : undefined)
          },
          prompt: userMessage.content,
          agentId,
          dataset: datasetType,
          groundTruth
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Failed to generate response");
      }

      setMessages((prev) => [
        ...prev, 
        { 
          role: "assistant", 
          content: data.answer,
          eval: data.evaluation
        }
      ]);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "Unknown error";
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${message}` },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col flex-1 items-center bg-zinc-50 font-sans dark:bg-black min-h-screen">
      <header className="w-full flex justify-between items-center py-6 px-8 md:px-16 bg-white dark:bg-black border-b border-black/[.08] dark:border-white/[.145]">
        <div className="flex items-center gap-2">
          <span className="text-xl font-semibold tracking-tight text-black dark:text-zinc-50">
            Memanto Evaluation
          </span>
        </div>
      </header>

      <main className="flex flex-1 w-full max-w-7xl flex-col py-12 px-8 md:px-16 bg-zinc-50 dark:bg-black">
        <div className="flex flex-col items-center gap-4 text-center sm:items-start sm:text-left mb-8">
          <h1 className="max-w-2xl text-4xl font-semibold leading-tight tracking-tight text-black dark:text-zinc-50">
            Interactive Model Testing
          </h1>
          <p className="max-w-2xl text-lg leading-8 text-zinc-600 dark:text-zinc-400">
            Select a benchmark question below to test how your models query the memory layer. Evaluate the results using a secondary LLM Judge.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Settings Sidebar */}
          <div className="lg:col-span-4 space-y-6">
            
            {/* Context Selection Settings */}
            <Card className="h-fit shadow-sm border-black/[.08] dark:border-white/[.145]">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-2 text-lg font-medium text-zinc-950 dark:text-zinc-50">
                  <BookOpen className="w-5 h-5 text-emerald-600" />
                  Context Question
                </CardTitle>
                <p className="text-xs text-zinc-500">Choose a ground-truth question from the benchmarks. This sets the Agent ID.</p>
              </CardHeader>
              <CardContent className="space-y-5">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-zinc-950 dark:text-zinc-50">Dataset</label>
                  <Select
                    value={datasetType}
                    onChange={(e) => {
                      const nextDataset = e.target.value as "locomo" | "longmem";
                      setDatasetType(nextDataset);
                      if (nextDataset === "longmem") {
                        const item = longmemData.find((d) => d.question_id === selectedLongmemId) || longmemData[0];
                        if (item) {
                          setSelectedLongmemId(item.question_id);
                          setPrompt(item.question);
                        }
                      } else {
                        const sample = locomoData.find((d) => d.sample_id === selectedLocomoSampleId) || locomoData[0];
                        if (sample) {
                          setSelectedLocomoSampleId(sample.sample_id);
                          setSelectedLocomoQuestionIdx("0");
                          setPrompt(sample.qa[0]?.question || "");
                        }
                      }
                    }}
                  >
                    <option value="longmem">LongMem (500 Samples)</option>
                    <option value="locomo">LoCoMo (10 Samples)</option>
                  </Select>
                </div>

                {datasetType === "longmem" && (
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-950 dark:text-zinc-50 flex justify-between">
                      Question
                      {selectedLongmemId && <span className="text-xs text-zinc-500 font-normal">Agent: longmem_eval_{selectedLongmemId}</span>}
                    </label>
                    <Input 
                      placeholder="Search questions..." 
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="text-sm h-9 mb-2"
                    />
                    <Select
                      value={selectedLongmemId}
                      onChange={(e) => {
                        const nextId = e.target.value;
                        setSelectedLongmemId(nextId);
                        const item = longmemData.find((d) => d.question_id === nextId);
                        if (item) setPrompt(item.question);
                      }}
                      disabled={filteredLongmemData.length === 0}
                    >
                      {filteredLongmemData.map(d => (
                        <option key={d.question_id} value={d.question_id}>
                          {d.question.length > 50 ? d.question.substring(0, 50) + "..." : d.question}
                        </option>
                      ))}
                    </Select>
                  </div>
                )}

                {datasetType === "locomo" && (
                  <>
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-zinc-950 dark:text-zinc-50 flex justify-between">
                        Sample User
                        {selectedLocomoSampleId && <span className="text-xs text-zinc-500 font-normal">Agent: locomo_eval_{selectedLocomoSampleId}</span>}
                      </label>
                      <Select 
                        value={selectedLocomoSampleId} 
                        onChange={(e) => {
                          const nextSampleId = e.target.value;
                          setSearchQuery(""); // Clear search when manually changing user
                          setSelectedLocomoSampleId(nextSampleId);
                          setSelectedLocomoQuestionIdx("0");
                          setPrompt(getLocomoQuestion(nextSampleId, "0"));
                        }}
                        disabled={locomoData.length === 0}
                      >
                        {locomoData.map(d => (
                          <option key={d.sample_id} value={d.sample_id}>
                            User {d.user_id} (Sample {d.sample_id})
                          </option>
                        ))}
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-zinc-950 dark:text-zinc-50">Question</label>
                      <Input
                        placeholder="Search questions..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="text-sm h-9 mb-2"
                      />
                      <Select
                        value={selectedLocomoQuestionIdx}
                        onChange={(e) => {
                          const nextQuestionIdx = e.target.value;
                          setSelectedLocomoQuestionIdx(nextQuestionIdx);
                          setPrompt(getLocomoQuestion(selectedLocomoSampleId, nextQuestionIdx));
                        }}
                      >
                        {locomoData
                          .find(d => d.sample_id === selectedLocomoSampleId)?.qa
                          .map((qa, idx) => ({ qa, idx }))
                          .filter(({ qa }) => qa.question.toLowerCase().includes(searchQuery.toLowerCase()))
                          .map(({ qa, idx }) => (
                            <option key={idx} value={idx.toString()}>
                              {qa.question.length > 50 ? qa.question.substring(0, 50) + "..." : qa.question}
                            </option>
                        ))}
                      </Select>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>

            {/* Inference LLM Settings */}
            <Card className="h-fit shadow-sm border-black/[.08] dark:border-white/[.145]">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-2 text-lg font-medium text-zinc-950 dark:text-zinc-50">
                  <Cpu className="w-5 h-5 text-blue-600" />
                  Inference LLM
                </CardTitle>
                <p className="text-xs text-zinc-500">The model generating the initial answers.</p>
              </CardHeader>
              <CardContent className="space-y-5">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-zinc-950 dark:text-zinc-50">Provider</label>
                  <Select
                    value={provider}
                    onChange={(e) => {
                      const nextProvider = e.target.value;
                      setProvider(nextProvider);
                      setModelDropdown(MODELS_BY_PROVIDER[nextProvider]?.[0] || "custom");
                    }}
                  >
                    <option value="Moorcheh">Moorcheh</option>
                    <option value="Anthropic">Anthropic</option>
                    <option value="Gemini">Gemini</option>
                    <option value="OpenAI">OpenAI</option>
                    <option value="Nvidia">Nvidia</option>
                    <option value="Custom">Custom</option>
                  </Select>
                </div>

                {provider === "Custom" ? (
                  <>
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-zinc-950 dark:text-zinc-50">Custom Base URL</label>
                      <Input 
                        placeholder="https://api.custom.com/v1" 
                        value={customBaseUrl}
                        onChange={(e) => setCustomBaseUrl(e.target.value)}
                        className="text-sm h-9"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-zinc-950 dark:text-zinc-50">Custom Model String</label>
                      <Input 
                        placeholder="e.g. custom-llama-8b" 
                        value={customModel}
                        onChange={(e) => setCustomModel(e.target.value)}
                        className="text-sm h-9"
                      />
                    </div>
                  </>
                ) : (
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-950 dark:text-zinc-50">Model</label>
                    <Select value={modelDropdown} onChange={(e) => setModelDropdown(e.target.value)}>
                      {MODELS_BY_PROVIDER[provider]?.map(m => (
                        <option key={m} value={m}>{m}</option>
                      ))}
                      <option value="custom">Other (Enter manually)...</option>
                    </Select>
                    {modelDropdown === "custom" && (
                      <Input 
                        placeholder="Enter exact model string" 
                        value={customModel}
                        onChange={(e) => setCustomModel(e.target.value)}
                        className="text-sm h-9 mt-2"
                      />
                    )}
                  </div>
                )}

                <div className="space-y-2">
                  <label className="text-sm font-medium flex justify-between text-zinc-950 dark:text-zinc-50">API Key</label>
                  <Input 
                    type="password" 
                    placeholder={provider === "Moorcheh" ? "Leave blank to use server key" : "Enter your API key"}
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    autoComplete="new-password"
                    className="font-mono text-sm h-9"
                  />
                  <div className="flex justify-between gap-3 text-xs font-medium pt-1">
                    <span className="text-zinc-500">Keys are not stored locally.</span>
                    <button type="button" onClick={handleClearKey} className="text-red-600 hover:text-red-700 transition-colors">Clear</button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Judge LLM Settings */}
            <Card className="h-fit shadow-sm border-black/[.08] dark:border-white/[.145]">
              <CardHeader className="pb-4">
                <div className="flex justify-between items-center">
                  <CardTitle className="flex items-center gap-2 text-lg font-medium text-zinc-950 dark:text-zinc-50">
                    <Gavel className="w-5 h-5 text-purple-600" />
                    Judge LLM
                  </CardTitle>
                  <label className="flex items-center gap-2 text-sm text-zinc-600 cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={useSameJudge}
                      onChange={(e) => setUseSameJudge(e.target.checked)}
                      className="rounded border-zinc-300 text-black focus:ring-black"
                    />
                    Use Inference LLM
                  </label>
                </div>
                <p className="text-xs text-zinc-500">The model evaluating the accuracy of the answer.</p>
              </CardHeader>
              
              {!useSameJudge && (
                <CardContent className="space-y-5 border-t border-black/[.08] dark:border-white/[.145] pt-5">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-950 dark:text-zinc-50">Judge Provider</label>
                    <Select
                      value={judgeProvider}
                      onChange={(e) => {
                        const nextJudgeProvider = e.target.value;
                        setJudgeProvider(nextJudgeProvider);
                        setJudgeModelDropdown(MODELS_BY_PROVIDER[nextJudgeProvider]?.[0] || "custom");
                      }}
                    >
                      <option value="Moorcheh">Moorcheh</option>
                      <option value="Anthropic">Anthropic</option>
                      <option value="Gemini">Gemini</option>
                      <option value="OpenAI">OpenAI</option>
                      <option value="Nvidia">Nvidia</option>
                      <option value="Custom">Custom</option>
                    </Select>
                  </div>

                  {judgeProvider === "Custom" ? (
                  <>
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-zinc-950 dark:text-zinc-50">Custom Base URL</label>
                      <Input 
                        placeholder="https://api.custom.com/v1" 
                        value={judgeCustomBaseUrl}
                        onChange={(e) => setJudgeCustomBaseUrl(e.target.value)}
                        className="text-sm h-9"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-zinc-950 dark:text-zinc-50">Custom Model String</label>
                      <Input 
                        placeholder="e.g. custom-llama-8b" 
                        value={judgeCustomModel}
                        onChange={(e) => setJudgeCustomModel(e.target.value)}
                        className="text-sm h-9"
                      />
                    </div>
                  </>
                ) : (
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-950 dark:text-zinc-50">Judge Model</label>
                    <Select value={judgeModelDropdown} onChange={(e) => setJudgeModelDropdown(e.target.value)}>
                      {MODELS_BY_PROVIDER[judgeProvider]?.map(m => (
                        <option key={m} value={m}>{m}</option>
                      ))}
                      <option value="custom">Other (Enter manually)...</option>
                    </Select>
                    {judgeModelDropdown === "custom" && (
                      <Input 
                        placeholder="Enter exact model string" 
                        value={judgeCustomModel}
                        onChange={(e) => setJudgeCustomModel(e.target.value)}
                        className="text-sm h-9 mt-2"
                      />
                    )}
                  </div>
                )}

                  <div className="space-y-2">
                    <label className="text-sm font-medium flex justify-between text-zinc-950 dark:text-zinc-50">Judge API Key</label>
                    <Input 
                      type="password" 
                      placeholder={judgeProvider === "Moorcheh" ? "Leave blank to use server key" : "Enter your API key"}
                      value={judgeApiKey}
                      onChange={(e) => setJudgeApiKey(e.target.value)}
                      autoComplete="new-password"
                      className="font-mono text-sm h-9"
                    />
                    <div className="flex justify-between gap-3 text-xs font-medium pt-1">
                      <span className="text-zinc-500">Keys are not stored locally.</span>
                      <button type="button" onClick={handleClearJudgeKey} className="text-red-600 hover:text-red-700 transition-colors">Clear</button>
                    </div>
                  </div>
                </CardContent>
              )}
            </Card>

          </div>

          {/* Chat Interface */}
          <Card className="lg:col-span-8 flex flex-col h-[750px] shadow-sm border-black/[.08] dark:border-white/[.145]">
            <CardContent className="flex-1 overflow-y-auto p-6 space-y-6">
              {messages.length === 0 ? (
                <div className="h-full flex items-center justify-center">
                  <div className="text-center space-y-2">
                    <p className="text-zinc-600 dark:text-zinc-400 font-medium">Ready to evaluate</p>
                    <p className="text-sm text-zinc-500">Review the context question and click Send to test the agent.</p>
                  </div>
                </div>
              ) : (
                messages.map((m, i) => (
                  <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                    <div className={`max-w-[85%] rounded-2xl px-5 py-3.5 text-[15px] leading-relaxed ${
                      m.role === "user" 
                        ? "bg-black text-white dark:bg-white dark:text-black" 
                        : "bg-zinc-100 dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 border border-black/[.04] dark:border-white/[.04]"
                    }`}>
                      {m.content}
                      
                      {/* Expected Answer Block (Only shown if available and it's a model response) */}
                      {m.eval && m.eval.groundTruth && (
                        <div className="mt-4 pt-3 border-t border-black/[.08] dark:border-white/[.145] text-sm">
                          <div className="flex items-center gap-2 font-medium mb-1 text-emerald-600 dark:text-emerald-400">
                            <BookOpen className="w-4 h-4" />
                            Expected Answer
                          </div>
                          <p className="text-zinc-600 dark:text-zinc-400 italic">
                            &quot;{m.eval.groundTruth}&quot;
                          </p>
                        </div>
                      )}

                      {/* Optional Judge Evaluation Block */}
                      {m.eval && m.eval.score !== undefined && (
                        <div className="mt-3 pt-3 border-t border-black/[.08] dark:border-white/[.145] text-sm">
                          <div className="flex items-center gap-2 font-medium mb-1 text-purple-600 dark:text-purple-400">
                            <Gavel className="w-4 h-4" />
                            Judge Evaluation
                          </div>
                          <p className="text-zinc-600 dark:text-zinc-400">
                            <strong>Score:</strong> {m.eval.score}/1
                          </p>
                          <p className="text-zinc-600 dark:text-zinc-400 mt-1">
                            {m.eval.reasoning}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-zinc-100 dark:bg-zinc-900 border border-black/[.04] dark:border-white/[.04] rounded-2xl px-5 py-3.5 text-zinc-500 animate-pulse text-[15px]">
                    Generating answer & evaluating...
                  </div>
                </div>
              )}
            </CardContent>
            
            <div className="p-4 border-t border-black/[.08] dark:border-white/[.145] bg-zinc-50/50 dark:bg-zinc-950/50 rounded-b-lg">
              <form onSubmit={handleSubmit} className="flex gap-3" autoComplete="off">
                <Input 
                  placeholder="Type a prompt to test the model..." 
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  disabled={isLoading}
                  className="h-12 px-4 shadow-sm"
                />
                <Button 
                  type="submit" 
                  disabled={isLoading || !prompt.trim()}
                  className="h-12 px-6 rounded-full bg-black hover:bg-[#383838] text-white dark:bg-white dark:hover:bg-[#ccc] dark:text-black font-medium transition-colors"
                >
                  <Send className="w-4 h-4 mr-2" />
                  Send
                </Button>
              </form>
            </div>
          </Card>
        </div>
      </main>
    </div>
  );
}
