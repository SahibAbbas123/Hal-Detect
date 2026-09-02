import csv, re, sys, collections
sys.path.append("current")

rows = list(csv.DictReader(open("current/master_corpus_v2_evolved_hd2_results.csv", encoding="utf-8")))

# The "Evolved Wikipedia Semantic Grounding" uses 60% word overlap threshold
# Let's see what threshold distribution looks like for the abstained claims
# by re-simulating the Wikipedia fetch (just looking at claims that DID get Wikipedia)

# Actually, let's just count how many claims have a Wikipedia-compatible subject
# by looking at which claims the pipeline tried to verify via Wikipedia

# Let's look at the hybrid_fallthrough.py - this is the NLI fallback for RELATIONAL
print("--- Does hybrid_fallthrough.py exist and what does it do? ---")
import hybrid_fallthrough as HF
print(dir(HF))

# Also check - the evaluate_master_corpus.py uses which pipeline?
print("\n--- How does evaluate_master_corpus route RELATIONAL? ---")

