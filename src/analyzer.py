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

    def is_land(self, prop: Property) -> bool:
        """Checks if a property is likely land."""
        description_lower = (prop.description + " " + prop.title).lower()
        return "land for sale" in description_lower or "plot of land" in description_lower or prop.title.lower().startswith("land")

    def analyze(self, properties: List[Property], exclude_land: bool = False) -> List[Property]:
        """
        Analyzes a list of properties and assigns an investment score.
        """
        analyzed_properties = []
        
        for prop in properties:
            # Strict Filtering: Exclude Land
            if exclude_land and self.is_land(prop):
                continue

            score = 0
            description_lower = (prop.description + " " + prop.title).lower()

            # Base score for price (lower is better, cap at 100k already filtered)
            if prop.price is not None:
                if prop.price < 50000:
                    score += 2
                elif prop.price < 80000:
                    score += 1
            else:
                # If price is N/A (e.g. Auction), give it a slight boost as it might be a deal
                score += 1

            # Keyword matching
            found_high_priority = False
            found_medium_priority = False
            
            for keyword in self.positive_keywords:
                if re.search(keyword, description_lower):
                    # Boost specifically requested "distressed" keywords
                    if keyword in [r"auction", r"eviction", r"unlivable", r"fire damage", r"repossession", r"derelict", r"structural"]:
                        score += 3
                        found_high_priority = True
                    else:
                        score += 1.5
                        found_medium_priority = True
            
            # Penalize for unwanted types if they slipped through
            for keyword in self.negative_keywords:
                if re.search(keyword, description_lower):
                    score -= 5

            # Freehold check (Critical)
            if "freehold" in description_lower:
                score += 2
            elif "leasehold" in description_lower:
                score -= 5

            # Land Penalty (User Request: Land should score lower than residential)
            is_land_prop = self.is_land(prop)
            if is_land_prop:
                score -= 10  # Heavy penalty to ensure it's below residential

            prop.investment_score = score
            
            # Categorization
            if is_land_prop:
                prop.category = "Land"
            elif found_high_priority:
                prop.category = "Distressed"
            elif found_medium_priority:
                prop.category = "Fixer Upper"
            else:
                prop.category = "Standard"

            # Simple "AI" summary based on keywords found
            found_keywords = [k for k in self.positive_keywords if re.search(k, description_lower)]
            if found_keywords:
                prop.ai_summary = f"Potential detected: {', '.join(found_keywords).replace(r'', '')}"
            else:
                prop.ai_summary = "Standard listing."
            
            analyzed_properties.append(prop)

        # Sort by score descending, then price ascending (handling None price)
        analyzed_properties.sort(key=lambda x: (-x.investment_score, x.price if x.price is not None else float('inf')))
        return analyzed_properties
