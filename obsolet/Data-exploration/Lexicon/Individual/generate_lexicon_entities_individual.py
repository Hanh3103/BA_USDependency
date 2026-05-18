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
    """
    Normalize entity:
    - strip whitespace
    - lowercase
    - lemmatize each word
    """
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
        goal_entities = item['Entity']['Primary Entity']
        benefit_entities = item['Entity']['Secondary Entity']
        for entity in goal_entities: 
            lexicon.add(entity)
        for entity in benefit_entities:
            lexicon.add(entity)
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
        goal_entities = item['Entity']['Primary Entity']
        benefit_entities = item['Entity']['Secondary Entity']
        for entity in goal_entities: 
            entity = normalized_entity(entity)
            if entity: # Ensure we don't add empty strings
                lexicon.add(entity)
        for entity in benefit_entities:
            entity = normalized_entity(entity)
            if entity:
                lexicon.add(entity)
    return lexicon

def main():
    folder_path = '_nlp/baseline'  
    output_folder = 'Data-exploration/Lexicon/Individual/entity_lexicons_original'
    #output_folder = 'Data-exploration/Lexicon/Individual/entity_lexicons_normalized'
    os.makedirs(output_folder, exist_ok=True)
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)
            lexicon = build_lexicon_original(file_path)
            #lexicon = build_lexicon(file_path)
            with open(os.path.join(output_folder, f'{filename[:-5]}_entity_lexicon.json'), 'w') as f:
                json.dump(sorted(lexicon), f, indent=4)

if __name__ == "__main__":
    main()