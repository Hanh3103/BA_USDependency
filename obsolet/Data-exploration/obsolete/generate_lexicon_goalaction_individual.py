import json
import os
import nltk
from nltk.stem import WordNetLemmatizer
from collections import defaultdict

# Download WordNet corpus if it's not already downloaded
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')
    
lemmatizer = WordNetLemmatizer()

def build_lexicon(file_path):
    #lexicon = defaultdict(lambda: {'frequency': 0, 'us': []})
    lexicon = defaultdict(lambda: {'frequency': 0})
    with open(file_path, 'r') as f:
        data = json.load(f)
    for item in data:
        primary_actions = item['Action']['Primary Action']
        for action in primary_actions:
            # Convert to lowercase and lemmatize the word
            lemmatized_action = lemmatizer.lemmatize(action.lower())
            lexicon[lemmatized_action]['frequency'] += 1
            #lexicon[lemmatized_action]['us'].append(item['Text'])
    # Sort the lexicon by frequency
    sorted_lexicon = dict(sorted(lexicon.items(), key=lambda item: item[1]['frequency'], reverse=True))
    return sorted_lexicon

def main():
    folder_path = '_nlp/baseline' # input folder containing JSON files
    output_folder = 'Data-exploration/goal_action_lexicons' # output folder for individual lexicons
    os.makedirs(output_folder, exist_ok=True)
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)
            lexicon = build_lexicon(file_path)
            with open(os.path.join(output_folder, f'{filename[:-5]}_primary_action_lexicon.json'), 'w') as f:
                json.dump(lexicon, f, indent=4)

if __name__ == "__main__":
    main()