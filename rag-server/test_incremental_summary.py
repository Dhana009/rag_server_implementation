#!/usr/bin/env python3
"""Test incremental indexing behavior"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.tools.vector_crud import search_by_metadata

# Search for deleted file
result = search_by_metadata(
    {'must': [{'key': 'file_path', 'match': 'TEST_INCREMENTAL.md'}]}, 
    limit=10
)
data = json.loads(result)

print('=== TEST 4: Search for deleted file ===')
print('SUCCESS:', data['success'])
print('Results found:', data.get('data', {}).get('count', 0))
if data.get('data', {}).get('results'):
    first_result = data['data']['results'][0]
    print('First result is_deleted:', first_result.get('metadata', {}).get('is_deleted', False))
    print('First result file_path:', first_result.get('metadata', {}).get('file_path', 'N/A'))









