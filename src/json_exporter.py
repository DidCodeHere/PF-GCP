"""
JSON Export Module for Web Interface

Exports scraped properties to JSON format for the static GitHub Pages frontend.
Includes timeout protection and error handling.
"""

import json
import os
from datetime import datetime
from typing import List, Optional
from dataclasses import asdict
from .models import Property


class JSONExporter:
    """Exports properties to JSON format for the web interface."""
    
    def __init__(self, output_dir: str = "data"):
        self.output_dir = output_dir
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """Create output directory if it doesn't exist."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def export_properties(
        self,
        properties: List[Property],
        location: str = "all",
        filename: Optional[str] = None
    ) -> str:
        """
        Export properties to JSON file.
        
        Args:
            properties: List of Property objects
            location: Search location (used for metadata)
            filename: Optional custom filename
            
        Returns:
            Path to the exported JSON file
        """
        if filename is None:
            filename = "properties.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Convert properties to dictionaries
        properties_data = []
        for prop in properties:
            try:
                prop_dict = self._property_to_dict(prop)
                properties_data.append(prop_dict)
            except Exception as e:
                print(f"[!] Error converting property {prop.id}: {e}")
                continue
        
        # Build export data with metadata
        export_data = {
            "lastUpdated": datetime.utcnow().isoformat() + "Z",
            "location": location,
            "totalCount": len(properties_data),
            "properties": properties_data
        }
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"[✓] Exported {len(properties_data)} properties to {filepath}")
        return filepath
    
    def _property_to_dict(self, prop: Property) -> dict:
        """Convert a Property object to a dictionary for JSON export."""
        return {
            "id": prop.id,
            "title": prop.title,
            "address": prop.address,
            "price": prop.price,
            "price_display": prop.price_display,
            "url": prop.url,
            "description": prop.description,
            "tenure": prop.tenure,
            "agent": prop.agent,
            "score": prop.investment_score,
            "category": prop.category,
            "ai_summary": prop.ai_summary,
            "llm_score": prop.llm_score,
            "llm_reasoning": prop.llm_reasoning,
            # Derived fields for frontend filtering
            "location": self._extract_location(prop.address)
        }
    
    def _extract_location(self, address: str) -> str:
        """Extract city/town from address for filtering."""
        if not address:
            return "Unknown"
        
        # Common UK cities to look for
        cities = [
            "London", "Manchester", "Birmingham", "Leeds", "Liverpool",
            "Sheffield", "Bristol", "Newcastle", "Nottingham", "Southampton",
            "Leicester", "Coventry", "Bradford", "Cardiff", "Belfast",
            "Edinburgh", "Glasgow", "Stoke", "Wolverhampton", "Derby",
            "Swansea", "Plymouth", "Reading", "Luton", "Bolton"
        ]
        
        address_upper = address.upper()
        for city in cities:
            if city.upper() in address_upper:
                return city
        
        # Fallback: try to extract from comma-separated parts
        parts = address.split(',')
        if len(parts) >= 2:
            # Usually city is second-to-last or third-to-last
            return parts[-2].strip() if len(parts) >= 2 else parts[-1].strip()
        
        return "Other"


def export_for_web(properties: List[Property], location: str = "all") -> str:
    """
    Convenience function to export properties for the web interface.
    
    Args:
        properties: List of Property objects
        location: Search location used
        
    Returns:
        Path to exported JSON file
    """
    exporter = JSONExporter()
    return exporter.export_properties(properties, location)
