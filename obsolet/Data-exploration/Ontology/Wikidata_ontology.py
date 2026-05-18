import requests
import time

def get_wikidata_hypernyms(term, limit=5, verbose=True):
    search_url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbsearchentities",
        "language": "en",
        "format": "json",
        "search": term
    }
    # Retry logic for 429
    tries = 0
    while tries < 3:
        try:
            response = requests.get(search_url, params=params, timeout=10)
            if response.status_code == 429:
                if verbose:
                    print(f"429 Too Many Requests for '{term}', waiting 10s before retrying...")
                time.sleep(10)
                tries += 1
                continue
            response.raise_for_status()
            search_json = response.json()
            break
        except Exception as e:
            if verbose:
                print(f"Error for '{term}': {e}")
            return []
    else:
        if verbose:
            print(f"Giving up on '{term}' after 3 tries.")
        return []

    if not search_json.get("search"):
        if verbose:
            print(f"No Wikidata entity found for: {term}")
        return []
    qid = search_json["search"][0]["id"]
    
    sparql_query = f"""
    SELECT ?superclass ?superclassLabel WHERE {{
      wd:{qid} wdt:P279 ?superclass .
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
    }} LIMIT {limit}
    """
    url = "https://query.wikidata.org/sparql"
    headers = {"Accept": "application/sparql-results+json"}
    tries = 0
    while tries < 3:
        try:
            r = requests.get(url, params={"query": sparql_query}, headers=headers, timeout=20)
            if r.status_code == 429:
                if verbose:
                    print(f"429 Too Many Requests for SPARQL '{term}', waiting 10s...")
                time.sleep(10)
                tries += 1
                continue
            r.raise_for_status()
            results = r.json().get("results", {}).get("bindings", [])
            break
        except Exception as e:
            if verbose:
                print(f"SPARQL error for '{term}': {e}")
            return []
    else:
        if verbose:
            print(f"SPARQL: Giving up on '{term}' after 3 tries.")
        return []

    hypernyms = []
    for res in results:
        label = res["superclassLabel"]["value"]
        qid = res["superclass"]["value"].split("/")[-1]
        hypernyms.append((label, qid))
    time.sleep(2)  # increase to 2s minimum!
    return hypernyms

# EXAMPLE USAGE
for term in ["age"]:
    print(f"Hypernyms for '{term}':")
    hypernyms = get_wikidata_hypernyms(term)
    if not hypernyms:
        print("  - No hypernyms found or no entity in Wikidata.")
    else:
        for label, qid in hypernyms:
            print(f"  - {label} (https://www.wikidata.org/wiki/{qid})")
    print()
