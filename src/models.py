from dataclasses import dataclass
from typing import Optional

@dataclass
class Property:
    id: str
    title: str
    address: str
    price: Optional[float]
    url: str
    description: str
    tenure: str = "Unknown"  # Freehold, Leasehold
    agent: str = "Unknown"
    investment_score: float = 0.0
    ai_summary: Optional[str] = None
    category: str = "Standard" # e.g. Fixer Upper, Ready to Rent, Land
    llm_score: Optional[float] = None
    llm_reasoning: Optional[str] = None
    price_display: str = "" # For "POA", "Guide Price", etc.

    def __post_init__(self):
        if not self.price_display:
            self.price_display = f"£{self.price:,.0f}" if self.price is not None else "N/A"

    def __str__(self):
        return f"{self.price_display} - {self.address}"
        return f"£{self.price:,.0f} - {self.address}"
