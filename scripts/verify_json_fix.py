
import json
import re

# Precise failing strings from user
test_cases = [
    """ ```json
 easily visible objects in the image, with their types and quantities where applicable:
{
  "summary": "A group of people appear to be engaged in a physical altercation outdoors in what looks like a park or similar open space.",
  "threats": ["physical", "violence"],
  "severity": "medium",
  "confidence": 60,
  "weapons": []
}
``` """,
    """ ```json
GroupLayout {
  "summary": "Scene description...",
  "threats": ["low"], 
  "severity": "low",
  "confidence": 50
}
``` """
]

def extract_json(text):
    print(f"\n--- Testing Input ---\n{text[:60]}...")
    try:
        # 1. Strip Markdown Code Blocks
        text = re.sub(r'```json\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'```\s*', '', text)
        
        # 2. Find outermost braces
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            candidate = match.group(0)
            print(f"  Candidate: {candidate[:50]}...")
            
            # 3. Fix simple trailing commas (common LLM error)
            candidate = re.sub(r',\s*}', '}', candidate)
            candidate = re.sub(r',\s*]', ']', candidate)
            
            return json.loads(candidate)
    except Exception as e:
        print(f"  ERROR: {e}")
    return None

for t in test_cases:
    res = extract_json(t)
    if res:
        print(f"  SUCCESS: Severity={res.get('severity')}")
    else:
        print("  FAILED to parse.")
