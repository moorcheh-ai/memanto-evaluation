# Mumla-Evaluation

## Benchmarks and Results

This repository contains benchmarking tools for evaluating the Mumla agentic memory system.

### Baseline Results

Official benchmark scores are tracked in `results/baselines/`. The results provide a detailed breakdown of accuracy across multiple categories.

#### LongMemEval

| Method | Single-session User | Single-session Assistant | Single-session Preference | Knowledge Update | Temporal Reasoning | Multi-session | Overall |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Mumla (Gemini-3)** | **95.7%** | **100.0%** | **93.3%** | **93.6%** | **88.0%** | **81.2%** | **89.8%** |
| Supermemory (Gemini-3) | 98.6% | 98.2% | 70.0% | 89.7% | 82.0% | 76.7% | 85.2% |
| Supermemory (GPT-5) | 97.1% | 100.0% | 76.7% | 87.2% | 81.2% | 75.2% | 84.6% |
| Supermemory (GPT-4o) | 97.1% | 96.4% | 70.0% | 88.5% | 76.7% | 71.4% | 81.6% |
| Zep (GPT-4o) | 92.9% | 80.4% | 56.7% | 83.3% | 62.4% | 57.9% | 71.2% |
| Full-context (GPT-4o) | 81.4% | 94.6% | 20.0% | 78.2% | 45.1% | 44.3% | 60.2% |
| Full-context (OSS-20B) | 38.6% | 80.4% | 20.0% | 60.3% | 31.6% | 21.1% | 39.0% |

#### LoCoMo

| Method | Single-Hop | Multi-Hop | Open Domain | Temporal | Overall |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Mumla (Gemini-3)** | **78.72%** | **70.83%** | **92.39%** | **85.36%** | **87.08%** |
| Memobase (v0.0.37) | 70.92% | 46.88% | 77.17% | 85.05% | 75.78% |
| Zep | 74.11% | 66.04% | 67.71% | 79.79% | 75.14% |
| Mem0-Graph | 65.71% | 47.19% | 75.71% | 58.13% | 68.44% |
| Mem0 | 67.13% | 51.15% | 72.93% | 55.51% | 66.88% |
| LangMem | 62.23% | 47.92% | 71.12% | 23.43% | 58.10% |
| OpenAI | 63.79% | 42.92% | 62.29% | 21.71% | 52.90% |

### Running Benchmarks

Ensure you have the following environment variables set before starting:
- `MOORCHEH_API_KEY`
- `GEMINI_API_KEY` (required for running the LLM evaluator)

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

(Note: Running the LongMem benchmark requires a **Moorcheh Pro** subscription)
