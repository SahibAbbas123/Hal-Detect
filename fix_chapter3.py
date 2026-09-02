import re

with open("thesis_latex/Chapter3/chapter3.tex", "r") as f:
    text = f.read()

# 1. Rename T_k to \Pi_k (the proposition tuple)
text = text.replace(r"\mathcal{T}_k = \langle", r"\Pi_k = \langle")
text = text.replace(r"proposition $\mathcal{T}_k$", r"proposition $\Pi_k$")
text = text.replace(r"\mathcal{M}(\mathcal{T}_k)", r"\mathcal{R}(\Pi_k)")
text = text.replace(r"\mathcal{T} = \langle S, P, O, T, M \rangle", r"\Pi = \langle S, P, O, T, M \rangle")
text = text.replace(r"\text{TaxonomyRouter}(\mathcal{T})", r"\text{TaxonomyRouter}(\Pi)")
text = text.replace(r"\text{VerifyQuantitative}(\mathcal{T}", r"\text{VerifyQuantitative}(\Pi")
text = text.replace(r"\text{VerifyTemporal}(\mathcal{T}", r"\text{VerifyTemporal}(\Pi")
text = text.replace(r"\text{VerifyEntityAttribute}(\mathcal{T}", r"\text{VerifyEntityAttribute}(\Pi")
text = text.replace(r"\text{VerifyCitation}(\mathcal{T}", r"\text{VerifyCitation}(\Pi")
text = text.replace(r"\text{VerifyRelational}(\mathcal{T}", r"\text{VerifyRelational}(\Pi")
text = text.replace(r"\mathcal{V}_1 \wedge \mathcal{V}_2 \wedge \dots \wedge \mathcal{V}_M", r"\mathcal{V}_1 \wedge \mathcal{V}_2 \wedge \dots \wedge \mathcal{V}_K")

# Fix ALUs
text = text.replace("Temporal ALU", "Temporal Verification Engine")
text = text.replace("Entity-Attribute ALU", "Entity-Attribute Verification Engine")
text = text.replace("Citation Registry ALU", "Citation Verification Engine")
text = text.replace("Relational ALU", "Relational Verification Engine")
text = text.replace("Citation ALU", "Citation Verification Engine")

# Add HalDetect 2.5 sentence
hd_sentence = r"The system described in this chapter, referred to as HalDetect~2.5 in the results tables, represents the final iteration of the pipeline incorporating all refinements documented in Appendix~I."
if "HalDetect~2.5" not in text:
    text = text.replace(r"This chapter formalizes the architecture of \textbf{HalDetect}, a type-directed neuro-symbolic fact verification engine.", hd_sentence + "\n\n" + r"This chapter formalizes the architecture of \textbf{HalDetect}, a type-directed neuro-symbolic fact verification engine.")

# Add Truth Table to Section 3.5
table_code = r"""
\begin{table}[h]
\centering
\caption{Complete three-valued (Kleene) conjunction truth table.}
\label{tab:kleene}
\begin{tabular}{l|ccc}
$\wedge_3$ & \texttt{TRUE} & \texttt{FALSE} & \texttt{UNVERIFIABLE} \\
\hline
\texttt{TRUE}         & \texttt{TRUE}  & \texttt{FALSE} & \texttt{UNVERIFIABLE} \\
\texttt{FALSE}        & \texttt{FALSE} & \texttt{FALSE} & \texttt{FALSE} \\
\texttt{UNVERIFIABLE} & \texttt{UNVERIFIABLE} & \texttt{FALSE} & \texttt{UNVERIFIABLE} \\
\end{tabular}
\end{table}

Abstention propagation: if any aspect abstains and none contradicts, the compound verdict is \texttt{UNVERIFIABLE}, propagating epistemic uncertainty conservatively.
"""
target_eq = r"\mathcal{V}_{\text{final}} = \mathcal{V}_1 \wedge \mathcal{V}_2 \wedge \dots \wedge \mathcal{V}_K"
# It's inside an equation block, let's insert after \end{equation} following this target
idx = text.find(target_eq)
if idx != -1:
    end_eq_idx = text.find(r"\end{equation}", idx)
    if end_eq_idx != -1 and "tab:kleene" not in text:
        insert_pos = end_eq_idx + len(r"\end{equation}")
        text = text[:insert_pos] + "\n\n" + table_code + text[insert_pos:]

with open("thesis_latex/Chapter3/chapter3.tex", "w") as f:
    f.write(text)
