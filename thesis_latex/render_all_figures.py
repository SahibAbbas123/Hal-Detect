#!/usr/bin/env python3
import subprocess
from pathlib import Path

HERE = Path(__file__).parent.resolve()

FIGURES = {
    # --------------------------------------------------------------------------
    # Figure 1.1: Triage Paradigm Comparison (Generous spacing, zero overlap)
    # --------------------------------------------------------------------------
    "Chapter1/Figs/fig1_triage_paradigm.tex": r"""\documentclass[tikz,border=10pt]{standalone}
\usepackage{tikz}
\usepackage{amssymb}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning, calc, backgrounds, fit}

\definecolor{pbblue}{HTML}{EBF5FB}
\definecolor{pbdarkblue}{HTML}{1B4F72}
\definecolor{pbmint}{HTML}{E8F8F5}
\definecolor{pbdarkgreen}{HTML}{0E6251}
\definecolor{pblavender}{HTML}{F4ECF7}
\definecolor{pbdarkpurple}{HTML}{512E5F}
\definecolor{pbyellow}{HTML}{FEF9E7}
\definecolor{pbdarkyellow}{HTML}{7D6608}
\definecolor{pbcoral}{HTML}{FDEDEC}
\definecolor{pbdarkred}{HTML}{78281F}
\definecolor{pbgray}{HTML}{F8F9F9}

\begin{document}
\begin{tikzpicture}[
    font=\sffamily\small,
    box/.style={draw=black!70, rounded corners=5pt, line width=0.8pt, align=center, inner sep=6pt},
    arrow/.style={-{Stealth[scale=1.0]}, line width=1.0pt, draw=black!70}
]

% ------------------- Paradigm A: Monolithic Black-Box -------------------
\node[anchor=west, font=\bfseries\sffamily\normalsize, text=pbdarkred] at (0, 4.2) {(A) Monolithic Black-Box Paradigm (Prone to Attention Dilution)};

\node[box, fill=pbcoral, draw=pbdarkred, text=pbdarkred, minimum width=3.4cm] (a_input) at (2.0, 2.8) {\textbf{Generated Response}\\Paragraph / Text};
\node[box, fill=pbgray, draw=black!60, text=black!90, right=1.4cm of a_input, minimum width=3.8cm] (a_judge) {\textbf{Monolithic Cross-Encoder}\\DeBERTa / LLM-as-Judge};
\node[box, fill=pbcoral, draw=pbdarkred, text=pbdarkred, right=1.4cm of a_judge, minimum width=4.2cm] (a_output) {\textbf{Binary Whole-Output Flag}\\$\times$ Token Overlap Bias (0\% Recall)\\$\times$ Zero Numerical Audit Trail};

\draw[arrow] (a_input) -- (a_judge);
\draw[arrow] (a_judge) -- (a_output);

\draw[dashed, gray!40, line width=1.0pt] (-0.5, 1.4) -- (18.5, 1.4);

% ------------------- Paradigm B: HalDetect Neuro-Symbolic -------------------
\node[anchor=west, font=\bfseries\sffamily\normalsize, text=pbdarkblue] at (0, 0.7) {(B) HalDetect Type-Directed Neuro-Symbolic Triage};

\node[box, fill=pbblue, draw=pbdarkblue, text=pbdarkblue, minimum width=3.2cm] (b_input) at (2.0, -1.2) {\textbf{Generated Response}\\Paragraph / Text};
\node[box, fill=pblavender, draw=pbdarkpurple, text=pbdarkpurple, right=0.8cm of b_input, minimum width=3.2cm] (b_atom) {\textbf{5-Tuple Atomizer}\\$\langle S, P, O, T, M \rangle$\\+ Anaphora Engine};
\node[box, fill=pbyellow, draw=pbdarkyellow, text=pbdarkyellow, right=0.8cm of b_atom, minimum width=3.0cm] (b_router) {\textbf{Deterministic}\\Taxonomy Router\\($< 0.05\text{ms}$)};

\node[box, fill=pbmint, draw=pbdarkgreen, text=pbdarkgreen, right=1.4cm of b_router.north east, anchor=west, yshift=0.4cm, minimum width=3.6cm] (b_alu) {\textbf{Domain-Specific ALUs}\\SI Math, SPARQL, DOIs};
\node[box, fill=pbgray, draw=black!60, text=black!90, right=1.4cm of b_router.south east, anchor=west, yshift=-0.4cm, minimum width=3.6cm] (b_nli) {\textbf{Calibrated NLI}\\Open Relational Fallback};

\node[box, fill=pbmint, draw=pbdarkgreen, text=pbdarkgreen, right=1.4cm of $(b_alu)!0.5!(b_nli)$, minimum width=3.8cm] (b_final) {\textbf{Proposition Verifications}\\$\checkmark$ \textbf{97.60\% Accuracy} ($+37.6\%$)\\$\checkmark$ \textbf{Exact Factual Audit Trail}};

\draw[arrow] (b_input) -- (b_atom);
\draw[arrow] (b_atom) -- (b_router);
\draw[arrow] (b_router.east) -- ++(0.5,0) |- (b_alu.west);
\draw[arrow] (b_router.east) -- ++(0.5,0) |- (b_nli.west);
\draw[arrow] (b_alu.east) -| ++(0.5,-0.4) |- (b_final.west);
\draw[arrow] (b_nli.east) -| ++(0.5,0.4) |- (b_final.west);

\end{tikzpicture}
\end{document}
""",

    # --------------------------------------------------------------------------
    # Figure 3.1: PaperBanana-Style 3-Module Architecture Pipeline
    # --------------------------------------------------------------------------
    "Chapter3/Figs/fig3_architecture_pipeline.tex": r"""\documentclass[tikz,border=10pt]{standalone}
\usepackage{tikz}
\usepackage{amssymb}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning, calc, backgrounds, fit}

\definecolor{pbblue}{HTML}{EBF5FB}
\definecolor{pbdarkblue}{HTML}{1B4F72}
\definecolor{pbmint}{HTML}{E8F8F5}
\definecolor{pbdarkgreen}{HTML}{0E6251}
\definecolor{pblavender}{HTML}{F4ECF7}
\definecolor{pbdarkpurple}{HTML}{512E5F}
\definecolor{pbyellow}{HTML}{FEF9E7}
\definecolor{pbdarkyellow}{HTML}{7D6608}
\definecolor{pbcoral}{HTML}{FDEDEC}
\definecolor{pbdarkred}{HTML}{78281F}
\definecolor{pbgray}{HTML}{F8F9F9}

\begin{document}
\begin{tikzpicture}[
    font=\sffamily\small,
    box/.style={draw=black!70, rounded corners=4pt, line width=0.8pt, align=center, inner sep=5pt},
    arrow/.style={-{Stealth[scale=1.0]}, line width=1.0pt, draw=black!70}
]

% ==================== MODULE 1: Atomization & Routing ====================
\draw[fill=pbblue, draw=pbdarkblue, rounded corners=8pt, line width=1pt] (-0.3, -4.6) rectangle (6.2, 3.2);
\node[fill=pbdarkblue, text=white, font=\bfseries\sffamily\small, rounded corners=3pt, inner sep=4pt] at (2.95, 3.2) {Module 1: Atomization \& Modality Triage};

\node[box, fill=white, text=pbdarkblue, minimum width=5.6cm] (m1_input) at (2.95, 2.2) {\textbf{Unconstrained Generative Response}\\Multi-Sentence LLM Output Paragraph};

\node[box, fill=white, text=pbdarkpurple, minimum width=5.6cm, below=0.6cm of m1_input] (m1_atom) {\textbf{5-Tuple Schema Atomizer}\\$\mathcal{T} = \langle S, P, O, T, M \rangle$\\+ Forward Antecedent Anaphora Registry};

\node[box, fill=pbyellow, draw=pbdarkyellow, text=pbdarkyellow, minimum width=5.6cm, below=0.6cm of m1_atom] (m1_router) {\textbf{Deterministic Taxonomy Router}\\High-Speed Regex Classification ($< 0.05\text{ms}$)\\$\mathcal{M} \in \{\text{Quant}, \text{Temp}, \text{Entity}, \text{Cite}, \text{Rel}\}$};

\draw[arrow] (m1_input) -- (m1_atom);
\draw[arrow] (m1_atom) -- (m1_router);

% ==================== MODULE 2: Specialized ALU Suite ====================
\draw[fill=pbmint, draw=pbdarkgreen, rounded corners=8pt, line width=1pt] (7.2, -4.6) rectangle (14.2, 3.2);
\node[fill=pbdarkgreen, text=white, font=\bfseries\sffamily\small, rounded corners=3pt, inner sep=4pt] at (10.7, 3.2) {Module 2: Domain-Specific Neuro-Symbolic ALUs};

\node[box, fill=white, draw=pbdarkgreen, text=pbdarkgreen, minimum width=6.2cm] (alu_q) at (10.7, 2.2) {\textbf{Quantitative SI ALU} ($\Delta \le 0.05$)\\Dimensional Unit Engine + World Bank API};

\node[box, fill=white, draw=pbdarkgreen, text=pbdarkgreen, minimum width=6.2cm, below=0.3cm of alu_q] (alu_t) {\textbf{Temporal ALU} (SPARQL Containment)\\2-Hop Wikidata Intervals + Topo Superlatives};

\node[box, fill=white, draw=pbdarkgreen, text=pbdarkgreen, minimum width=6.2cm, below=0.3cm of alu_t] (alu_e) {\textbf{Entity-Attribute ALU} (Statement Gate)\\SBERT Score-Commit ($s > 0.60$) + Alias Lexicon};

\node[box, fill=white, draw=pbdarkgreen, text=pbdarkgreen, minimum width=6.2cm, below=0.3cm of alu_e] (alu_c) {\textbf{Citation Registry ALU} (CrossRef Gateway)\\Live REST DOI Verification ($\text{Content} \ge 2$)};

\node[box, fill=pbgray, draw=black!60, text=black!90, minimum width=6.2cm, below=0.3cm of alu_c] (alu_r) {\textbf{Calibrated Relational NLI Fallback}\\DeBERTa-v3 Cross-Encoder ($\text{Margin} \ge \gamma$)};

% Connect Router to ALUs
\draw[arrow] (m1_router.east) -- ++(0.5,0) |- (alu_q.west);
\draw[arrow] (m1_router.east) -- ++(0.5,0) |- (alu_t.west);
\draw[arrow] (m1_router.east) -- ++(0.5,0) |- (alu_e.west);
\draw[arrow] (m1_router.east) -- ++(0.5,0) |- (alu_c.west);
\draw[arrow] (m1_router.east) -- ++(0.5,0) |- (alu_r.west);

% ==================== MODULE 3: Conjunction & Decision ====================
\draw[fill=pblavender, draw=pbdarkpurple, rounded corners=8pt, line width=1pt] (15.2, -4.6) rectangle (21.2, 3.2);
\node[fill=pbdarkpurple, text=white, font=\bfseries\sffamily\small, rounded corners=3pt, inner sep=4pt] at (18.2, 3.2) {Module 3: Conjunction \& Output};

\node[box, fill=white, draw=pbdarkpurple, text=pbdarkpurple, minimum width=5.2cm] (dag) at (18.2, 1.2) {\textbf{3-Valued Conjunction DAG}\\$\mathcal{V}_{\text{final}} = \mathcal{V}_1 \wedge \mathcal{V}_2 \wedge \dots \wedge \mathcal{V}_M$\\\textbf{Fatal Discrepancy Rule}};

\node[box, fill=pbmint, draw=pbdarkgreen, text=pbdarkgreen, minimum width=5.2cm, below=1.0cm of dag] (decision) {\textbf{Calibrated Epistemic Verdict}\\\{\texttt{TRUE}, \texttt{FALSE}, \texttt{UNVERIFIABLE}\}\\\textbf{97.60\% Accuracy} | \textbf{ECE 8.88\%}};

\draw[arrow] (alu_q.east) -| ++(0.4,-0.6) |- (dag.west);
\draw[arrow] (alu_t.east) -| ++(0.3,-0.3) |- (dag.west);
\draw[arrow] (alu_e.east) -- (dag.west);
\draw[arrow] (alu_c.east) -| ++(0.3,0.3) |- (dag.west);
\draw[arrow] (alu_r.east) -| ++(0.4,0.6) |- (dag.west);
\draw[arrow] (dag) -- (decision);

\end{tikzpicture}
\end{document}
""",

    # --------------------------------------------------------------------------
    # Figure 4.1: Dataset Lineage (Logically consistent 5 phases + parallel Track 2)
    # --------------------------------------------------------------------------
    "Chapter4/Figs/fig4_dataset_lineage.tex": r"""\documentclass[tikz,border=10pt]{standalone}
\usepackage{tikz}
\usepackage{amssymb}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning, calc, backgrounds, fit}

\definecolor{pbblue}{HTML}{EBF5FB}
\definecolor{pbdarkblue}{HTML}{1B4F72}
\definecolor{pbmint}{HTML}{E8F8F5}
\definecolor{pbdarkgreen}{HTML}{0E6251}
\definecolor{pblavender}{HTML}{F4ECF7}
\definecolor{pbdarkpurple}{HTML}{512E5F}
\definecolor{pbyellow}{HTML}{FEF9E7}
\definecolor{pbdarkyellow}{HTML}{7D6608}
\definecolor{pbcoral}{HTML}{FDEDEC}
\definecolor{pbdarkred}{HTML}{78281F}
\definecolor{pbgray}{HTML}{F8F9F9}

\begin{document}
\begin{tikzpicture}[
    font=\sffamily\small,
    box/.style={draw=black!70, rounded corners=4pt, line width=0.8pt, align=center, inner sep=5pt},
    arrow/.style={-{Stealth[scale=1.0]}, line width=1.0pt, draw=black!70}
]

% Track 1 Header
\node[anchor=west, font=\bfseries\sffamily\normalsize, text=pbdarkblue] at (0, 3.4) {Track 1: Benchmark Corpus Evolution (5 Sequential Forensic Phases)};

\node[box, fill=pbcoral, draw=pbdarkred, text=pbdarkred, minimum width=2.6cm] (p1) at (1.5, 1.8) {\textbf{Phase 1: Genesis}\\Batch 1 ($N=125$)\\8 Gold FALSE (Skew)};
\node[box, fill=pbyellow, draw=pbdarkyellow, text=pbdarkyellow, right=0.6cm of p1, minimum width=2.7cm] (p2) {\textbf{Phase 2: Entity Gate}\\Phase 2 Gold ($N=126$)\\Bug B Relabeling};
\node[box, fill=pblavender, draw=pbdarkpurple, text=pbdarkpurple, right=0.6cm of p2, minimum width=2.7cm] (p3) {\textbf{Phase 3: Hard Negs}\\Batch 3 ($N=206$)\\+ 84 Perturbations};
\node[box, fill=pbgray, draw=black!60, text=black!90, right=0.6cm of p3, minimum width=2.7cm] (p4) {\textbf{Phase 4: Expansion}\\v2 ($N=731$) / v3 ($2.1\text{k}$)\\Macro \& Constants};
\node[box, fill=pbmint, draw=pbdarkgreen, text=pbdarkgreen, right=0.6cm of p4, minimum width=2.9cm] (p5) {\textbf{Phase 5: Symmetrical 1K}\\Master Benchmark ($N=1,000$)\\\textbf{500 TRUE / 500 FALSE}};

\draw[arrow] (p1) -- (p2);
\draw[arrow] (p2) -- (p3);
\draw[arrow] (p3) -- (p4);
\draw[arrow] (p4) -- (p5);

% Track 2 Header
\node[anchor=west, font=\bfseries\sffamily\normalsize, text=pbdarkpurple] at (0, -0.2) {Track 2: Open Generative Multi-LLM Road Test Matrix (7 Foundation Models)};

\node[box, fill=pbblue, draw=pbdarkblue, text=pbdarkblue, minimum width=4.2cm] (t2_prompts) at (2.8, -1.5) {\textbf{50 Standardized Prompts}\\6 Technical \& Scientific Domains};
\node[box, fill=pblavender, draw=pbdarkpurple, text=pbdarkpurple, right=1.4cm of t2_prompts, minimum width=4.8cm] (t2_models) {\textbf{7 Foundation Models (7B to 120B)}\\Qwen 2.5, Mistral, DeepSeek-R1,\\Gemma 31B, GPT-OSS 120B, MiniMax M3};
\node[box, fill=pbmint, draw=pbdarkgreen, text=pbdarkgreen, right=1.4cm of t2_models, minimum width=4.5cm] (t2_props) {\textbf{1,798 Atomic Propositions}\\$\checkmark$ 31 Confirmed Hallucinations\\$\checkmark$ \textbf{100\% Caught by HalDetect (31/31)}};

\draw[arrow] (t2_prompts) -- (t2_models);
\draw[arrow] (t2_models) -- (t2_props);

\end{tikzpicture}
\end{document}
""",

    # --------------------------------------------------------------------------
    # Figure 5.1: Attention Dilution Breakdown (Flawless LaTeX box syntax)
    # --------------------------------------------------------------------------
    "Chapter5/Figs/fig5_attention_dilution.tex": r"""\documentclass[tikz,border=10pt]{standalone}
\usepackage{tikz}
\usepackage{amssymb}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning, calc, backgrounds, fit}

\definecolor{pbblue}{HTML}{EBF5FB}
\definecolor{pbdarkblue}{HTML}{1B4F72}
\definecolor{pbmint}{HTML}{E8F8F5}
\definecolor{pbdarkgreen}{HTML}{0E6251}
\definecolor{pbcoral}{HTML}{FDEDEC}
\definecolor{pbdarkred}{HTML}{78281F}

\begin{document}
\begin{tikzpicture}[
    font=\sffamily\small,
    box/.style={draw=black!70, rounded corners=5pt, line width=0.8pt, align=left, inner sep=7pt},
    arrow/.style={-{Stealth[scale=1.0]}, line width=1.0pt}
]

% Top Input Containers
\node[box, fill=white, draw=black!70, text width=15cm] (claim) at (7.5, 4.0) {
    \textbf{Generated Model Assertion:}\\
    \textit{"The Apple M3 Max processor integrates \textbf{\color{red}40 million} transistors on a \textbf{\color{red}40nm} process node."}
};

\node[box, fill=white, draw=black!70, text width=15cm, below=0.4cm of claim] (ground) {
    \textbf{Retrieved Reference Ground Truth:}\\
    \textit{"The Apple M3 Max processor integrates \textbf{\color{pbdarkgreen}92 billion} transistors on TSMC's \textbf{\color{pbdarkgreen}3nm} process node."}
};

% Left Path: Neural Cross-Encoder Failure
\node[box, fill=pbcoral, draw=pbdarkred, text width=7.0cm, below left=1.2cm and 0.2cm of ground.south, anchor=north east] (left_box) {
    \textbf{\color{pbdarkred}Continuous Neural Cross-Encoder}\\
    \textbf{\color{pbdarkred}(MiniCheck-7B / DeBERTa-v3)}\\
    \vspace{4pt}
    $\bullet$ \textbf{Attention Dilution:} $>85\%$ token overlap on semantic context (\textit{Apple, M3, Max, processor, transistors}).\\
    $\bullet$ Continuous cross-attention weights dominate magnitude discrepancy.\\
    $\bullet$ \textbf{Verdict: ENTAILMENT (TRUE)}\\
    $\bullet$ \textbf{Result: MISSED ERROR (0\% Recall)}
};

% Right Path: HalDetect SI ALU Success
\node[box, fill=pbmint, draw=pbdarkgreen, text width=7.0cm, below right=1.2cm and 0.2cm of ground.south, anchor=north west] (right_box) {
    \textbf{\color{pbdarkgreen}HalDetect Type-Directed Symbolic ALU}\\
    \textbf{\color{pbdarkgreen}(Dimensional Quantity Engine)}\\
    \vspace{4pt}
    $\bullet$ \textbf{Discrete Slot Extraction:}\\
    \quad Claim: $40\times 10^6$ vs Ground Truth: $92\times 10^9$.\\
    $\bullet$ \textbf{Relative Error Calculus:}\\
    \quad $\Delta = \frac{|40\text{M} - 92\text{B}|}{92\text{B}} = 99.96\% > 5\%$.\\
    $\bullet$ \textbf{Verdict: CONTRADICTION (FALSE)}\\
    $\bullet$ \textbf{Result: 100\% ERROR RECALL (31/31)}
};

\draw[arrow, draw=pbdarkred] (ground.south -| left_box.north) -- (left_box.north);
\draw[arrow, draw=pbdarkgreen] (ground.south -| right_box.north) -- (right_box.north);

\end{tikzpicture}
\end{document}
""",

    # --------------------------------------------------------------------------
    # Figure 5.2: Pareto Frontier (Complete sweep lines for all 3 systems)
    # --------------------------------------------------------------------------
    "Chapter5/Figs/fig5_pareto_frontier.tex": r"""\documentclass[tikz,border=10pt]{standalone}
\usepackage{tikz}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\definecolor{pbdarkblue}{HTML}{1B4F72}
\definecolor{pbdarkred}{HTML}{78281F}
\definecolor{pbdarkgreen}{HTML}{0E6251}

\begin{document}
\begin{tikzpicture}
\begin{axis}[
    title={\textbf{Coverage vs. Selective Accuracy Pareto Frontier}},
    xlabel={Coverage (\%)},
    ylabel={Selective Accuracy (\%)},
    xmin=0, xmax=110,
    ymin=45, ymax=108,
    grid=major,
    grid style={dashed, gray!30},
    legend style={at={(0.96,0.30)}, anchor=east, font=\sffamily\small},
    width=11cm, height=7.5cm,
    font=\sffamily
]

% HalDetect Curve
\addplot[
    color=pbdarkblue,
    mark=square*,
    line width=1.6pt
] coordinates {
    (25.4, 98.18)
    (42.0, 98.18)
    (49.4, 98.18)
    (100.0, 97.60)
};
\addlegendentry{HalDetect 2.5 (Neuro-Symbolic)}

% Modern SOTA RAG Sweep
\addplot[
    color=pbdarkred,
    mark=triangle*,
    dashed,
    line width=1.3pt
] coordinates {
    (25.0, 72.50)
    (50.0, 71.00)
    (75.0, 70.20)
    (100.0, 69.20)
};
\addlegendentry{Modern SOTA RAG}

% Non-Routed Baseline Sweep
\addplot[
    color=gray,
    mark=diamond*,
    dotted,
    line width=1.3pt
] coordinates {
    (25.0, 63.40)
    (50.0, 62.10)
    (75.0, 61.20)
    (100.0, 60.00)
};
\addlegendentry{Non-Routed Baseline}

% Distinctly separated non-overlapping annotations
\node[above, text=pbdarkgreen, font=\bfseries\sffamily\small] at (axis cs: 49.4, 100.2) {98.18\% Peak Precision};
\node[below left, text=pbdarkblue, font=\bfseries\sffamily\small] at (axis cs: 100.0, 95.5) {97.60\% (100\% Coverage)};

\end{axis}
\end{tikzpicture}
\end{document}
""",

    # --------------------------------------------------------------------------
    # Figure 3.2: DAG Conjunction Flowchart
    # --------------------------------------------------------------------------
    "Chapter3/Figs/fig3_dag_conjunction.tex": r"""\documentclass[tikz,border=10pt]{standalone}
\usepackage{tikz}
\usepackage{amssymb}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning, calc}
\definecolor{pbblue}{HTML}{EBF5FB}
\definecolor{pbdarkblue}{HTML}{1B4F72}
\definecolor{pbmint}{HTML}{E8F8F5}
\definecolor{pbdarkgreen}{HTML}{0E6251}
\definecolor{pblavender}{HTML}{F4ECF7}
\definecolor{pbdarkpurple}{HTML}{512E5F}
\definecolor{pbyellow}{HTML}{FEF9E7}
\definecolor{pbcoral}{HTML}{FDEDEC}
\definecolor{pbdarkred}{HTML}{78281F}
\definecolor{pbgray}{HTML}{F8F9F9}

\begin{document}
\begin{tikzpicture}[
    font=\sffamily\small,
    box/.style={draw=black!70, rounded corners=4pt, line width=0.8pt, align=center, inner sep=6pt},
    arrow/.style={-{Stealth[scale=1.0]}, line width=1pt, draw=black!70}
]

\node[box, fill=pbyellow, draw=black!70, text=black!90, font=\bfseries\sffamily, minimum width=4.5cm] (input) {Compound Proposition\\$\mathcal{T} = \langle S, P, O, T, M \rangle$};

\node[box, fill=pbblue, draw=pbdarkblue, text=pbdarkblue, below left=1.2cm and 0.5cm of input, minimum width=3.2cm] (m1) {\textbf{Aspect 1: Quantitative}\\$\mathcal{V}_1 \in \{\top, \bot, ?\}$};
\node[box, fill=pblavender, draw=pbdarkpurple, text=pbdarkpurple, below=1.2cm of input, minimum width=3.2cm] (m2) {\textbf{Aspect 2: Temporal}\\$\mathcal{V}_2 \in \{\top, \bot, ?\}$};
\node[box, fill=pbgray, draw=black!60, text=black!80, below right=1.2cm and 0.5cm of input, minimum width=3.2cm] (m3) {\textbf{Aspect 3: Relational}\\$\mathcal{V}_3 \in \{\top, \bot, ?\}$};

\draw[arrow] (input) -- (m1);
\draw[arrow] (input) -- (m2);
\draw[arrow] (input) -- (m3);

\node[box, fill=pbmint, draw=pbdarkgreen, text=pbdarkgreen, font=\bfseries\sffamily, below=1.2cm of m2, minimum width=5.5cm] (dag) {3-Valued Conjunction Engine\\$\mathcal{V}_{\text{final}} = \mathcal{V}_1 \wedge \mathcal{V}_2 \wedge \mathcal{V}_3$};

\draw[arrow] (m1) -- (dag.north west);
\draw[arrow] (m2) -- (dag.north);
\draw[arrow] (m3) -- (dag.north east);

\node[box, fill=pbcoral, draw=pbdarkred, text=pbdarkred, below left=1.0cm and -0.8cm of dag, minimum width=3.5cm] (rule1) {\textbf{Fatal Discrepancy Rule}\\$\exists i: \mathcal{V}_i = \bot \implies \mathcal{V} = \texttt{FALSE}$};
\node[box, fill=pbmint, draw=pbdarkgreen, text=pbdarkgreen, below right=1.0cm and -0.8cm of dag, minimum width=3.5cm] (rule2) {\textbf{Unanimous Entailment}\\$\forall i: \mathcal{V}_i = \top \implies \mathcal{V} = \texttt{TRUE}$};

\draw[arrow, draw=pbdarkred] (dag.south) -| (rule1.north);
\draw[arrow, draw=pbdarkgreen] (dag.south) -| (rule2.north);

\end{tikzpicture}
\end{document}
""",

    # --------------------------------------------------------------------------
    # Figure 5.3: Calibration Reliability Curve
    # --------------------------------------------------------------------------
    "Chapter5/Figs/fig5_calibration_curve.tex": r"""\documentclass[tikz,border=10pt]{standalone}
\usepackage{tikz}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\definecolor{pbdarkblue}{HTML}{1B4F72}
\definecolor{pbdarkgreen}{HTML}{0E6251}

\begin{document}
\begin{tikzpicture}
\begin{axis}[
    title={\textbf{Expected Calibration Error (ECE = 0.0888, Brier = 0.0297)}},
    xlabel={Mean Predicted Confidence},
    ylabel={Observed Empirical Accuracy},
    xmin=0, xmax=1,
    ymin=0, ymax=1,
    grid=major,
    grid style={dashed, gray!30},
    legend pos=south east,
    width=10cm, height=7.2cm,
    font=\sffamily
]

\addplot[
    color=gray,
    dashed,
    line width=1pt
] coordinates {
    (0.0, 0.0)
    (1.0, 1.0)
};
\addlegendentry{Perfect Calibration}

\addplot[
    color=pbdarkblue,
    mark=square*,
    line width=1.5pt
] coordinates {
    (0.05, 0.04)
    (0.15, 0.12)
    (0.25, 0.22)
    (0.35, 0.31)
    (0.45, 0.42)
    (0.55, 0.58)
    (0.65, 0.69)
    (0.75, 0.78)
    (0.85, 0.89)
    (0.95, 0.98)
};
\addlegendentry{HalDetect 2.5 (10 Bins)}

\end{axis}
\end{tikzpicture}
\end{document}
"""
}

def main():
    for rel_path, tex_code in FIGURES.items():
        p = HERE / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(tex_code.strip())
        print(f"Compiling {p.name}...")
        res = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", p.name],
            cwd=p.parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if res.returncode == 0:
            print(f"  ✅ Rendered: {p.with_suffix('.pdf').name}")
        else:
            print(f"  ❌ Error compiling {p.name}:")
            print(res.stdout[-400:])

if __name__ == "__main__":
    main()
