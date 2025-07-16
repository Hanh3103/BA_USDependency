import re
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

# def normalize_phrase(phrase: str) -> str:
#     """
#     Normalize a phrase for grouping purposes:
#     - Lowercase
#     - Remove possessive "'s"
#     - Remove extra punctuation (commas, periods)
#     - Lemmatize each word
#     - Collapse multiple spaces
#     """
#     phrase = phrase.lower()
#     phrase = re.sub(r"'s\b", "", phrase)         # Remove possessive endings
#     phrase = re.sub(r"[^\w\s]", "", phrase)      # Remove punctuation except spaces
#     words = phrase.strip().split()
#     lemmatized_words = [lemmatizer.lemmatize(w) for w in words]
#     return " ".join(lemmatized_words)

def normalize_entity(entity):
    entity = entity.strip().lower()
    if not entity:
        return None
    tokens = re.findall(r'[\w-]+', entity) # matches sequences of letters/digits (word characters) AND hyphens as a single token
    lemmatized_tokens = [lemmatizer.lemmatize(token) for token in tokens]
    return ' '.join(lemmatized_tokens)

def build_lexicon(file_path):
    lexicon = set()
    with open(file_path, 'r') as f:
        data = json.load(f)
    for item in data:
        goal_entities = item['Entity']['Primary Entity']
        for entity in goal_entities: 
            normalized = normalize_entity(entity)
            if normalized:
                lexicon.add(normalized)
    return lexicon

def build_lexicon_original(file_path):
    lexicon = set()
    with open(file_path, 'r') as f:
        data = json.load(f)
    for item in data:
        goal_entities = item['Entity']['Primary Entity']
        for entity in goal_entities: 
            lexicon.add(entity)
    return lexicon

def main():
    folder_path = '_nlp/baseline'  
    output_folder = 'Data-exploration/Lexicon/Individual/goal_entity_lexicons_normalized'
    os.makedirs(output_folder, exist_ok=True)
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)
            lexicon = build_lexicon(file_path)
            with open(os.path.join(output_folder, f'{filename[:-5]}_goal_entity_lexicon.json'), 'w') as f:
                json.dump(sorted(lexicon), f, indent=4)

if __name__ == "__main__":
    main()