from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL

g= Graph()
g.parse("yago.ttl", format="ttl")

entity = "accounting"
g.bind("yago", Namespace("http://yago-knowledge.org/resource/"))
g.bind("rdf", RDF)
g.bind("rdfs", RDFS)
g.bind("owl", OWL)

def get_hypernym(entity):
    hypernym= set()
    for cls in g.objects(entity, RDF.type):
        stack = [cls]
        while stack:
            current = stack.pop()
            hypernym.add(current)
            for parent in g.objects(current, RDFS.subClassOf):
                if parent not in hypernym:
                    stack.append(parent)
    return hypernym

hypernyms = get_hypernym(URIRef(f"http://yago-knowledge.org/resource/{entity}"))

for hypernym in hypernyms:
    g.add((URIRef(f"http://yago-knowledge.org/resource/{entity}"), RDFS.subClassOf, hypernym))

g.serialize(destination="yago_ontology.ttl", format="turtle")
print(f"Ontology for {entity} has been created and saved to 'yago_ontology.ttl'.")
