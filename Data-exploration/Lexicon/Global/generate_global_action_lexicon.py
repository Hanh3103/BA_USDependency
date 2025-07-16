import json
import os
import nltk
from nltk.stem import WordNetLemmatizer

# Download WordNet corpus if it's not already downloaded
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')
    
lemmatizer = WordNetLemmatizer()

def normalized_entity(entity: str) -> str:
    words = entity.strip().lower().split()
    lemmatized = [lemmatizer.lemmatize(word) for word in words]
    return ' '.join(lemmatized)

def build_lexicon_original(file_path):

    """
    Build a lexicon of entities from the JSON file.
    The lexicon includes both goal and benefit entities.
    """
    lexicon = set()
    with open(file_path, 'r') as f:
        data = json.load(f)
    for item in data:
        goal_actions = item['Action']['Primary Action']
        benefit_actions = item['Action']['Secondary Action']
        for action in goal_actions: 
            lexicon.add(action)
        for action in benefit_actions:
            lexicon.add(action)
    return lexicon

def build_lexicon(file_path):
    """
    Build a lexicon of entities from the JSON file.
    The lexicon includes both goal and benefit entities, normalized.
    """
    lexicon = set()
    with open(file_path, 'r') as f:
        data = json.load(f)
    for item in data:
        goal_actions = item['Action']['Primary Action']
        benefit_actions = item['Action']['Secondary Action']
        for action in goal_actions: 
            action = normalized_entity(action)
            if action: # Ensure we don't add empty strings
                lexicon.add(action)
        for action in benefit_actions:
            action = normalized_entity(action)
            if action:
                lexicon.add(action)
    return lexicon

def main():
    folder_path = '_nlp/baseline'  # path to your folder
    lexicon = set()
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)
            file_lexicon = build_lexicon(file_path)
            for action in file_lexicon:
                lexicon.add(action)
    with open('Data-exploration/Lexicon/Global/action_lexicon_normalized.json', 'w') as f:
        json.dump(sorted(lexicon), f, indent=4) # sort the lexicon by alphabetical order

if __name__ == "__main__":
    main()
