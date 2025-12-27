from dataclasses import dataclass
from typing import Optional

@dataclass
class Property:
    id: str
    title: str
    address: str
    price: float
    url: str
    description: str
    tenure: str = "Unknown"  # Freehold, Leasehold
    agent: str = "Unknown"
    investment_score: float = 0.0
    ai_summary: Optional[str] = None

    def __str__(self):
        return f"£{self.price:,.0f} - {self.address}"
