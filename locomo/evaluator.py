import json
import os
from datetime import datetime
from shared.client import MemoryClient
from shared.utils import LLM_Judge
from concurrent.futures import ThreadPoolExecutor

class LoCoMoEvaluator:
    def __init__(self, endpoint_url: str, num_clients: int = 10):
        self.endpoint_url = endpoint_url
        self.max_workers = num_clients
        # Create a pool of judges sharing clients
        self.judge_clients = [MemoryClient(endpoint_url) for _ in range(num_clients)]
        self.judges = [LLM_Judge(client.ask_ai) for client in self.judge_clients]
        self.results = []

    def run(self, dataset_path: str = None):
        if dataset_path is None:
            dataset_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "data", "locomo10.json"
            )

        with open(dataset_path, "r") as f:
            dataset = json.load(f)

        def evaluate_sample(sample, judge):
            client = MemoryClient(self.endpoint_url)
            # judge is passed in
            sample_id = sample["sample_id"]
            print(f"\n--- Evaluating Sample: {sample_id} ---")
            # 1. SETUP: Unique agent name
            agent_id = f"Agent_{sample_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            client.create_agent(
                agent_id=agent_id, pattern="support", description="LoCoMo eval agent"
            )
            # 2. INGESTION
            conv_data = sample["conversation"]
            session_keys = sorted(
                [
                    k
                    for k in conv_data.keys()
                    if k.startswith("session_") and not k.endswith("date_time")
                ],
                key=lambda x: int(x.split("_")[1]),
            )
            for s_key in session_keys:
                timestamp = conv_data.get(f"{s_key}_date_time", "Unknown")
                client.start_session(agent_id)
                for turn in conv_data[s_key]:
                    content = f"[{timestamp}] {turn['speaker']}: {turn['text']}"
                    client.store_memory(
                        agent_id=agent_id,
                        content=content,
                        metadata={
                            "dia_id": turn.get("dia_id", ""),
                            "session": s_key,
                            "timestamp": timestamp,
                        },
                    )
                client.end_session(agent_id=agent_id)
            # 3. EVALUATION (Filtering Category 5)
            print(f"\n--- Testing Sample: {sample_id} ---")
            client.start_session(agent_id)

            def evaluate_qa(qa):
                try:
                    category = int(qa["category"])
                    if category == 5:
                        return None
                    question = qa["question"]
                    ground_truth = qa["answer"]
                    predicted_answer = client.answer(agent_id, question)
                    score_data = judge.evaluate(
                        question, predicted_answer, ground_truth
                    )
                    return {
                        "sample_id": sample_id,
                        "category": category,
                        "question": question,
                        "prediction": predicted_answer,
                        "ground_truth": ground_truth,
                        "score": score_data.get("score", 0),
                    }
                except Exception as e:
                    print(f"Error processing QA for sample {sample_id}: {e}")
                    return None

            for qa in sample["qa"]:
                result = evaluate_qa(qa)
                if result:
                    self.results.append(result)

            client.end_session(agent_id=agent_id)
            # 4. CLEANUP
            client.delete_agent(agent_id)

        # Use ThreadPoolExecutor to respect max_workers (num_clients)
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for idx, sample in enumerate(dataset):
                judge = self.judges[idx % len(self.judges)]
                futures.append(executor.submit(evaluate_sample, sample, judge))
            
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    print(f"Error evaluating sample: {e}")

        self.save_results()

    def save_results(self):
        results_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "results"
        )
        os.makedirs(results_dir, exist_ok=True)
        filename = os.path.join(
            results_dir, f"locomo_results_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        )
        with open(filename, "w") as f:
            json.dump(self.results, f, indent=4)
        print(f"\nResults saved to {filename}")
