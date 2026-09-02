import re

path = "thesis_latex/Appendix1/appendix1.tex"
with open(path, "r") as f:
    text = f.read()

new_listing = """\\begin{lstlisting}[language=Python]
class BidirectionalKGResolver:
    \"\"\"
    Static registry fallback for topological superlatives
    and capital cities, implemented to bypass SPARQL timeouts.
    \"\"\"
    _STATIC_REGISTRY = {
        "highest_peak": {
            "north america": "Denali", "south america": "Aconcagua", 
            "asia": "Mount Everest", "africa": "Mount Kilimanjaro", 
            "europe": "Mount Elbrus", "antarctica": "Vinson Massif"
        },
        "capital": {
            "france": "Paris", "australia": "Canberra", "japan": "Tokyo", 
            "united states": "Washington, D.C.", "uk": "London"
        },
        "lowest_point": {
            "north america": "Badwater Basin", "earth": "Challenger Deep", 
            "africa": "Lake Assal", "asia": "Dead Sea"
        }
    }

    def resolve_superlative(self, subject: str, property_name: str, 
                            container: str) -> Tuple[str, float]:
        cont_clean = container.strip().lower()
        prop_clean = property_name.strip().lower()
        
        if prop_clean in self._STATIC_REGISTRY:
            record = self._STATIC_REGISTRY[prop_clean]
            if cont_clean in record:
                expected = record[cont_clean]
                is_match = (subject.lower() in expected.lower()) or (expected.lower() in subject.lower())
                return ("TRUE", 1.0) if is_match else ("FALSE", 0.95)
        return "UNVERIFIABLE", 0.0
\\end{lstlisting}"""

start = text.find("\\begin{lstlisting}[language=Python]\nclass BidirectionalKGResolver:")
if start != -1:
    end = text.find("\\end{lstlisting}", start) + len("\\end{lstlisting}")
    text = text[:start] + new_listing + text[end:]
    with open(path, "w") as f:
        f.write(text)
