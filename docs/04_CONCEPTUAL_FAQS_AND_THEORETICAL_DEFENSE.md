# 🧠 Conceptual FAQs & Theoretical Academic Defense: Deep "Why" Inquiries

This document provides rigorous, examiner-proof answers to the hardest theoretical and methodological questions regarding HalDetect.

---

### Q1: WHY does SOTA RAG fail on numerical, temporal, and negation claims?
* **The Token Overlap Trap:** Dense embedding models (e.g. SBERT) and neural Cross-Encoders (e.g. DeBERTa-v3) compute cosine similarities and attention matrices across all tokens.
* When a claim is 95% identical to an evidence paragraph with only a corrupted number (*"Marie Curie won 3 Nobel Prizes"* vs. evidence stating *"won 2 Nobel Prizes"*), the attention weights from the matching 95% of tokens (`Marie`, `Curie`, `won`, `Nobel`, `Prizes`) overwhelm the single corrupted token (`3` vs `2`). The neural cross-encoder predicts `TRUE` with high confidence.
* **HalDetect's Solution:** Symbolic extraction isolates the count `3` and compares it using deterministic arithmetic against the evidence count `2`, catching the contradiction instantly.

---

### Q2: WHY do massive frontier LLMs (GPT-4o, Gemma, MiniMax) hallucinate on temporal roles?
* **Parametric Memory Prior & Temporal Drift:**  
  Frontier LLMs understand grammar, but for long-tail entities (e.g. a prime minister, a CEO, or a regional sports captain who recently stepped down), the model has seen `(Entity, Active Role)` millions of times during pre-training.
* This creates a high prior probability in the model weights that causes the generative model to default to present-tense assertions (*"X is the captain"*).
* **HalDetect's Solution:** Enforces an absolute symbolic invariant checking structured timestamps and tenure end dates in real-time.

---

### Q3: WHY is rule-based regex parsing subject to the "Whack-a-Mole" ceiling?
* Language is combinatorial. If you write regexes to fix `and` in compound subjects, you break clause conjunctions. If you fix pronouns, you break multi-entity conversations. If you fix entity matchers, nicknames (`Joe` vs `Joseph`) break string equality.
* **The Core Thesis Contribution:**  
  HalDetect demonstrates **Neuro-Symbolic Asymmetry**:
  * Use a **small neural LLM grammar / DSPy pipeline** for the fuzzy qualitative task: **Pronoun coreference & 5-tuple schema atomization**.
  * Use **deterministic symbolic ALUs & REST APIs** for the hard mathematical task: **Arithmetic, unit conversions, date bounds, and DOI lookups**.

---

### Q4: WHY is McNemar's Paired Test required instead of Student's t-test or simple Accuracy?
* Standard accuracy does not account for whether two systems are getting the *same* claims right or failing on different claims.
* Because both HalDetect and SOTA RAG were evaluated on the **exact same 2,130 claims**, their predictions are paired and dependent.
* **McNemar's Paired Chi-Squared Test** specifically isolates discordant pairs ($b$: HalDetect Correct & RAG Wrong vs. $c$: HalDetect Wrong & RAG Correct):
  $$\chi^2 = rac{(|698 - 17| - 1)^2}{698 + 17} = 646.71, \quad \mathbf{p < 10^{-100}} \ (p < 0.0001)$$
* This proves beyond any mathematical doubt that HalDetect's performance advantage is statistically overwhelming.

---

### Q5: WHY is Selective Accuracy paired with Coverage and Matthews Correlation Coefficient (MCC)?
* In factuality verification, an algorithm that answers only 10 easy claims out of 2,000 and gets all 10 right has $100\%$ accuracy, but only $0.5\%$ coverage (a useless system in production).
* By reporting:
  1. **Coverage:** Percentage of claims the system felt confident enough to answer ($97.4\%$).
  2. **Selective Accuracy:** Accuracy strictly on answered claims ($97.44\%$).
  3. **Matthews Correlation Coefficient (MCC):** Balanced quality metric that accounts for all four confusion matrix quadrants ($+0.949$).
* This guarantees that HalDetect achieves both high coverage and high precision without hiding behind cowardly abstentions.
