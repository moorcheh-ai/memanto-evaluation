# Mumla-Evaluation

## Benchmarks and Results

This repository contains benchmarking tools for evaluating the Mumla agentic memory system.

### Baseline Results

Official benchmark scores are tracked in `results/baselines/`. The results provide a detailed breakdown of accuracy across multiple categories.

#### LongMemEval

| Method | Single-session User | Single-session Assistant | Single-session Preference | Knowledge Update | Temporal Reasoning | Multi-session | Overall |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Mumla | 88.6% | 100.0% | 93.3% | 91.0% | 68.4% | 66.2% | 79.2% |

#### LoCoMo

| Method | Single-Hop | Multi-Hop | Open Domain | Temporal | Overall |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Mumla | 68.4% | 69.8% | 86.7% | 79.8% | 80.8% |

### Running Benchmarks

Ensure the `MOORCHEH_API_KEY` environment variable is set before starting.

To run a benchmark, execute the ingestion script followed by the evaluator. Replace `<benchmark>` with either `locomo` or `longmem`:

1.  **Ingest Data** (populates the memory store):
    ```bash
    python <benchmark>/ingestor.py
    ```

2.  **Run Evaluation** (generates results):
    ```bash
    python <benchmark>/evaluator.py
    ```