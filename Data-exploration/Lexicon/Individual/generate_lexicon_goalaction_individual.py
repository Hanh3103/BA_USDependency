from pathlib import Path
import json
import nltk
from nltk.stem import WordNetLemmatizer

# Ensure WordNet corpus is downloaded
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

lemmatizer = WordNetLemmatizer()

def normalize_action(action: str) -> str:
    """
    Normalize action phrase:
    - strip whitespace
    - lowercase
    - lemmatize each word
    """
    words = action.strip().lower().split()
    lemmatized = [lemmatizer.lemmatize(word) for word in words]
    return ' '.join(lemmatized)

def build_lexicon(actions_list):
    """
    Given a list of action strings, return a set of normalized, unique actions.
    """
    lexicon = set()
    for action in actions_list:
        if not action or not action.strip():
            continue  # skip empty/blank strings
        normalized = normalize_action(action)
        if normalized:
            lexicon.add(normalized)
    return lexicon

def main():
    input_folder = Path('_nlp/baseline')
    output_folder = Path('Data-exploration/Lexicon/Individual/goal_action_lexicons')
    output_folder.mkdir(parents=True, exist_ok=True)

    for json_file in input_folder.glob('*.json'):
        with json_file.open('r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Assuming each data item has 'Action'->'Primary Action' list
        all_actions = []
        for item in data:
            primary_actions = item.get('Action', {}).get('Primary Action', [])
            if isinstance(primary_actions, list):
                all_actions.extend(primary_actions)

        lexicon = build_lexicon(all_actions)

        # Save sorted list of unique normalized actions
        output_file = output_folder / f"{json_file.stem}_goal_action_lexicon.json"
        with output_file.open('w', encoding='utf-8') as f:
            json.dump(sorted(lexicon), f, indent=4, ensure_ascii=False)

if __name__ == '__main__':
    main()