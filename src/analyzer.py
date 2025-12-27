import re
from typing import List
from .models import Property

class PropertyAnalyzer:
    def __init__(self):
        self.positive_keywords = [
            r"modernisation", r"refurbishment", r"renovation", r"repair",
            r"development opportunity", r"investment opportunity", r"fixer upper",
            r"unmodernised", r"cash buyers", r"planning permission", r"freehold",
            r"derelict", r"structural", r"project",
            # New high priority keywords
            r"auction", r"repossession", r"eviction", r"unlivable", r"fire damage",
            r"water damage", r"vandalised", r"uninhabitable", r"condemned", r"dangerous",
            r"unsafe", r"gutted", r"shell", r"squatters"
        ]
        self.negative_keywords = [
            r"shared ownership", r"leasehold", r"retirement", r"park home",
            r"holiday home", r"student"
        ]

    def analyze(self, properties: List[Property]) -> List[Property]:
        """
        Analyzes a list of properties and assigns an investment score.
        """
        for prop in properties:
            score = 0
            description_lower = (prop.description + " " + prop.title).lower()

            # Base score for price (lower is better, cap at 100k already filtered)
            if prop.price < 50000:
                score += 2
            elif prop.price < 80000:
                score += 1

            # Keyword matching
            for keyword in self.positive_keywords:
                if re.search(keyword, description_lower):
                    # Boost specifically requested "distressed" keywords
                    if keyword in [r"auction", r"eviction", r"unlivable", r"fire damage", r"repossession"]:
                        score += 3
                    else:
                        score += 1.5
            
            # Penalize for unwanted types if they slipped through
            for keyword in self.negative_keywords:
                if re.search(keyword, description_lower):
                    score -= 5

            # Freehold check (Critical)
            if "freehold" in description_lower:
                score += 2
            elif "leasehold" in description_lower:
                score -= 5

            prop.investment_score = score
            
            # Simple "AI" summary based on keywords found
            found_keywords = [k for k in self.positive_keywords if re.search(k, description_lower)]
            if found_keywords:
                prop.ai_summary = f"Potential detected: {', '.join(found_keywords).replace(r'', '')}"
            else:
                prop.ai_summary = "Standard listing."

        # Sort by score descending, then price ascending
        properties.sort(key=lambda x: (-x.investment_score, x.price))
        return properties
