import requests

WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
USER_AGENT = "AcademicResearchBot/2.5 (contact@example.com)"

query = """
SELECT ?item ?itemLabel ?sitelinks (GROUP_CONCAT(?altLabel; separator="|") AS ?altLabels) WHERE {
  ?container rdfs:label "France"@en .
  ?container wdt:P36 ?item .
  ?container wikibase:sitelinks ?sitelinks .
  OPTIONAL { ?item skos:altLabel ?altLabel . FILTER (lang(?altLabel) = "en") }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
} GROUP BY ?item ?itemLabel ?sitelinks ORDER BY DESC(?sitelinks) LIMIT 1
"""
resp = requests.get(
    WIKIDATA_SPARQL,
    params={"query": query, "format": "json"},
    headers={"User-Agent": USER_AGENT},
    timeout=5.0
)
print(resp.json())
