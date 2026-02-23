
import requests
import os

class MemoryClient:
	def __init__(self, endpoint_url: str):
		self.moorcheh_url = "https://api.moorcheh.ai"
		self.endpoint_url = endpoint_url.rstrip('/')
		self.api_key = os.environ.get("MOORCHEH_API_KEY")
		self.session_token = None

	def _headers(self):
		headers = {
			"Authorization": f"Bearer {self.api_key}"
		}
		if self.session_token:
			headers["X-Session-Token"] = self.session_token
		return headers

	# Agent Management
	def create_agent(self, agent_id: str, pattern: str = "support", description: str = "Agent for LoCoMo eval"):
		payload = {
			"agent_id": agent_id,
			"pattern": pattern,
			"description": description
		}
		resp = requests.post(f"{self.endpoint_url}/api/v2/agents", json=payload, headers=self._headers())
		resp.raise_for_status()
		return agent_id

	def delete_agent(self, agent_id: str):
		resp = requests.delete(f"{self.endpoint_url}/api/v2/agents/{agent_id}", headers=self._headers())
		resp.raise_for_status()
		return True

	# Session Management
	def start_session(self, agent_id: str):
		resp = requests.post(f"{self.endpoint_url}/api/v2/agents/{agent_id}/activate", headers=self._headers())
		resp.raise_for_status()
		self.session_token = resp.json().get("session_token", None)
		return self.session_token

	def end_session(self, agent_id: str = None, session_token: str = None):
		# agent_id is required for the correct endpoint
		token = session_token or self.session_token
		if not token or not agent_id:
			return False
		resp = requests.post(f"{self.endpoint_url}/api/v2/agents/{agent_id}/deactivate", headers={**self._headers(), "X-Session-Token": token})
		resp.raise_for_status()
		self.session_token = None
		return True

	# Memory Operations
	def store_memory(self, agent_id: str, content: str, metadata: dict = None):
		params = {
			"memory_type": "preference",
			"title": metadata["session"] if metadata and "session" in metadata else "Memory",
			"content": content,
			"confidence": 0.8,
			"tags": f"{metadata['dia_id']},{metadata['session']}" if metadata else "",
			"source": "agent",
			"provenance": "explicit_statement"
		}
		resp = requests.post(f"{self.endpoint_url}/api/v2/agents/{agent_id}/remember", headers=self._headers(), params=params)
		resp.raise_for_status()
		return resp.json()

	def search_memory(self, agent_id: str, query: str):
		params = {"query": query, "limit": 10}
		resp = requests.get(f"{self.endpoint_url}/api/v2/agents/{agent_id}/recall", params=params, headers=self._headers())
		resp.raise_for_status()
		return resp.json().get("memories", [])

	def answer(self, agent_id: str, question: str):
		ANSWER_PROMPT = (
			"You are an intelligent memory assistant tasked with retrieving accurate information from conversation memories.\n"
			"\n# CONTEXT:\n"
			"You have access to memories from two speakers in a conversation. These memories contain "
			"timestamped information that may be relevant to answering the question.\n"
			"\n# INSTRUCTIONS:\n"
			"1. Carefully analyze all provided memories from both speakers\n"
			"2. Pay special attention to the timestamps to determine the answer\n"
			"3. If the question asks about a specific event or fact, look for direct evidence in the memories\n"
			"4. If the memories contain contradictory information, prioritize the most recent memory\n"
			"5. If there is a question about time references (like 'last year', 'two months ago', etc.), "
			"calculate the actual date based on the memory timestamp. For example, if a memory from "
			"4 May 2022 mentions 'went to India last year,' then the trip occurred in 2021.\n"
			"6. Always convert relative time references to specific dates, months, or years. For example, "
			"convert 'last year' to '2022' or 'two months ago' to 'March 2023' based on the memory "
			"timestamp. Ignore the reference while answering the question.\n"
			"7. Focus only on the content of the memories from both speakers. Do not confuse character "
			"names mentioned in memories with the actual users who created those memories.\n"
			"8. The answer should be less than 5-6 words.\n"
			"\n# APPROACH (Think step by step):\n"
			"1. First, examine all memories that contain information related to the question\n"
			"2. Examine the timestamps and content of these memories carefully\n"
			"3. Look for explicit mentions of dates, times, locations, or events that answer the question\n"
			"4. If the answer requires calculation (e.g., converting relative time references), show your work\n"
			"5. Formulate a precise, concise answer based solely on the evidence in the memories\n"
			"6. Double-check that your answer directly addresses the question asked\n"
			"7. Ensure your final answer is specific and avoids vague time references."
		)
		params = {
			"kiosk_mode": True,
			"threshold": 0.15,
			"limit": 30,
			"temperature": 0
		}
		data = {
			"question": question,
			"header_prompt": ANSWER_PROMPT
		}
		
		resp = requests.post(f"{self.endpoint_url}/api/v2/agents/{agent_id}/answer", headers=self._headers(), params=params, json=data)
		
		if not resp.ok:
			print(f"API Error {resp.status_code}: {resp.text}")
			
		resp.raise_for_status()
		return resp.json().get("answer", "")
		
	
	def ask_ai(self, question: str):
		data = {"query": question, "namespace": ""}
		headers = self._headers().copy()
		# Replace Authorization with x-api-key for Moorcheh API
		if "Authorization" in headers:
			headers.pop("Authorization")
		headers["x-api-key"] = self.api_key
		resp = requests.post(f"{self.moorcheh_url}/v1/answer", headers=headers, json=data)
		resp.raise_for_status()
		return resp.json().get("answer", "")
