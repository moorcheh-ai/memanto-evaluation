import json
import os
import sys
import logging
from concurrent.futures import ThreadPoolExecutor

# Add parent directory to path to import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.client import MemoryClient

class LoCoMoIngestor:
    def __init__(self, endpoint_url: str, num_clients: int = 5):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self.logger = logging.getLogger(__name__)
        self.endpoint_url = endpoint_url
        self.max_workers = num_clients

    def run(self, dataset_path: str = None, limit: int = None):
        if dataset_path is None:
            dataset_path = os.path.join(
                os.path.dirname(__file__), "data", "locomo10.json"
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

        def process_sample(sample):
            client = MemoryClient(self.endpoint_url)
            sample_id = sample.get("sample_id", "unknown")
            # Use deterministic agent ID
            agent_id = f"locomo_eval_{sample_id}"
            
            self.logger.info(f"Ingesting Sample: {sample_id} into Agent: {agent_id}")

            try:
                # 1. SETUP: Create agent
                try:
                    client.create_agent(
                        agent_id=agent_id, pattern="support", description=f"LoCoMo eval agent for sample {sample_id}"
                    )
                except Exception:
                    # Agent might already exist
                    pass

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
                
                memories_to_store = []
                count = 0
                for s_key in session_keys:
                    timestamp = conv_data.get(f"{s_key}_date_time", "Unknown")
                    
                    try:
                        for turn in conv_data[s_key]:
                            text = turn['text']
                            if "blip_caption" in turn and turn["blip_caption"]:
                                caption = turn["blip_caption"]
                                query = turn.get("query", "")
                                if query:
                                    text += f" [Image: {caption} (Query: {query})]"
                                else:
                                    text += f" [Image: {caption}]"
                            
                            content = f"[{timestamp}] {turn['speaker']}: {text}"
                            dia_id = turn.get("dia_id", "")
                            
                            memories_to_store.append({
                                "content": content,
                                "title": f"{s_key} - {timestamp}",
                                "tags": [str(dia_id), str(s_key)],
                                "type": "preference" # Matching the type used in original store_memory
                            })
                            count += 1
                    except Exception as e:
                        self.logger.error(f"Error preparing memories for session {s_key} for agent {agent_id}: {e}")

                if memories_to_store:
                    try:
                        client.start_session(agent_id)
                    except Exception as e:
                        self.logger.warning(f"Failed to start session for {agent_id}: {e}")

                    # Batch store
                    chunk_size = 50 
                    for i in range(0, len(memories_to_store), chunk_size):
                        chunk = memories_to_store[i:i + chunk_size]
                        try:
                            client.batch_store_memories(agent_id, chunk)
                        except Exception as e:
                            self.logger.error(f"Error storing memories for {agent_id}: {e}")

                    try:
                        client.end_session(agent_id=agent_id)
                    except Exception:
                        pass

                self.logger.info(f"Ingested {count} memories for agent {agent_id}")

            except Exception as e:
                self.logger.error(f"Critical error processing sample {sample_id}: {e}")

        self.logger.info(f"Starting ingestion of {len(dataset)} samples with {self.max_workers} threads...")
        
        # Use ThreadPoolExecutor to parallelize
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            executor.map(process_sample, dataset)
        
        self.logger.info("Ingestion complete, ready for evaluation.")

if __name__ == "__main__":
    # Default execution
    ingestor = LoCoMoIngestor("http://127.0.0.1:8000")
    ingestor.run()
