import json
import csv
import itertools

def extract_field(item, key_path):
    # Support for single- or multi-element lists, return joined string or empty if missing
    for key in key_path:
        item = item.get(key, [])
    if isinstance(item, list):
        return ', '.join([str(e) for e in item if e])
    elif item is None:
        return ''
    return str(item)

def load_stories(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_flat_story(item):
    return {
        'Story': item['Text'],
        'GoalAction': extract_field(item, ['Action', 'Primary Action']),
        'GoalEntity': extract_field(item, ['Entity', 'Primary Entity']),
        'BenefitAction': extract_field(item, ['Action', 'Secondary Action']),
        'BenefitEntity': extract_field(item, ['Entity', 'Secondary Entity'])
    }

def generate_pairs(json_file, csv_file):
    stories = load_stories(json_file)
    flat_stories = [build_flat_story(item) for item in stories]
    pairs = itertools.combinations(flat_stories, 2)

    header = [
        'Story_A', 'Story_B',
        'GoalAction_A', 'GoalAction_B',
        'GoalEntity_A', 'GoalEntity_B',
        'BenefitAction_A', 'BenefitAction_B',
        'BenefitEntity_A', 'BenefitEntity_B'
    ]
    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for a, b in pairs:
            row = [
                a['Story'], b['Story'],
                a['GoalAction'], b['GoalAction'],
                a['GoalEntity'], b['GoalEntity'],
                a['BenefitAction'], b['BenefitAction'],
                a['BenefitEntity'], b['BenefitEntity']
            ]
            writer.writerow(row)
    print(len(flat_stories), "stories processed, pairs generated:", len(list(itertools.combinations(flat_stories, 2))))

if __name__ == "__main__":
    json_file = "_nlp/baseline/g14_baseline.json"  # Path to the JSON file
    csv_file = "CSV-schema-generation/output_details/g14-datahub_baseline.csv"  # Output CSV file path

     # Ensure the output directory exists if needed
    import os
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)
    print(f"Output directory created if it did not exist: {os.path.dirname(csv_file)}")

    generate_pairs(json_file, csv_file)
    print(f"Generated pairs from {json_file} and saved to {csv_file}")
