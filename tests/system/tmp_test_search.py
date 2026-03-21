
import sys
import os
# Auto-injected to allow imports from project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import os
import sys

# Add backend to path


from backend.services.search_service import search_service

print(f"Vector Enabled: {search_service._vector_enabled}")
print(f"Collection: {search_service.collection}")

query = "fight"
results = search_service.search(query)
print(f"Search results for '{query}': {results}")

query = "general description"
results = search_service.search(query)
print(f"Search results for '{query}': {results}")
