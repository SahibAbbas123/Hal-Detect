# 🧠 Conceptual FAQs & Theoretical Academic Defense

This document provides rigorous, examiner-proof answers to the hardest theoretical and methodological questions regarding HalDetect.

---

### Q1: Why does SOTA RAG fail on numerical, temporal, and negation claims?
* **The Token Overlap Trap:** Dense embedding models (e.g. SBERT) and neural Cross-Encoders (e.g. DeBERTa-v3) compute cosine similarities and attention matrices across all tokens.
* When a claim is 95% identical to an evidence paragraph with only a corrupted number (*"3 Nobel Prizes"* instead of *"2 Nobel Prizes"*), the attention weights from the matching 95% of tokens overwhelm the single corrupted token, causing the neural judge to predict `TRUE` with high confidence.
* **HalDetect's Solution:** Symbolic extraction isolates the number `3` and compares it using deterministic arithmetic, catching the contradiction instantly.

---

### Q2: Why do massive frontier LLMs (GPT-4o, Gemma, MiniMax) hallucinate on temporal roles?
* **Parametric Memory Prior & Temporal Drift:**  
  Frontier LLMs understand grammar, but for long-tail entities (e.g. a prime minister, a CEO, or a regional sports captain who recently stepped down), the model has seen `(Entity, Active Role)` millions of times during pre-training.
* This creates a high prior probability in the model weights that causes the generative model to default to present-tense assertions (*"X is the captain"*).
* **HalDetect's Solution:** Enforces an absolute symbolic invariant checking structured timestamps and tenure end dates in real-time.

---

### Q3: What is the "Whack-a-Mole" Heuristic Ceiling, and how does HalDetect solve it?
* When trying to write regexes for open-ended English, language complexity causes combinatorial edge-case failures (e.g., compound names like *"John Cena and Roman Reigns"*, nicknames like *"Joe"* vs *"Joseph"*, or pronoun coreferences).
* **The Core Thesis Contribution:**  
  HalDetect demonstrates **Neuro-Symbolic Asymmetry**:
  * Use a **small neural LLM grammar / DSPy pipeline** for the fuzzy qualitative task: **Pronoun coreference & 5-tuple schema atomization**.
  * Use **deterministic symbolic ALUs & REST APIs** for the hard mathematical task: **Arithmetic, unit conversions, date bounds, and DOI lookups**.

---

### Q4: What is the difference between Closed-World and Open-World Assumptions in Fact-Checking?
* **Closed-World Fallacy (CWA):** Assuming that anything not explicitly written in a short summary is FALSE. (e.g., concluding that *"John Cena and Roman Reigns are enemies"* is a proven lie just because Wikipedia's summary doesn't mention their storyline feud).
* **Open-World Assumption (OWA):** If evidence is silent on an out-of-scope or unmentioned claim, the system must **safely abstain as `⚠️ UNVERIFIABLE`**.
* HalDetect enforces strict 3-valued logic, triggering `FALSE` only upon explicit contradictory proof.

---

### Q5: Is the 97.4% vs. 64.1% accuracy difference statistically significant?
* **Yes, overwhelmingly.** We conducted a formal **McNemar Paired Chi-Squared Test** on all 2,130 benchmark claims:
  $$\chi^2 = rac{(|698 - 17| - 1)^2}{698 + 17} = 646.71, \quad \mathbf{p < 10^{-100}} \ (p < 0.0001)$$
* The Wilson 95% Binomial Confidence Interval for HalDetect 2.0 is **$[96.7\%, 98.0\%]$** vs. **$[62.0\%, 66.1\%]$** for SOTA RAG. There is statistically zero chance this result is an artifact of sample noise.
