import os

thesis_path = "thesis_latex/Chapter3/chapter3.tex"
with open(thesis_path, "r") as f:
    th = f.read()

# Replace the claim of "Dynamic SPARQL" with "Static Registry Cache"
th = th.replace("executes time-scoped SPARQL statement filtering over Wikidata ($P580$ start time, $P582$ end time) to verify historical appointments, terms, and state transitions. To resolve inverse topological superlatives (e.g., \\textit{\"the highest point in Europe\"}), it dynamically queries Wikidata property $P610$ (highest point).", "executes time-scoped SPARQL statement filtering over Wikidata ($P580$ start time, $P582$ end time) to verify historical appointments, terms, and state transitions. Due to severe API rate-limiting and query timeouts encountered during dynamic SPARQL execution, inverse topological superlatives (e.g., \\textit{\"the highest point in Europe\"}) and capital cities are resolved using a curated, high-speed static fallback registry.")
th = th.replace("Dynamic SPARQL & topological superlative resolution", "Static topological superlative and capital city resolution")

with open(thesis_path, "w") as f:
    f.write(th)

