from nltk.corpus import wordnet as wn
import pandas as pd

phrases = [
    "affidavit", "appeal", "application", "approved proffer", "bond",
    "building development project", "citation", "code modification",
    "completeness review", "completion of required plan review", "consistency",
    "custom query report", "customer portal user account", "development-related permit",
    "draft proffer", "each condo unit", "fee", "fine", "formal response",
    "gi property management", "hearing calendar", "hearing date", "hearing decision",
    "hearing execution", "hearing requirement", "hold", "information", "inspection",
    "inspector workload", "internal note", "meeting", "notice of violation",
    "ordinance", "outcome", "plan", "plan amendment", "plan review meeting",
    "plan reviewer workload", "planning study", "planning-related report",
    "preapplication assistance", "property information", "request", "requirement",
    "service", "staff report", "staff review", "status", "supporting documentation",
    "when", "zoning-related permit"
]

# Extract hypernyms for each phrase
def get_hypernyms(phrase):
    phrase = phrase.replace(" ", "_")
    synsets = wn.synsets(phrase)
    hypernyms = set()
    for syn in synsets:
        for path in syn.hypernym_paths():
            for hypernym in path:
                hypernyms.update(hypernym.lemma_names())
    return list(hypernyms)

hypernym_data = []
for phrase in phrases:
    hypernyms = get_hypernyms(phrase)
    hypernym_data.append({
        "phrase": phrase,
        "hypernyms": hypernyms if hypernyms else ["No hypernym found"]
    })

# Convert results to DataFrame
hypernym_df = pd.DataFrame(hypernym_data)

# Display DataFrame
print(hypernym_df)
hypernym_df.to_csv('hypernyms.csv', index=False)




