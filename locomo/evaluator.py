import json
import os
import sys
import logging
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Add parent directory to path to import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.client import MemoryClient
from shared.utils import LLM_Judge

class LoCoMoEvaluator:
    def __init__(self, endpoint_url: str, num_clients: int = 10):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self.logger = logging.getLogger(__name__)
        self.endpoint_url = endpoint_url
        self.max_workers = num_clients
        self.results = []
        
        # Initialize results file path once
        results_dir = os.path.join(
            os.path.dirname(__file__), "results"
        )
        os.makedirs(results_dir, exist_ok=True)
        self.results_file = os.path.join(
            results_dir, f"locomo_results_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        )
        self.lock = threading.Lock()

    def run(self, dataset_path: str = None, limit: int = None):
        if dataset_path is None:
            dataset_path = os.path.join(
                os.path.dirname(__file__), "data", "locomo10.json"
            )

        with open(dataset_path, "r", encoding="utf-8") as f:
            dataset = json.load(f)

        if limit:
            dataset = dataset[:limit]
            self.logger.info(f"Limiting to first {limit} samples.")

        def evaluate_sample(sample):
            client = MemoryClient(self.endpoint_url)
            judge_client = MemoryClient(self.endpoint_url)
            judge = LLM_Judge(judge_client.ask_ai, dataset_name="LoCoMo")
            sample_id = sample["sample_id"]
            
            # 1. SETUP: Deterministic agent name (must match Ingestor)
            agent_id = f"locomo_eval_{sample_id}"
            self.logger.info(f"Evaluating Sample: {sample_id} with Agent: {agent_id}")

            # 3. EVALUATION (Filtering Category 5)
            try:
                client.start_session(agent_id)
            except Exception as e:
                self.logger.warning(f"Could not start session for agent {agent_id}: {e}")

            def evaluate_qa(qa):
                try:
                    category = int(qa["category"])
                    if category == 5:
                        return None
                    question = qa["question"]
                    ground_truth = qa["answer"]
                    predicted_answer = client.answer_rag(dataset_name="LoCoMo", agent_id=agent_id, question=question, threshold=0.05, limit=100)
                    score_data = judge.evaluate(
                        question, predicted_answer, ground_truth, category
                    )
                    return {
                        "sample_id": sample_id,
                        "category": category,
                        "question": question,
                        "prediction": predicted_answer,
                        "ground_truth": ground_truth,
                        "score": score_data.get("score", 0),
                        "reasoning": score_data.get("reasoning", ""),
                    }
                except Exception as e:
                    self.logger.error(f"Error processing QA for sample {sample_id}: {e}")
                    return None

            for qa in sample["qa"]:
                result = evaluate_qa(qa)
                if result:
                    with self.lock:
                        self.results.append(result)
                        if len(self.results) % 10 == 0:
                            self.save_results()

            # 4. CLEANUP
            client.end_session(agent_id=agent_id)

        # Use ThreadPoolExecutor to parallelize
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(evaluate_sample, sample) for sample in dataset]
            
            for i, future in enumerate(futures):
                try:
                    future.result()
                    self.logger.info(f"Finished processing sample {i + 1}/{len(dataset)}")
                except Exception as e:
                    self.logger.error(f"Future failed: {e}")
        
        with self.lock:
             self.save_results()

    def save_results(self):
        with open(self.results_file, "w") as f:
            json.dump(self.results, f, indent=4)
        self.logger.info(f"Results saved to {self.results_file}")

if __name__ == "__main__":
    evaluator = LoCoMoEvaluator("http://127.0.0.1:8000")
    evaluator.run()
