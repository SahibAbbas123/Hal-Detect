#!/usr/bin/env python3
import subprocess
from pathlib import Path

HERE = Path(__file__).parent.resolve()

FIGURES = {
    # --------------------------------------------------------------------------
    # Figure 1.1: Triage Paradigm Comparison (Clean spacing, zero overlap)
    # --------------------------------------------------------------------------
    "Chapter1/Figs/fig1_triage_paradigm.tex": r"""\documentclass[tikz,border=8pt]{standalone}
\usepackage{tikz}
\usepackage{amssymb}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning, calc, backgrounds, fit}

\definecolor{pbblue}{HTML}{E6F3FF}
\definecolor{pbdarkblue}{HTML}{1E3A8A}
\definecolor{pbmint}{HTML}{E0F2F1}
\definecolor{pbdarkgreen}{HTML}{065F46}
\definecolor{pblavender}{HTML}{F3E5F5}
\definecolor{pbdarkpurple}{HTML}{581C87}
\definecolor{pbyellow}{HTML}{FEF3C7}
\definecolor{pbdarkyellow}{HTML}{92400E}
\definecolor{pbcoral}{HTML}{FEE2E2}
\definecolor{pbdarkred}{HTML}{991B1B}
\definecolor{pbgray}{HTML}{F3F4F6}

\begin{document}
\begin{tikzpicture}[
    font=\sffamily\small,
    box/.style={draw=black!60, rounded corners=5pt, line width=0.8pt, align=center, inner sep=6pt},
    arrow/.style={-{Stealth[scale=1.0]}, line width=1.0pt, draw=black!70}
]

% ------------------- Paradigm A: Monolithic Black-Box -------------------
\node[anchor=west, font=\bfseries\sffamily\small, text=pbdarkred] at (0, 3.8) {(A) Monolithic Black-Box Fact-Checkers (Subject to Attention Dilution)};

\node[box, fill=pbcoral!60, text=pbdarkred, minimum width=3.2cm] (a_input) at (1.8, 2.6) {\textbf{Generated Response}\\Paragraph / Text};
\node[box, fill=pbgray, text=black!85, right=1.2cm of a_input, minimum width=3.4cm] (a_judge) {\textbf{Monolithic Cross-Encoder}\\DeBERTa / LLM-as-Judge};
\node[box, fill=pbcoral!80, text=pbdarkred, right=1.2cm of a_judge, minimum width=3.8cm] (a_output) {\textbf{Whole-Output Binary Flag}\\$\times$ Token Overlap Bias\\$\times$ Zero Numerical Audit};

\draw[arrow] (a_input) -- (a_judge);
\draw[arrow] (a_judge) -- (a_output);

\draw[dashed, gray!50, line width=0.8pt] (-0.2, 1.4) -- (15.5, 1.4);

% ------------------- Paradigm B: HalDetect Neuro-Symbolic -------------------
\node[anchor=west, font=\bfseries\sffamily\small, text=pbdarkblue] at (0, 0.9) {(B) HalDetect: Type-Directed Neuro-Symbolic Modality Triage};

\node[box, fill=pbblue!60, text=pbdarkblue, minimum width=3.0cm] (b_input) at (1.8, -0.8) {\textbf{Generated Response}\\Paragraph / Text};
\node[box, fill=pblavender!70, text=pbdarkpurple, right=0.8cm of b_input, minimum width=3.0cm] (b_atom) {\textbf{5-Tuple Atomizer}\\+ Forward Anaphora};
\node[box, fill=pbyellow!80, text=pbdarkyellow, right=0.8cm of b_atom, minimum width=2.8cm] (b_router) {\textbf{Deterministic}\\Taxonomy Router};

\node[box, fill=pbmint!80, text=pbdarkgreen, right=1.2cm of b_router.north east, anchor=west, yshift=0.3cm, minimum width=3.0cm] (b_alu) {\textbf{Symbolic ALUs}\\SI Math, SPARQL, DOIs};
\node[box, fill=pbblue!50, text=pbdarkblue, right=1.2cm of b_router.south east, anchor=west, yshift=-0.3cm, minimum width=3.0cm] (b_nli) {\textbf{Calibrated NLI}\\Open Relational Fallback};

\node[box, fill=pbmint, draw=pbdarkgreen, text=pbdarkgreen, right=1.0cm of $(b_alu)!0.5!(b_nli)$, minimum width=3.2cm] (b_final) {\textbf{3-Valued Verdicts}\\$\checkmark$ 97.60\% Accuracy\\$\checkmark$ Exact Factual Audit};

\draw[arrow] (b_input) -- (b_atom);
\draw[arrow] (b_atom) -- (b_router);
\draw[arrow] (b_router.east) -- ++(0.5,0) |- (b_alu.west);
\draw[arrow] (b_router.east) -- ++(0.5,0) |- (b_nli.west);
\draw[arrow] (b_alu.east) -| ++(0.4,-0.4) |- (b_final.west);
\draw[arrow] (b_nli.east) -| ++(0.4,0.4) |- (b_final.west);

\end{tikzpicture}
\end{document}
""",

    # --------------------------------------------------------------------------
    # Figure 3.1: Architecture Pipeline (Expanded vertical clearance, no text collision)
    # --------------------------------------------------------------------------
    "Chapter3/Figs/fig3_architecture_pipeline.tex": r"""\documentclass[tikz,border=8pt]{standalone}
\usepackage{tikz}
\usepackage{amssymb}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning, calc, backgrounds, fit}

\definecolor{pbblue}{HTML}{E6F3FF}
\definecolor{pbdarkblue}{HTML}{1E3A8A}
\definecolor{pbmint}{HTML}{E0F2F1}
\definecolor{pbdarkgreen}{HTML}{065F46}
\definecolor{pblavender}{HTML}{F3E5F5}
\definecolor{pbdarkpurple}{HTML}{581C87}
\definecolor{pbyellow}{HTML}{FEF3C7}
\definecolor{pbdarkyellow}{HTML}{92400E}
\definecolor{pbcoral}{HTML}{FEE2E2}
\definecolor{pbdarkred}{HTML}{991B1B}
\definecolor{pbgray}{HTML}{F3F4F6}

\begin{document}
\begin{tikzpicture}[
    font=\sffamily\small,
    box/.style={draw=black!60, rounded corners=4pt, line width=0.8pt, align=center, inner sep=5pt},
    arrow/.style={-{Stealth[scale=0.9]}, line width=0.9pt, draw=black!70}
]

% Input & Atomization
\node[box, fill=pbblue!60, text=pbdarkblue, minimum width=2.4cm] (input) at (0, 0) {\textbf{Unconstrained}\\Generated Text};
\node[box, fill=pblavender!70, text=pbdarkpurple, right=0.8cm of input, minimum width=2.8cm] (atom) {\textbf{5-Tuple Atomizer}\\$\langle S, P, O, T, M \rangle$\\+ Anaphora Engine};
\node[box, fill=pbyellow!80, text=pbdarkyellow, right=0.8cm of atom, minimum width=2.6cm] (router) {\textbf{Deterministic}\\Taxonomy Router\\($< 0.05\text{ms}$)};

\draw[arrow] (input) -- (atom);
\draw[arrow] (atom) -- (router);

% 5 Specialized ALUs (Spaced vertically by 1.1cm)
\node[box, fill=pbmint!80, text=pbdarkgreen, right=1.2cm of router, yshift=2.4cm, minimum width=4.0cm] (alu1) {\textbf{Quantitative SI ALU}\\Dimensional Base ($\Delta \le \tau_{\text{rel}}$) + World Bank};
\node[box, fill=pbmint!80, text=pbdarkgreen, below=0.35cm of alu1, minimum width=4.0cm] (alu2) {\textbf{Temporal ALU}\\2-Hop SPARQL + 7-Continent Resolver};
\node[box, fill=pbmint!80, text=pbdarkgreen, below=0.35cm of alu2, minimum width=4.0cm] (alu3) {\textbf{Entity-Attribute ALU}\\Score-Commit Gate ($s > 0.60$)};
\node[box, fill=pbmint!80, text=pbdarkgreen, below=0.35cm of alu3, minimum width=4.0cm] (alu4) {\textbf{Citation ALU}\\CrossRef Live REST API Gateway};
\node[box, fill=pbgray, text=black!85, below=0.35cm of alu4, minimum width=4.0cm] (alu5) {\textbf{Relational NLI Fallback}\\Calibrated DeBERTa-v3 ($\text{Margin} \ge \gamma$)};

\draw[arrow] (router.east) -- ++(0.4,0) |- (alu1.west);
\draw[arrow] (router.east) -- ++(0.4,0) |- (alu2.west);
\draw[arrow] (router.east) -- ++(0.4,0) |- (alu3.west);
\draw[arrow] (router.east) -- ++(0.4,0) |- (alu4.west);
\draw[arrow] (router.east) -- ++(0.4,0) |- (alu5.west);

% DAG Conjunction & Output
\node[box, fill=pblavender!90, text=pbdarkpurple, right=1.2cm of alu3, minimum width=2.8cm] (dag) {\textbf{Multi-Aspect DAG}\\Conjunction Engine\\$\mathcal{V}_{\text{final}} = \bigwedge \mathcal{V}_i$};
\node[box, fill=pbmint, draw=pbdarkgreen, text=pbdarkgreen, right=0.8cm of dag, minimum width=2.6cm] (output) {\textbf{3-Valued Output}\\\{\texttt{TRUE}, \texttt{FALSE}, \texttt{UNV}\}};

\draw[arrow] (alu1.east) -| ++(0.4,-0.4) |- (dag.west);
\draw[arrow] (alu2.east) -| ++(0.3,-0.2) |- (dag.west);
\draw[arrow] (alu3.east) -- (dag.west);
\draw[arrow] (alu4.east) -| ++(0.3,0.2) |- (dag.west);
\draw[arrow] (alu5.east) -| ++(0.4,0.4) |- (dag.west);
\draw[arrow] (dag) -- (output);

\end{tikzpicture}
\end{document}
""",

    # --------------------------------------------------------------------------
    # Figure 4.1: Dataset Lineage (Logically consistent 5 phases + parallel Track 2)
    # --------------------------------------------------------------------------
    "Chapter4/Figs/fig4_dataset_lineage.tex": r"""\documentclass[tikz,border=8pt]{standalone}
\usepackage{tikz}
\usepackage{amssymb}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning, calc, backgrounds, fit}

\definecolor{pbblue}{HTML}{E6F3FF}
\definecolor{pbdarkblue}{HTML}{1E3A8A}
\definecolor{pbmint}{HTML}{E0F2F1}
\definecolor{pbdarkgreen}{HTML}{065F46}
\definecolor{pblavender}{HTML}{F3E5F5}
\definecolor{pbdarkpurple}{HTML}{581C87}
\definecolor{pbyellow}{HTML}{FEF3C7}
\definecolor{pbdarkyellow}{HTML}{92400E}
\definecolor{pbcoral}{HTML}{FEE2E2}
\definecolor{pbdarkred}{HTML}{991B1B}
\definecolor{pbgray}{HTML}{F3F4F6}

\begin{document}
\begin{tikzpicture}[
    font=\sffamily\small,
    box/.style={draw=black!60, rounded corners=4pt, line width=0.8pt, align=center, inner sep=5pt},
    arrow/.style={-{Stealth[scale=0.9]}, line width=1.0pt, draw=black!70}
]

% ------------------- Track 1: 5-Phase Master Benchmark Evolution -------------------
\node[anchor=west, font=\bfseries\sffamily\small, text=pbdarkblue] at (0, 3.2) {Track 1: Master Benchmark Evolution (5 Chronological Phases)};

\node[box, fill=pbcoral!60, text=pbdarkred, minimum width=2.4cm] (p1) at (1.3, 1.8) {\textbf{Phase 1: Genesis}\\Batch 1 ($N=125$)\\8 Gold FALSE (Skew)};
\node[box, fill=pbyellow!70, text=pbdarkyellow, right=0.5cm of p1, minimum width=2.5cm] (p2) {\textbf{Phase 2: Entity Gate}\\Phase 2 Gold ($N=126$)\\Bug B Relabeling};
\node[box, fill=pblavender!70, text=pbdarkpurple, right=0.5cm of p2, minimum width=2.5cm] (p3) {\textbf{Phase 3: Hard Negs}\\Batch 3 ($N=206$)\\+ 84 Perturbations};
\node[box, fill=pbgray, text=black!85, right=0.5cm of p3, minimum width=2.5cm] (p4) {\textbf{Phase 4: Expansion}\\v2 ($N=731$) / v3 ($N=2.1\text{k}$)\\Macro \& Constants};
\node[box, fill=pbmint, draw=pbdarkgreen, text=pbdarkgreen, right=0.5cm of p4, minimum width=2.6cm] (p5) {\textbf{Phase 5: Symmetrical 1K}\\Master Benchmark ($N=1,000$)\\\textbf{500 TRUE / 500 FALSE}};

\draw[arrow] (p1) -- (p2);
\draw[arrow] (p2) -- (p3);
\draw[arrow] (p3) -- (p4);
\draw[arrow] (p4) -- (p5);

% ------------------- Track 2: Open Generative Road Test -------------------
\node[anchor=west, font=\bfseries\sffamily\small, text=pbdarkpurple] at (0, -0.1) {Track 2: Multi-LLM Generative Road Test (7 Foundation Models)};

\node[box, fill=pbblue!60, text=pbdarkblue, minimum width=3.6cm] (t2_prompts) at (2.5, -1.2) {\textbf{50 Standardized Prompts}\\6 Technical / Scientific Domains};
\node[box, fill=pblavender!80, text=pbdarkpurple, right=1.2cm of t2_prompts, minimum width=4.2cm] (t2_models) {\textbf{7 Foundation Models (7B to 120B)}\\Qwen, Mistral, DeepSeek-R1,\\Gemma 31B, GPT-OSS 120B, MiniMax};
\node[box, fill=pbmint!80, text=pbdarkgreen, right=1.2cm of t2_models, minimum width=3.8cm] (t2_props) {\textbf{1,798 Atomic Propositions}\\$\checkmark$ 31 Confirmed Hallucinations\\$\checkmark$ \textbf{100\% Caught by HalDetect}};

\draw[arrow] (t2_prompts) -- (t2_models);
\draw[arrow] (t2_models) -- (t2_props);

\end{tikzpicture}
\end{document}
""",

    # --------------------------------------------------------------------------
    # Figure 5.1: Attention Dilution Breakdown (Redesigned with publication aesthetics)
    # --------------------------------------------------------------------------
    "Chapter5/Figs/fig5_attention_dilution.tex": r"""\documentclass[tikz,border=8pt]{standalone}
\usepackage{tikz}
\usepackage{amssymb}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning, calc, backgrounds, fit}

\definecolor{pbblue}{HTML}{E6F3FF}
\definecolor{pbdarkblue}{HTML}{1E3A8A}
\definecolor{pbmint}{HTML}{E0F2F1}
\definecolor{pbdarkgreen}{HTML}{065F46}
\definecolor{pbcoral}{HTML}{FEE2E2}
\definecolor{pbdarkred}{HTML}{991B1B}
\definecolor{pbgray}{HTML}{F3F4F6}

\begin{document}
\begin{tikzpicture}[
    font=\sffamily\small,
    box/.style={draw=black!60, rounded corners=4pt, line width=0.8pt, align=center, inner sep=6pt},
    arrow/.style={-{Stealth[scale=0.9]}, line width=1.0pt, draw=black!70}
]

% Top Input Containers
\node[box, fill=white, draw=black!70, minimum width=13cm] (claim) at (6.5, 3.6) {
    \textbf{Generated Model Claim:} \textit{"The Apple M3 Max is manufactured on a \textbf{\color{red}40nm} process with \textbf{\color{red}40 million} transistors."}
};
\node[box, fill=white, draw=black!70, minimum width=13cm, below=0.3cm of claim] (ground) {
    \textbf{Retrieved Ground Truth:} \textit{"The Apple M3 Max is manufactured on TSMC's \textbf{\color{pbdarkgreen}3nm} process with \textbf{\color{pbdarkgreen}92 billion} transistors."}
};

% Left Path: Neural Cross-Encoder Failure
\node[box, fill=pbcoral!60, draw=pbdarkred, text=pbdarkred, below left=1.2cm and -0.2cm of ground.south, anchor=north east, minimum width=6.2cm] (left_box) {
    \textbf{Continuous Neural Cross-Encoder (MiniCheck / DeBERTa)}\\
    \vspace{2pt}
    \begin{itemize}
        \setlength{\itemsep}{1pt}
        \item \textbf{Attention Dilution:} 85\% token overlap on context\\(\textit{Apple, M3, Max, process, transistors}).
        \item Continuous cross-attention assigns high softmax mass.
        \item Output: \textbf{ENTAILMENT (TRUE)} $\implies$ \textbf{MISSED ERROR (0\% Recall)}
    \end{itemize}
};

% Right Path: HalDetect SI ALU Success
\node[box, fill=pbmint!70, draw=pbdarkgreen, text=pbdarkgreen, below right=1.2cm and -0.2cm of ground.south, anchor=north west, minimum width=6.2cm] (right_box) {
    \textbf{HalDetect Type-Directed Symbolic SI ALU}\\
    \vspace{2pt}
    \begin{itemize}
        \setlength{\itemsep}{1pt}
        \item \textbf{Discrete Slot Isolation:} Claim = $40\times 10^6$, Truth = $92\times 10^9$.
        \item Relative Discrepancy: $\Delta = \frac{|40\text{M} - 92\text{B}|}{92\text{B}} = 99.96\% > 5\%$.
        \item Output: \textbf{CONTRADICTION (FALSE)} $\implies$ \textbf{100\% REAL ERROR RECALL}
    \end{itemize}
};

\draw[arrow, draw=pbdarkred] (ground.south -| left_box.north) -- (left_box.north);
\draw[arrow, draw=pbdarkgreen] (ground.south -| right_box.north) -- (right_box.north);

\end{tikzpicture}
\end{document}
""",

    # --------------------------------------------------------------------------
    # Figure 5.2: Pareto Frontier (Fixed legend overlap and label boundary leak)
    # --------------------------------------------------------------------------
    "Chapter5/Figs/fig5_pareto_frontier.tex": r"""\documentclass[tikz,border=8pt]{standalone}
\usepackage{tikz}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\definecolor{pbdarkblue}{HTML}{1E3A8A}
\definecolor{pbdarkred}{HTML}{991B1B}
\definecolor{pbdarkgreen}{HTML}{065F46}

\begin{document}
\begin{tikzpicture}
\begin{axis}[
    title={\textbf{Coverage vs. Selective Accuracy Pareto Frontier}},
    xlabel={Coverage (\%)},
    ylabel={Selective Accuracy (\%)},
    xmin=0, xmax=112,
    ymin=45, ymax=106,
    grid=major,
    grid style={dashed, gray!30},
    legend style={at={(0.96,0.30)}, anchor=east, font=\sffamily\small},
    width=10.5cm, height=7.2cm,
    font=\sffamily
]

% HalDetect Curve
\addplot[
    color=pbdarkblue,
    mark=square*,
    line width=1.5pt
] coordinates {
    (25.4, 80.85)
    (42.0, 80.60)
    (49.4, 98.18)
    (100.0, 97.60)
};
\addlegendentry{HalDetect 2.5 (Neuro-Symbolic)}

% Modern SOTA RAG
\addplot[
    color=pbdarkred,
    mark=triangle*,
    dashed,
    line width=1.3pt
] coordinates {
    (100.0, 69.20)
};
\addlegendentry{Modern SOTA RAG}

% Non-Routed Baseline
\addplot[
    color=gray,
    mark=diamond*,
    dotted,
    line width=1.3pt
] coordinates {
    (100.0, 60.00)
};
\addlegendentry{Non-Routed Baseline}

% Annotations safely positioned inside boundaries
\node[above, text=pbdarkgreen, font=\bfseries\sffamily\small] at (axis cs: 49.4, 99.0) {98.18\% Peak Precision};
\node[above left, text=pbdarkblue, font=\bfseries\sffamily\small] at (axis cs: 100.0, 98.5) {97.60\% (100\% Cov)};

\end{axis}
\end{tikzpicture}
\end{document}
""",

    # --------------------------------------------------------------------------
    # Figure 3.2: DAG Conjunction Flowchart
    # --------------------------------------------------------------------------
    "Chapter3/Figs/fig3_dag_conjunction.tex": r"""\documentclass[tikz,border=8pt]{standalone}
\usepackage{tikz}
\usepackage{amssymb}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning, calc}
\definecolor{pbblue}{HTML}{E6F3FF}
\definecolor{pbdarkblue}{HTML}{1E3A8A}
\definecolor{pbmint}{HTML}{E0F2F1}
\definecolor{pbdarkgreen}{HTML}{065F46}
\definecolor{pblavender}{HTML}{F3E5F5}
\definecolor{pbdarkpurple}{HTML}{581C87}
\definecolor{pbyellow}{HTML}{FEF3C7}
\definecolor{pbcoral}{HTML}{FEE2E2}
\definecolor{pbdarkred}{HTML}{991B1B}
\definecolor{pbgray}{HTML}{F3F4F6}

\begin{document}
\begin{tikzpicture}[
    font=\sffamily\small,
    box/.style={draw=black!70, rounded corners=4pt, line width=0.8pt, align=center, inner sep=6pt},
    arrow/.style={-{Stealth[scale=1.0]}, line width=1pt, draw=black!70}
]

\node[box, fill=pbyellow!70, text=black!90, font=\bfseries\sffamily, minimum width=4.5cm] (input) {Compound Proposition\\$\mathcal{T} = \langle S, P, O, T, M \rangle$};

\node[box, fill=pbblue!70, text=pbdarkblue, below left=1.2cm and 0.5cm of input, minimum width=3.2cm] (m1) {\textbf{Aspect 1: Quantitative}\\$\mathcal{V}_1 \in \{\top, \bot, ?\}$};
\node[box, fill=pblavender!70, text=pbdarkpurple, below=1.2cm of input, minimum width=3.2cm] (m2) {\textbf{Aspect 2: Temporal}\\$\mathcal{V}_2 \in \{\top, \bot, ?\}$};
\node[box, fill=pbgray, text=black!80, below right=1.2cm and 0.5cm of input, minimum width=3.2cm] (m3) {\textbf{Aspect 3: Relational}\\$\mathcal{V}_3 \in \{\top, \bot, ?\}$};

\draw[arrow] (input) -- (m1);
\draw[arrow] (input) -- (m2);
\draw[arrow] (input) -- (m3);

\node[box, fill=pbmint!80, text=pbdarkgreen, font=\bfseries\sffamily, below=1.2cm of m2, minimum width=5.5cm] (dag) {3-Valued Conjunction Engine\\$\mathcal{V}_{\text{final}} = \mathcal{V}_1 \wedge \mathcal{V}_2 \wedge \mathcal{V}_3$};

\draw[arrow] (m1) -- (dag.north west);
\draw[arrow] (m2) -- (dag.north);
\draw[arrow] (m3) -- (dag.north east);

\node[box, fill=pbcoral!70, text=pbdarkred, below left=1.0cm and -0.8cm of dag, minimum width=3.5cm] (rule1) {\textbf{Fatal Discrepancy Rule}\\$\exists i: \mathcal{V}_i = \bot \implies \mathcal{V} = \texttt{FALSE}$};
\node[box, fill=pbmint, text=pbdarkgreen, below right=1.0cm and -0.8cm of dag, minimum width=3.5cm] (rule2) {\textbf{Unanimous Entailment}\\$\forall i: \mathcal{V}_i = \top \implies \mathcal{V} = \texttt{TRUE}$};

\draw[arrow, draw=pbdarkred] (dag.south) -| (rule1.north);
\draw[arrow, draw=pbdarkgreen] (dag.south) -| (rule2.north);

\end{tikzpicture}
\end{document}
""",

    # --------------------------------------------------------------------------
    # Figure 5.3: Calibration Reliability Curve
    # --------------------------------------------------------------------------
    "Chapter5/Figs/fig5_calibration_curve.tex": r"""\documentclass[tikz,border=8pt]{standalone}
\usepackage{tikz}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\definecolor{pbdarkblue}{HTML}{1E3A8A}
\definecolor{pbdarkgreen}{HTML}{065F46}

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
    width=9.5cm, height=7cm,
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
            print(res.stdout[-300:])

if __name__ == "__main__":
    main()
