
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from locomo.evaluator import LoCoMoEvaluator

if __name__ == "__main__":
	endpoint_url = "http://127.0.0.1:8000"
	evaluator = LoCoMoEvaluator(endpoint_url, num_clients=5)
	evaluator.run()
