import json
import os
import sys
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Add parent directory to path to import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.client import MemoryClient
from shared.utils import LLM_Judge

class LongMemEvaluator:
    def __init__(self, endpoint_url: str, num_clients: int = 2):
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
            results_dir, f"longmem_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

    def save_results(self):
        with open(self.results_file, "w") as f:
            json.dump(self.results, f, indent=4)
        self.logger.info(f"Results saved to {self.results_file}")

    def run(self, dataset_path: str = None, limit: int = None):
        if dataset_path is None:
            dataset_path = os.path.join(
                os.path.dirname(__file__), "data", "longmemeval_s_cleaned.json"
            )

        self.logger.info(f"Loading dataset from {dataset_path}")
        try:
            with open(dataset_path, "r", encoding="utf-8") as f:
                dataset = json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Dataset not found at {dataset_path}")
            return

        if limit:
            dataset = dataset[:limit]
            self.logger.info(f"Limiting to first {limit} samples.")

        def evaluate_sample(sample):
            # Create a new client instance for this thread
            client = MemoryClient(self.endpoint_url)
            sample_id = sample.get("question_id", "unknown")
            # Ensure agent_id is safe for URLs
            agent_id = f"longmem_eval_{sample_id}".replace(" ", "_")
            
            try:
                # Start a session before answering
                client.start_session(agent_id)
                
                # 3. Evaluate
                question = sample.get("question", "")
                ground_truth = sample.get("answer", "")
                question_date = sample.get("question_date", "")
                question_type = sample.get("question_type", "unknown")
                full_question = f"[{question_date}] {question}"
                
                # 3. Answer using Agent API (Server-side RAG)
                try:
                    predicted_answer = client.answer(dataset_name="LongMem", agent_id=agent_id, question=full_question, threshold=0.1, limit=40)
                except Exception as e:
                    self.logger.error(f"Error asking AI for {agent_id}: {e}")
                    predicted_answer = "Error generating answer"

                # Judge
                try:
                    judge_client = MemoryClient(self.endpoint_url)
                    judge = LLM_Judge(judge_client.ask_ai, dataset_name="LongMem")
                    score_data = judge.evaluate(question, predicted_answer, ground_truth, category=question_type)
                except Exception as e:
                    self.logger.error(f"Error judging answer for {agent_id}: {e}")
                    score_data = {"score": 0, "reasoning": "Evaluation failed"}

                result = {
                    "sample_id": sample_id,
                    "question_type": question_type,
                    "question": question,
                    "prediction": predicted_answer,
                    "ground_truth": ground_truth,
                    "score": score_data.get("score", 0),
                    "reasoning": score_data.get("reasoning", ""),
                    "context_size": "Server-side"
                }
                
                return result

            except Exception as e:
                self.logger.error(f"Critical error processing sample {sample_id}: {e}")
                return {
                    "sample_id": sample_id,
                    "error": str(e),
                    "score": 0,
                    "question": sample.get("question", ""),
                    "ground_truth": sample.get("answer", ""),
                    "prediction": "Error"
                }


        self.logger.info(f"Starting isolated evaluation of {len(dataset)} samples with {self.max_workers} threads...")
        
        # Use ThreadPoolExecutor to parallelize
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(evaluate_sample, sample) for sample in dataset]
            
            for i, future in enumerate(futures):
                try:
                    res = future.result()
                    self.results.append(res)
                    # Save incrementally but avoid duplicate save on the last item
                    if (i + 1) % 5 == 0 and (i + 1) < len(dataset):
                        self.logger.info(f"Processed {i + 1}/{len(dataset)} samples")
                        # Incremental save
                        self.save_results()
                except Exception as e:
                    self.logger.error(f"Future failed: {e}")
        
        self.save_results()

if __name__ == "__main__":
    # Default execution
    evaluator = LongMemEvaluator("http://127.0.0.1:8000")
    evaluator.run(limit=None)
