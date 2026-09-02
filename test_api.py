import requests

WIKIDATA_API = "https://www.wikidata.org/w/api.php"
USER_AGENT = "AcademicResearchBot/1.0 (contact@example.com)"

resp = requests.get(
    WIKIDATA_API,
    params={
        "action": "wbsearchentities",
        "search": "France",
        "language": "en",
        "format": "json",
        "limit": 1
    },
    headers={"User-Agent": USER_AGENT},
    timeout=3.0
)
print(resp.status_code)
print(resp.json())
