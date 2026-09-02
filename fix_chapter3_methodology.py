path = "thesis_latex/Chapter3/chapter3.tex"
with open(path, "r") as f: text = f.read()

# Router False-Negative Bound Disclaimer
router_anchor = r"\mathcal{R}(\Pi_k) \in \{\text{Quantitative}, \text{Temporal}, \text{Entity-Attribute}, \text{Citation}, \text{Relational}\}"
router_disclaimer = r"""

Because HalDetect enforces a strict, mutually exclusive verification pipeline, the Taxonomy Router introduces a hard theoretical upper bound on total system recall. Any misclassification at this stage strictly truncates maximum recall. For example, if a \textit{Quantitative} claim is misrouted to a pipeline lacking dimensional analysis, or inappropriately dropped to \texttt{UNVERIFIABLE}, it generates a permanent false negative that cannot be recovered by downstream components."""
text = text.replace(router_anchor + "\n\\end{equation}", router_anchor + "\n\\end{equation}" + router_disclaimer)

# DAG Statistical Independence Disclaimer
dag_anchor = r"\mathcal{V}_{\text{final}} = \mathcal{V}_1 \wedge \mathcal{V}_2 \wedge \dots \wedge \mathcal{V}_K"
dag_disclaimer = r"""

It is critical to note that the verification micro-checks $\mathcal{V}_i$ are \textit{not} statistically independent. A failure in an upstream component (such as taxonomy routing) guarantees downstream verification failure. Furthermore, the parallel verification engines often suffer from correlated failure modes---such as joint entity disambiguation errors---which strictly violates naive assumptions of statistical independence across the DAG edges."""
text = text.replace(dag_anchor + "\n\\end{equation}", dag_anchor + "\n\\end{equation}" + dag_disclaimer)

with open(path, "w") as f: f.write(text)
