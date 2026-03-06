# MUMLA Benchmarking Progress Report

## Introduction
This document outlines the benchmarking progression for the MUMLA project using the `locomo` and `longmem` datasets. The primary objective was to establish a comprehensive baseline for retrieval accuracy and answer quality by using a standard RAG implementation.

---

## Establishing the Baseline
Our starting point was a standard "Naive RAG" implementation designed to establish a performance floor.
- **Methodology**: Simple semantic search against ingested memory chunks.
- **Parameters**: 
  - **Retrieval Limit**: Top 10 chunks.
  - **Similarity Threshold**: 0.15 ITS score.
  - **Model**: Claude Sonnet 4.

#### LongMemEval
**Overall Accuracy**: 56.6%

#### LoCoMo
**Overall Accuracy**: 76.2%

At its absolute baseline it performs fairly well on the LoCoMo dataset, already surpassing some agentic AI systems but doing much more poorly on the LongMemEval dataset.

---

## Retrieval & Parameter Optimization
We observed that a chunk retrieval limit of 10 chunks was a major bottleneck. There are many complex user queries which reference several events scattered across various sessions which would be nearly impossible for semantic search to find all of them.

### Updates
- Increased retrieval limit from **10** to **40** chunks.
- Lowered similarity threshold from **0.15** to **0.10**.

#### LongMemEval
**Overall Accuracy**: 77.0%

#### LoCoMo
**Overall Accuracy**: 82.8%

As we can see, with a sufficiently strong LLM, it's better to retrieve "noisy" chunks and let the LLM filter them than to miss relevant chunks entirely, so we see significant accuracy increases across the board.

---

## Prompt Engineering
The next thing to focus on is the prompts specified for both the LLM judge and LLM answerer.

A significant amount of attention has to be dedicated to this due to the nature of using an LLM as a judge. It introduces the possibility of semantically correct answers which can be rejected if they don't match the ground truth's phrasing.

This applies to the LLM answerer too as there are scenarios where even if it knows the right answer, due to lack of context or potential ambiguities in the question, the LLM may not present it with much confidence or outright say it doesn't know causing the answer to be rejected.

We adopted prompts from the [*Hindsight*](https://github.com/vectorize-io/hindsight) repository to establish a more equal benchmark with other agentic systems and modified it to account for our specific memory architecture.

#### LongMemEval
**Overall Accuracy**: 79.2%

#### LoCoMo
**Overall Accuracy**: 82.9%

We can see an accuracy increase in the LongMem dataset but not the LoCoMo one likely due to the difference in question schema. The LoCoMo dataset uses much more straightforward questioning which is easy to parse while the LongMem dataset asks questions which may require more complex reasoning and small ambiguities in the answering schema.

---

## 5. Continued Retrieval & Parameter Optimization
Observing the individual questions and how the LLM fails to answer them, we notice that incorrect answers aren't usually a result of noisy chunks being provided, but rather the semantic search didn't manage to search all of the correct chunks making it impossible for the LLM to deduce the answer.

### Updates
- Increased retrieval limit from **40** to **100** chunks.
- Lowered similarity threshold from **0.10** to **0.05**.

#### LongMemEval
**Overall Accuracy**: 85.0%

#### LoCoMo
**Overall Accuracy**: 86.3%

Looking at the answering improvements, we can see that semantic search engines can be fooled by chunks that contain multiple topics. A chunk might be 90% irrelevant but contain one critical sentence. Considering the existence of multi-session questions where multiple critical sentences throughout the dataset are required, utilizing a larger chunk retrieval shows massive benefit.
---

## Architectural Experiments
We briefly explored structural changes to the memory system itself to improve performance without significantly altering the overall RAG architecture of Moorcheh. The issue of critical sentences in otherwise irrelevant chunks is still very prevalent and retrieving more chunks only serves to mitigate the problem.

We tried the following:
- **Session Summaries**: Summarizing an entire conversation session into a single block.
- **Global Summaries**: Aggregating insights across all sessions.

The hope is that while the chunk relevancy may gloss over these critical sentences a wholistic session summary or global summary may see these as more important to mention.

While these provided marginal improvements, they introduced a significant increase in token consumption and cost. We decided that the marginal improvements were not worth it and that utilizing a graph-based memory architecture may be the route to further memory retrieval accuracy.

---

## Gemini 3 Transition
For the final comprehensive evaluation, we switched the underlying inference model from **Claude Sonnet 4** to **Gemini 3**. Along with the issue of finding a needle in a haystack, there were also many questions where the model was simply not smart enough to interpret all of the information correctly and come up with the correct answer. This is also necessary to establish an equal comparison between other agentic systems who use gemini 3 for their evaluation testing.

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
With using just a RAG-based schema as a memory layer retrieving the first 100 relevant chunks, we already see major proficiency with memory tasks that were previously thought to require complex graph databases or parallel search retrieval. Achieving **89.8%** on LongMemEval and **87.1%** on LoCoMo is a testament to the power of Moorchehs high quality semantic search and retrieval.
