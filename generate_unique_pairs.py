import re
import itertools
import csv
import os

def read_user_stories(txt_file):
    """Read user stories from a txt file and clean them (remove any #GXX# prefix)."""
    pattern = re.compile(r'^#G\d+#\s*', re.IGNORECASE)
    with open(txt_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    # Remove the prefix dynamically for all lines
    stories = [pattern.sub('', line.strip()) for line in lines if line.strip()]
    return stories

def generate_unique_pairs(stories):
    """Generate all unique unordered pairs from the list of stories."""
    return list(itertools.combinations(stories, 2))

def write_pairs_to_csv(pairs, csv_file):
    """Write the list of pairs to a CSV file."""
    with open(csv_file, 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Story A', 'Story B'])
        for s1, s2 in pairs:
            writer.writerow([s1, s2])

def user_story_pairs_to_csv(txt_file, csv_file):
    """Main function: read txt, generate pairs, write to csv."""
    stories = read_user_stories(txt_file)
    pairs = generate_unique_pairs(stories)
    write_pairs_to_csv(pairs, csv_file)
    print(f"{len(pairs)} unique pairs written to '{csv_file}'")

if __name__ == "__main__":
    txt_file = "_raw/dalpiaz2018/g14-datahub.txt"  # Path to the specific file
    csv_file = "output/g14-datahub.csv"  # Output CSV file path

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)

    # Process the specific file
    user_story_pairs_to_csv(txt_file, csv_file)

