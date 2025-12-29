import json
import sys
import os
import time
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.llm_analyzer import LLMAnalyzer

def analyze_existing_data(data_path: str):
    if not os.path.exists(data_path):
        print(f"Error: File {data_path} not found.")
        return

    print(f"Loading data from {data_path}...")
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    properties_data = data.get('properties', [])
    
    llm = LLMAnalyzer()
    if not llm.is_available():
        print("Error: LLM Analyzer not available (check API key configuration).")
        return

    print(f"Loaded {len(properties_data)} properties.")
    
    # Sort by heuristic score to prioritize best candidates
    # We want to analyze the ones that are already promising
    properties_data.sort(key=lambda x: x.get('investment_score', 0) + x.get('score', 0), reverse=True)
    
    # Counter for how many we've analyzed in this run
    analyzed_count = 0
    max_to_analyze = 200  # Fast deterministic scoring
    
    print(f"Starting analysis on top {max_to_analyze} properties...")

    for i, prop in enumerate(properties_data):
        if analyzed_count >= max_to_analyze:
            break
            
        # Skip if already analyzed
        # if prop.get('llm_score') is not None and prop.get('llm_score') > 0:
        #     continue

        print(f"[{analyzed_count + 1}/{max_to_analyze}] Analyzing: {prop.get('address', 'Unknown')}")
        
        result = llm.analyze_property(prop)
        
        prop['llm_score'] = result['score']
        prop['llm_reasoning'] = result['reasoning']
        
        # Keep the base heuristic score stable; only lightly adjust on very strong signals.
        current_score = prop.get('score', 0)
        if result['score'] >= 10:
            prop['score'] = min(10, current_score + 1)
            print(f"  -> STRICT 10/10 matched. Score nudged to {prop['score']}")
        elif result['score'] >= 9:
            prop['score'] = min(10, current_score + 0.5)
            print(f"  -> Strong candidate. Score nudged to {prop['score']}")
        else:
            print(f"  -> AI Score: {result['score']}/10")
            
        analyzed_count += 1
        time.sleep(0.01)

    data['properties'] = properties_data
    
    print(f"Saving analyzed data to {data_path}...")
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        
    print("Analysis complete!")

if __name__ == "__main__":
    # Default to the standard location
    data_file = "data/properties.json"
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
        
    analyze_existing_data(data_file)