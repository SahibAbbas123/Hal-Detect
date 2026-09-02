path = "thesis_latex/Chapter1/chapter1.tex"
with open(path, "r") as f: text = f.read()

old_str = r"""\item \textbf{Open Multi-LLM Road Test \& Empirical Validation:} A rigorous evaluation across 1,798 propositions from seven foundation models, proving HalDetect achieves \textbf{100.0\% recall on real hallucinations} (31/31 errors caught) where Modern SOTA RAG and MiniCheck-7B achieve 0.0\% recall ($p < 10^{-60}$)."""
new_str = r"""\item \textbf{Open Multi-LLM Road Test \& Empirical Validation:} A rigorous evaluation across 1,798 propositions from seven foundation models, proving HalDetect reliably isolates deterministic truth and exposes real-world hallucinations, where Modern SOTA RAG and MiniCheck-7B struggle with token overlap blindness."""

text = text.replace(old_str, new_str)
with open(path, "w") as f: f.write(text)
