import requests

WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
USER_AGENT = "AcademicResearchBot/1.0 (contact@example.com)"

query = """
SELECT ?item ?itemLabel WHERE {
  ?container rdfs:label "France"@en .
  ?container wdt:P36 ?item .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
} LIMIT 1
"""
resp = requests.get(
    WIKIDATA_SPARQL,
    params={"query": query, "format": "json"},
    headers={"User-Agent": USER_AGENT},
    timeout=5.0
)
print(resp.status_code)
if resp.status_code == 200:
    print(resp.json())
else:
    print(resp.text)
