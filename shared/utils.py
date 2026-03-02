import json
from .prompts import get_judge_prompt_long_mem, get_judge_prompt_locomo

class LLM_Judge:
    def __init__(self, ask_ai_func, dataset_name):
        """
        Initializes the judge with a reference to your AI calling function.
        :param ask_ai_func: A function that takes a string prompt and returns a string response.
        :param dataset_name: Name of the dataset being evaluated.
        """
        self.ask_ai = ask_ai_func
        self.dataset_name = dataset_name

    def evaluate(self, question, prediction, ground_truth):
        try:
            # Generate the appropriate prompt based on the dataset
            if self.dataset_name.lower() == "locomo":
                prompt = get_judge_prompt_locomo(question, ground_truth, prediction)
            else:
                prompt = get_judge_prompt_long_mem(question, ground_truth, prediction)
            # Call your implemented ask_ai function
            response_str = self.ask_ai(prompt)

            # Clean potential markdown formatting
            cleaned_response = response_str.strip()
            
            # Find the JSON object in the string if it's mixed with text
            try:
                start_idx = cleaned_response.find('{')
                end_idx = cleaned_response.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    cleaned_response = cleaned_response[start_idx:end_idx+1]
            except Exception:
                pass  # Fallback to original string if extraction fails
                
            response = json.loads(cleaned_response)
            score = response.get('score', None)
            reasoning = response.get('reasoning', '')
            return {"score": score, "reasoning": reasoning}
        except Exception as e:
            print(f"Error during LLM Judging: {e}")
            # Fallback in case the AI fails or returns invalid JSON
            return {"score": 0, "reasoning": f"Error parsing judge response: {str(e)}"}