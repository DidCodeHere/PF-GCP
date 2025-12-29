import ollama
from typing import Optional

class LLMAnalyzer:
    def __init__(self, model_name: str = "llama3"):
        self.model_name = model_name

    def analyze_description(self, description: str) -> dict:
        """
        Analyzes the property description using a local LLM.
        Returns a dictionary with 'score' (1-10) and 'reasoning'.
        """
        prompt = f"""
        You are a property investment expert looking for "fixer-upper" opportunities in the UK.
        Analyze the following property description and assign an investment potential score from 1 to 10.
        
        Scoring Criteria:
        - 10: Unlivable, derelict, fire damaged, structural issues (High profit potential).
        - 7-9: Requires full modernisation/refurbishment.
        - 4-6: Dated, needs cosmetic work.
        - 1-3: Move-in ready, modern, or leasehold/shared ownership (Low profit potential).

        Description:
        "{description}"

        Return your response in this exact format:
        Score: [Number]
        Reasoning: [One sentence summary]
        """

        try:
            response = ollama.chat(model=self.model_name, messages=[
                {'role': 'user', 'content': prompt},
            ])
            content = response['message']['content']
            
            # Parse the response
            score = 0
            reasoning = "Could not parse LLM response."
            
            for line in content.split('\n'):
                if line.startswith("Score:"):
                    try:
                        score = float(line.replace("Score:", "").strip())
                    except:
                        pass
                elif line.startswith("Reasoning:"):
                    reasoning = line.replace("Reasoning:", "").strip()
            
            return {"score": score, "reasoning": reasoning}

        except Exception as e:
            print(f"[!] LLM Error: {e}")
            return {"score": 0, "reasoning": "LLM analysis failed."}

    def is_available(self) -> bool:
        """Checks if Ollama is running and the model is available."""
        try:
            ollama.list()
            return True
        except:
            return False
