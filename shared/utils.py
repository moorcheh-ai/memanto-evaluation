import json

class LLM_Judge:

    def _extract_first_json(self, text):
        import re
        # Try to find the first JSON object or array in the string
        match = re.search(r'({[\s\S]*?}|\[[\s\S]*?\])', text)
        if match:
            json_str = match.group(0)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # Naive fix: replace single quotes with double quotes
                fixed = re.sub(r"'", '"', json_str)
                return json.loads(fixed)
        raise ValueError("No JSON object found in response")
        
    def __init__(self, ask_ai_func):
        """
        Initializes the judge with a reference to your AI calling function.
        :param ask_ai_func: A function that takes a string prompt and returns a string response.
        """
        self.ask_ai = ask_ai_func

    def evaluate(self, question, prediction, ground_truth):
        prompt = f"""
        Your task is to label an answer to a question as 1 (CORRECT) or 0 (WRONG). You will be given the following data:
            (1) a question (posed by one user to another user),
            (2) a 'gold' (ground truth) answer,
            (3) a generated answer
        which you will score as 1 (CORRECT) or 0 (WRONG).

        The point of the question is to ask about something one user should know about the other user based on their prior conversations.
        The gold answer will usually be a concise and short answer that includes the referenced topic, for example:
        Question: Do you remember what I got the last time I went to Hawaii?
        Gold answer: A shell necklace
        The generated answer might be much longer, but you should be generous with your grading - as long as it touches on the same topic as the gold answer, it should be counted as 1 (CORRECT).

        For time related questions, the gold answer will be a specific date, month, year, etc. The generated answer might be much longer or use relative time references (like "last Tuesday" or "next month"), but you should be generous with your grading - as long as it refers to the same date or time period as the gold answer, it should be counted as 1 (CORRECT). Even if the format differs (e.g., "May 7th" vs "7 May"), consider it 1 (CORRECT) if it's the same date.

        Now it’s time for the real question:
        Question: {question}
        Gold answer: {ground_truth}
        Generated answer: {prediction}

        Return ONLY a JSON object: {{"score": 0 or 1, "reasoning": "string"}}
        """
        try:
            # 1. Call your implemented ask_ai function
            raw_response = self.ask_ai(prompt)
            # 2. Clean the response (LLMs sometimes wrap JSON in markdown blocks like ```json)
            clean_response = raw_response.strip().replace("```json", "").replace("```", "")
            # 3. Parse and return only the first JSON object
            result = self._extract_first_json(clean_response)
            score = result.get('score', None)
            reasoning = result.get('reasoning', '') if 'reasoning' in result else ''
            return {"score": score, "reasoning": reasoning}
        except Exception as e:
            print(f"Error during LLM Judging: {e}")
            # Fallback in case the AI fails or returns invalid JSON
            return {"score": 0, "reasoning": f"Error parsing judge response: {str(e)}"}