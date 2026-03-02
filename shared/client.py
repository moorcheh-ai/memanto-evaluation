import requests
import os
import logging
from .prompts import LOCOMO_HEADER_ANSWER_PROMPT, LONGMEM_HEADER_ANSWER_PROMPT

logger = logging.getLogger(__name__)

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

	def search_memory(self, agent_id: str, query: str, limit: int, tags: list = None):
		params = {"query": query, "limit": limit}
		resp = requests.get(f"{self.endpoint_url}/api/v2/agents/{agent_id}/recall", params=params, headers=self._headers())
		resp.raise_for_status()
		return resp.json().get("memories", [])

	def answer(self, dataset_name, agent_id: str, question: str, threshold: float, limit: int):
		params = {
			"kiosk_mode": True,
			"threshold": threshold,
			"limit": limit,
			"temperature": 0
		}
		data = {
			"question": question,
			"header_prompt": LONGMEM_HEADER_ANSWER_PROMPT if dataset_name.lower() == "longmem" else LOCOMO_HEADER_ANSWER_PROMPT
		}
		
		resp = requests.post(f"{self.endpoint_url}/api/v2/agents/{agent_id}/answer", headers=self._headers(), params=params, json=data)
		
		if not resp.ok:
			logger.error(f"API Error {resp.status_code}: {resp.text}")
			
		resp.raise_for_status()
		data = resp.json()
		return data.get("answer", "")
		
	
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

	def batch_store_memories(self, agent_id: str, memories: list):
		"""
		Batch store memories.
		memories: list of dicts, each with keys:
		  - content (required)
		  - title (optional)
		  - tags (optional)
		  - type (optional, default "context")
		"""
		payload = {"memories": []}
		for mem in memories:
			payload["memories"].append({
				"content": mem.get("content"),
				"title": mem.get("title", "Batch Memory"),
				"tags": mem.get("tags", []),
				"type": mem.get("type", "fact"),
				"confidence": mem.get("confidence", 0.8)
			})

		resp = requests.post(
			f"{self.endpoint_url}/api/v2/agents/{agent_id}/batch-remember",
			headers=self._headers(),
			json=payload
		)
		if not resp.ok:
			logger.error(f"Batch store error: {resp.status_code} - {resp.text}")
		resp.raise_for_status()
		return resp.json()
