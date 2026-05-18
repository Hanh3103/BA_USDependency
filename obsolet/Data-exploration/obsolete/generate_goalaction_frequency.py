import json
import os
import nltk
from nltk.stem import WordNetLemmatizer
from collections import defaultdict

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
    return dict(lexicon)

def main():
    folder_path = '_nlp/baseline'  # path to your folder
    #lexicon = defaultdict(lambda: {'frequency': 0, 'us': []})
    lexicon = defaultdict(lambda: {'frequency': 0})
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)
            file_lexicon = build_lexicon(file_path)
            for action, info in file_lexicon.items():
                lexicon[action]['frequency'] += info['frequency']
                #lexicon[action]['us'].extend(info['us'])
    # Sort the lexicon by frequency
    sorted_lexicon = dict(sorted(lexicon.items(), key=lambda item: item[1]['frequency'], reverse=True))
    with open('Data-exploration/GoalAction_lexicon.json', 'w') as f:
        json.dump(sorted_lexicon, f, indent=4)

if __name__ == "__main__":
    main()