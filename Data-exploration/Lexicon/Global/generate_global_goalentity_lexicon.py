import json
import os
import nltk
from nltk.stem import WordNetLemmatizer

nltk.download('wordnet')
lemmatizer = WordNetLemmatizer()

def build_lexicon(file_path):
    lexicon = set()
    with open(file_path, 'r') as f:
        data = json.load(f)
    for item in data:
        primary_entities = item['Entity']['Primary Entity']
        for entity in primary_entities:
            # Convert to lowercase and lemmatize the word
            lemmatized_entity = lemmatizer.lemmatize(entity.lower())
            lexicon.add(lemmatized_entity)
    return lexicon

def main():
    folder_path = '_nlp/baseline'  # path to your folder
    lexicon = set()
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)
            file_lexicon = build_lexicon(file_path)
            for entity in file_lexicon:
                lexicon.add(entity)
    with open('Data-exploration/Lexicon/Global/GoalEntity_lexicon.json', 'w') as f:
        json.dump(sorted(lexicon), f, indent=4) # sort the lexicon by alphabetical order

if __name__ == "__main__":
    main()