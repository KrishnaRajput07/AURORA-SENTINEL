
import json
import re

test_cases = [
    # Case 1: Extra text inside code block
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
    
    # Case 2: Clean
    """ ```json

{
    "summary": "Two people are wrestling in a park. One person appears to be falling while the other has them pinned down.",
    "threats": [],
    "severity": "low",
    "confidence": 70
}
``` """,

    # Case 3: GroupLayout prefix
    """ ```json
GroupLayout {
  "summary": "This image depicts a scene where a person is attempting to hold another individual from the ground. The environment suggests an outdoor setting with people in casual clothing and a playground in the background.",
  "threats": ["low"],
  "severity": "low",
  "confidence": 50
}
``` """
]

def parse(raw_text):
    print(f"\n--- Parsing Input ---\n{raw_text[:50]}...")
    parsed_data = {}
    try:
        # Current Logic in offline_processor.py
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if json_match:
            candidate = json_match.group(0)
            print(f"  Regex Match: {candidate[:50]}...")
            parsed_data = json.loads(candidate)
            print("  SUCCESS: Parsed JSON")
            print(f"  Severity: {parsed_data.get('severity')}")
        else:
            print("  FAIL: No JSON extraction regex match")
    except Exception as e:
        print(f"  ERROR: {e}")

for text in test_cases:
    parse(text)
