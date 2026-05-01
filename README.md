# Memanto Benchmarks & Evaluation

This repository contains the official evaluation suite, benchmark results, and an interactive visualization tool for **Memanto**, the Information-Theoretic agent memory system.

Our goal with this repository is transparency and reproducibility. Rather than just publishing static accuracy tables, we provide the complete pipelines and an interactive web interface so you can explore the data, test the system yourself, and verify the results.

This repository includes:
* **Industry Benchmarks:** Official LoCoMo and LongMemEval results comparing Memanto to other leading memory frameworks.
* **Evaluation Pipelines:** Python scripts to locally reproduce the ingestion and LLM-as-a-Judge evaluation processes.
* **Interactive Visualizer:** A local web application to deeply explore the datasets, construct your own queries, and run real-time evaluations.

---

## Memory Performance & Accuracy

Memanto achieves state-of-the-art performance on both LongMemEval and LoCoMo benchmarks by utilizing Moorcheh's Information-Theoretic Scoring (ITS) engine. It outperforms the vast majority of hybrid knowledge-graph architectures without requiring an LLM during the ingestion phase.

### LongMemEval Results

| Method | Single-session User | Single-session Assistant | Single-session Preference | Knowledge Update | Temporal Reasoning | Multi-session | Overall |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Hindsight (Gemini-3) | 97.1% | 96.4% | 80.0% | 94.9% | 91.0% | 87.2% | 91.4% |
| **Memanto (Gemini-3)** | **95.7%** | **100.0%** | **93.3%** | **93.6%** | **88.0%** | **81.2%** | **89.8%** |
| Hindsight (OSS-120B) | 100.0% | 98.2% | 86.7% | 92.3% | 85.7% | 81.2% | 89.0% |
| Supermemory (Gemini-3) | 98.6% | 98.2% | 70.0% | 89.7% | 82.0% | 76.7% | 85.2% |
| Supermemory (GPT-5) | 97.1% | 100.0% | 76.7% | 87.2% | 81.2% | 75.2% | 84.6% |
| Hindsight (OSS-20B) | 95.7% | 94.6% | 66.7% | 84.6% | 79.7% | 79.7% | 83.6% |
| Supermemory (GPT-4o) | 97.1% | 96.4% | 70.0% | 88.5% | 76.7% | 71.4% | 81.6% |
| Zep (GPT-4o) | 92.9% | 80.4% | 56.7% | 83.3% | 62.4% | 57.9% | 71.2% |
| Full-context (GPT-4o) | 81.4% | 94.6% | 20.0% | 78.2% | 45.1% | 44.3% | 60.2% |
| Full-context (OSS-20B) | 38.6% | 80.4% | 20.0% | 60.3% | 31.6% | 21.1% | 39.0% |

### LoCoMo Results

| Method | Single-Hop | Multi-Hop | Open Domain | Temporal | Overall |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Hindsight (Gemini-3) | 86.17% | 70.83% | 95.12% | 83.80% | 89.61% |
| **Memanto (Gemini-3)** | **78.72%** | **70.83%** | **92.39%** | **85.36%** | **87.08%** |
| Hindsight (OSS-120B) | 76.79% | 62.50% | 93.68% | 79.44% | 85.67% |
| Hindsight (OSS-20B) | 74.11% | 64.58% | 90.96% | 76.32% | 83.18% |
| Memobase (v0.0.37) | 70.92% | 46.88% | 77.17% | 85.05% | 75.78% |
| Zep | 74.11% | 66.04% | 67.71% | 79.79% | 75.14% |
| Mem0-Graph | 65.71% | 47.19% | 75.71% | 58.13% | 68.44% |
| Mem0 | 67.13% | 51.15% | 72.93% | 55.51% | 66.88% |
| LangMem | 62.23% | 47.92% | 71.12% | 23.43% | 58.10% |
| OpenAI | 63.79% | 42.92% | 62.29% | 21.71% | 52.90% |

### Note on Benchmark Validity

While Memanto achieves state-of-the-art results on both LongMemEval and LoCoMo, we share the broader industry sentiment that the current generation of agentic memory benchmarks is deeply flawed and should not be used as the sole indicator of a memory system's quality or production readiness.

As detailed in the original Memanto paper (and mirrored by [other researchers](https://blog.getzep.com/lies-damn-lies-statistics-is-mem0-really-sota-in-agent-memory/)), these datasets suffer from:
1. **Missing Ground Truth:** Several categories have missing answers, incorrect speaker attributions, and subjective edge cases.
2. **Ambiguous Questions:** Questions often lack the specificity needed for a single correct answer, causing LLM judges to unfairly penalize semantically correct responses.
3. **Insufficient Challenge (Saturated Baselines):** The conversations in LoCoMo, for example, are too short (16k-26k tokens) to genuinely stress-test retrieval. They easily fit within the standard context windows of modern foundational models without needing a memory system at all. Because of this, leading architectures are quickly reaching the practical accuracy ceilings of both LoCoMo and LongMemEval, creating an illusion of parity that breaks down at true long-horizon scales. 
4. **Poor Context Simulation:** LongMemEval struggles to accurately simulate organic, long-horizon temporal drift, often relying on contrived scenarios rather than authentic state changes.

---

## Quick Start: Interactive Visualizer

> **🚧 Notice:** The interactive visualizer is currently in development and is not live yet.

We provide a local web application that allows you to interactively explore and evaluate the datasets yourself. 

Instead of just trusting our static scores, the visualizer lets you:
* **Dive into the Data:** Browse individual questions from the LongMemEval and LoCoMo datasets.
* **Inspect the Reasoning:** See exactly which memories Memanto retrieved and read the LLM judge's reasoning for why an answer passed or failed.
* **Bring Your Own Keys:** Plug in your own LLM provider keys (e.g., OpenAI, Google) to evaluate different inference models. *(Note: Do NOT supply a `MOORCHEH_API_KEY` to the visualizer, as it needs to run against the pre-indexed public dataset.)*
* **Choose Your Models:** Select which models you want to use for inference and which to use for judging.
* **Construct Custom Scenarios:** Write your own complex, multi-hop questions against the dataset history to see how the architecture responds in real-time.

---

## Reproducing the Benchmarks (CLI)

If you prefer to run the full end-to-end evaluation pipeline via the command line to reproduce our static scores, you can use the included Python scripts.

Ensure you have the following environment variables set before starting:
- `MOORCHEH_API_KEY`
- `GEMINI_API_KEY` (or the respective key for your chosen LLM evaluator)

To run a benchmark, execute the ingestion script followed by the evaluator. Replace `<benchmark>` with either `locomo` or `longmem`:

1.  **Ingest Data** (populates the memory store):
    ```bash
    python <benchmark>/ingestor.py
    ```

2.  **Run Evaluation** (generates results):
    ```bash
    python <benchmark>/evaluator.py
    ```

3.  **Generate Report** (compiles the final evaluation report):
    ```bash
    python <benchmark>/generate_report.py
    ```

*(Note: Running the full LongMemEval benchmark pipeline requires a **Moorcheh Pro** subscription due to the dataset size).*
