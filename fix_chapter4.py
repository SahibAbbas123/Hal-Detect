import re

with open("thesis_latex/Chapter4/chapter4.tex", "r") as f:
    text = f.read()

# Fix Bug B
bug_b_target = r"and (b) source-existence misattributions (e.g., claim \texttt{Q22\_C01} regarding FAO food insecurity trends, corrected to gold \texttt{FALSE})."
bug_b_replacement = r"and (b) ``Bug B'', an entity disambiguation defect where unscored Wikidata search queries fetched incorrect homonyms instead of committing via SBERT, resulting in 14 label revisions across Phase 2."
text = text.replace(bug_b_target, bug_b_replacement)

# Fix Paragraph vs Proposition counts (mn11)
# Search for the sentence: "The suite comprises 200 input paragraphs yielding 1,437 extracted propositions"
prop_target = r"The Track 1 Master Benchmark (\(N=1,000\)) represents a meticulously curated, uniformly distributed 50/50 dataset"
if "yielding 1,437 extracted propositions" not in text:
    prop_replacement = r"From an initial corpus of 200 raw input paragraphs, the Schema Atomizer extracted 1,437 atomic propositions (of which 112 are gold \texttt{TRUE} and 88 are gold \texttt{FALSE} at the proposition level, with the remainder being \texttt{UNVERIFIABLE}). The Track 1 Master Benchmark (\(N=1,000\)) was then sampled from this extraction to form a meticulously curated, uniformly distributed 50/50 dataset"
    text = text.replace(prop_target, prop_replacement)

with open("thesis_latex/Chapter4/chapter4.tex", "w") as f:
    f.write(text)
