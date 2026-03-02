import json
import os
import sys
import logging
from concurrent.futures import ThreadPoolExecutor
import time

# Add parent directory to path to import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.client import MemoryClient

class LongMemIngestor:
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

        def process_sample(sample):
            # Create a new client instance for this thread
            client = MemoryClient(self.endpoint_url)
            sample_id = sample.get("question_id", "unknown")
            # Ensure agent_id is safe for URLs
            agent_id = f"longmem_eval_{sample_id}".replace(" ", "_")
            
            try:
                # 1. Create Agent
                # Use a unique agent for this sample
                try:
                    client.create_agent(
                        agent_id=agent_id, pattern="support", description=f"Agent for sample {sample_id}"
                    )
                except Exception:
                    # Agent might already exist, just proceed
                    pass

                # 2. Ingest Data
                memories_to_store = []
                
                sessions = sample.get("haystack_sessions", [])
                dates = sample.get("haystack_dates", [])
                session_ids = sample.get("haystack_session_ids", [])
                
                for i, session_turns in enumerate(sessions):
                    timestamp = dates[i] if i < len(dates) else "Unknown Date"
                    session_id_val = session_ids[i] if i < len(session_ids) else f"session_{i}"
                    
                    for turn in session_turns:
                        speaker = turn.get("role", "user")
                        text = turn.get("content", "")
                        content = f"[{timestamp}] {speaker}: {text}"
                        
                        # Re-enable truncation, but with a larger limit (e.g., 9000 chars to be safe)
                        if len(content) > 9000:
                            content = content[:9000] + "... (truncated)"
                        
                        title = f"{sample_id}_{session_id_val}"
                        if len(title) > 100:
                            title = title[:100]

                        # Ensure tags are strings
                        tags_list = [str(t) for t in [sample_id, session_id_val, "longmem_eval"]]

                        memories_to_store.append({
                            "content": content,
                            "title": title,
                            "tags": tags_list,
                            "type": "fact"
                        })

                if memories_to_store:
                     # Start session before storing?
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
                    
                    self.logger.info(f"Ingested {len(memories_to_store)} memories for agent {agent_id}")
                
            except Exception as e:
                self.logger.error(f"Critical error processing sample {sample_id}: {e}")

        self.logger.info(f"Starting ingestion of {len(dataset)} samples with {self.max_workers} threads...")
        
        # Use ThreadPoolExecutor to parallelize
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            executor.map(process_sample, dataset)
        
        self.logger.info("Ingestion complete.")

if __name__ == "__main__":
    # Default execution
    ingestor = LongMemIngestor("http://127.0.0.1:8000")
    ingestor.run()
