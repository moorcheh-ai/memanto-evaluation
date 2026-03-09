# MUMLA Benchmarking Progress Report

## Introduction
This document outlines the benchmarking progression for the MUMLA project using the `locomo` and `longmem` datasets. The primary objective was to establish a comprehensive baseline for retrieval accuracy and answer quality by using a standard RAG implementation.

---

## Establishing the Baseline
We started with a standard "Naive RAG" implementation to establish a performance floor.
- **Methodology**: Simple semantic search against ingested memory chunks.
- **Parameters**: 
  - **Retrieval Limit**: Top 10 chunks.
  - **Similarity Threshold**: 0.15 ITS score.
  - **Model**: Claude Sonnet 4.

#### LongMemEval
**Overall Accuracy**: 56.6%

#### LoCoMo
**Overall Accuracy**: 76.2%

Even at this barebones baseline, we were already seeing results comparable to full-context baselines (LoCoMo 72.9%, LongMemEval 60.2%). It performed fairly well on the LoCoMo dataset, already surpassing some agentic AI systems, though it struggled more with the complex reasoning required by LongMemEval.

---

## Retrieval & Parameter Optimization
We quickly realized that a retrieval limit of 10 chunks was a major bottleneck. Many complex user queries reference several events scattered across various sessions, making it nearly impossible for a semantic search to find all relevant pieces of information within such a tight constraint.

### Updates
- Increased retrieval limit from **10** to **40** chunks.
- Lowered similarity threshold from **0.15** to **0.10**.

#### LongMemEval
**Overall Accuracy**: 77.0%

#### LoCoMo
**Overall Accuracy**: 82.8%

We immediately see significant accuracy increases across the board. The takeaway? With a sufficiently capable LLM, it's better to retrieve "noisy" chunks and let the model filter them than to miss relevant chunks entirely.

---

## Prompt Engineering
Next, we turned our attention to the prompts used for both the LLM judge and the LLM answerer.

When using an LLM as a judge, significant care must be taken. A poorly tuned judge might reject semantically correct answers simply because they don't exactly match the ground truth's phrasing.

Similarly, an LLM answerer might know the right answer but, due to perceived ambiguities or a lack of explicit context, fail to present it confidently or outright refuse to answer.

To establish a fairer benchmark against other agentic systems, we adopted prompts from the [*Hindsight*](https://github.com/vectorize-io/hindsight) repository, modifying them to account for our specific memory architecture.

#### LongMemEval
**Overall Accuracy**: 79.2%

#### LoCoMo
**Overall Accuracy**: 82.9%

We observed an accuracy increase in the LongMemEval dataset, but not LoCoMo. This is likely due to the difference in question schemas: LoCoMo features straightforward, easy-to-parse questions, while LongMemEval involves queries that require complex reasoning and nuanced answering schemas.

The accuracy increase isn't significant so in the near future with stronger LLM's or a more robust memory architecture, the attention put into prompting can be reduced, allowing MUMLA to perform the complex reasoning tasks without prompting guidance.

---

## Pushing Retrieval Further
Analyzing the individual failures revealed that incorrect answers weren't usually caused by noisy chunks confusing the LLM. Instead, the semantic search was still missing critical chunks needed to deduce the answer.

### Updates
- Increased retrieval limit from **40** to **100** chunks.
- Lowered similarity threshold from **0.10** to **0.05**.

#### LongMemEval
**Overall Accuracy**: 85.0%

#### LoCoMo
**Overall Accuracy**: 86.3%

Again we continue to see major improvements across the board by increasing retrieval size. Semantic search engines can sometimes be fooled by chunks containing multiple topics, a chunk might be 90% irrelevant but contain one critical sentence. Because multi-session questions require synthesizing critical sentences scattered throughout the dataset, utilizing a much larger chunk retrieval pool proved massively beneficial.

---

## Architectural Experiments
We briefly explored structural changes to the memory system itself to improve performance without significantly altering MUMLA's core RAG architecture. Despite the improvements, retrieving more chunks only serves to mitigate the "critical sentence in an irrelevant chunk" problem; it doesn't solve it.

We experimented with:
- **Session Summaries**: Summarizing an entire conversation session into a single block.
- **Global Summaries**: Aggregating insights across all sessions.

The hope was that while chunk-level retrieval might skim over critical sentences, holistic session or global summaries would highlight them.

These approaches did provide some marginal improvements, however it started to introduce a significant increase in token consumption and cost. We concluded that the trade-off wasn't worth it, and that pivoting to a graph-based memory architecture might be the more viable route for future retrieval accuracy gains.

---

## Transitioning to Gemini 3
For our final comprehensive evaluation, we switched the underlying inference model from **Claude Sonnet 4** to **Gemini 3**. Beyond the "needle in a haystack" retrieval problem, there were instances where the previous model struggled to correctly interpret the provided information. This transition was also necessary to establish an apples-to-apples comparison with other agentic systems that use Gemini 3 for their evaluation testing.

#### LongMemEval
| Single-session User | Single-session Assistant | Single-session Preference | Knowledge Update | Temporal Reasoning | Multi-session | Overall |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **95.7%** | **100.0%** | **93.3%** | **93.6%** | **88.0%** | **81.2%** | **89.8%** |

#### LoCoMo
| Single-Hop | Multi-Hop | Open Domain | Temporal | Overall |
| :--- | :--- | :--- | :--- | :--- |
| **78.7%** | **70.8%** | **92.4%** | **85.4%** | **87.1%** |

---

## Conclusion
Using a standard RAG-based schema as a memory layer and retrieving the top 100 relevant chunks, we've demonstrated major proficiency in memory tasks previously thought to require complex graph databases or parallel search retrieval architectures.

Achieving **89.8%** on LongMemEval and **87.1%** on LoCoMo is a testament to the power of Moorcheh's high-quality semantic search and retrieval. Simple, highly-optimized RAG is far more capable than it gets credit for.
