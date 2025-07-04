import json

import json

def nodes_with_multiple_primary_actions(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    result = []
    for node in data:
        primary_actions = node.get('Action', {}).get('Primary Action', [])
        if len(primary_actions) > 1:
            result.append(node)
    return result


if __name__ == "__main__":
    filename = '_nlp/baseline/g04_baseline.json'  # Path to the JSON file
    nodes = nodes_with_multiple_primary_actions(filename)
    
    if nodes:
        print(f"Found {len(nodes)} nodes with multiple primary actions:")
        for node in nodes:
            print(json.dumps(node, indent=2, ensure_ascii=False))
    else:
        print("No nodes with multiple primary actions found.")
