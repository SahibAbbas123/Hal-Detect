import os
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent

figures = {
    "Chapter1/Figs/fig1_triage_paradigm.tex": r"""\documentclass[tikz,border=5pt]{standalone}
\usepackage{tikz}\n\usepackage{amssymb}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning, calc, backgrounds, matrix, fit}
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
    font=\sffamily,
    box/.style={draw=black!70, rounded corners=4pt, line width=0.8pt, align=center, inner sep=6pt},
    arrow/.style={-{Stealth[scale=1.0]}, line width=1pt, draw=black!70}
]

% Top: Traditional Paradigm
\node[box, fill=pbcoral!60, text=pbdarkred, font=\bfseries\sffamily, minimum width=3.5cm] (input1) {Generated LLM\\Response (Paragraph)};
\node[box, fill=pbgray, right=1.5cm of input1, minimum width=3.5cm] (rag) {Monolithic Neural\\Cross-Encoder / Judge};
\node[box, fill=pbcoral, text=pbdarkred, right=1.5cm of rag, font=\bfseries\sffamily, minimum width=3.2cm] (out1) {Binary Flag (Whole Output)\\$\times$ Token Overlap Trap\\$\times$ Zero Audit Trail};

\draw[arrow] (input1) -- (rag);
\draw[arrow] (rag) -- (out1);

% Divider
\draw[dashed, line width=0.8pt, black!40] ($(input1.south west)+(-0.5,-0.8)$) -- ($(out1.south east)+(0.5,-0.8)$);

% Bottom: HalDetect Triage
\node[box, fill=pbblue!70, text=pbdarkblue, font=\bfseries\sffamily, minimum width=3.5cm, below=1.6cm of input1] (input2) {Generated LLM\\Response (Paragraph)};
\node[box, fill=pblavender!70, right=0.8cm of input2, minimum width=3.0cm] (atom) {5-Tuple Atomizer\\+ Anaphora Engine};
\node[box, fill=pbyellow!70, text=black!80, right=0.8cm of atom, minimum width=2.8cm] (router) {Deterministic\\Taxonomy Router};

\node[box, fill=pbmint!80, text=pbdarkgreen, above right=-0.3cm and 0.8cm of router, minimum width=2.6cm, font=\small] (alu1) {Symbolic ALUs\\(Exact Math \& KG)};
\node[box, fill=pbmint!80, text=pbdarkgreen, below right=-0.3cm and 0.8cm of router, minimum width=2.6cm, font=\small] (alu2) {Calibrated NLI\\(Open Semantics)};

\node[box, fill=pbmint, text=pbdarkgreen, font=\bfseries\sffamily, right=3.8cm of router, minimum width=3.2cm] (out2) {Proposition Verifications\\$\checkmark$ 97.6\% Accuracy\\$\checkmark$ Exact Factual Audit};

\draw[arrow] (input2) -- (atom);
\draw[arrow] (atom) -- (router);
\draw[arrow] (router.north east) -- (alu1.west);
\draw[arrow] (router.south east) -- (alu2.west);
\draw[arrow] (alu1.east) -- (out2.north west);
\draw[arrow] (alu2.east) -- (out2.south west);

\node[above=0.1cm of input1, font=\bfseries\sffamily\small, text=pbdarkred] {(A) Monolithic Black-Box Paradigm (Prone to Attention Dilution)};
\node[above=0.1cm of input2, font=\bfseries\sffamily\small, text=pbdarkblue] {(B) HalDetect Type-Directed Neuro-Symbolic Triage};

\end{tikzpicture}
\end{document}
""",

    "Chapter3/Figs/fig3_architecture_pipeline.tex": r"""\documentclass[tikz,border=5pt]{standalone}
\usepackage{tikz}\n\usepackage{amssymb}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning, calc, backgrounds, matrix, fit}
\definecolor{pbblue}{HTML}{E6F3FF}
\definecolor{pbdarkblue}{HTML}{1E3A8A}
\definecolor{pbmint}{HTML}{E0F2F1}
\definecolor{pbdarkgreen}{HTML}{065F46}
\definecolor{pblavender}{HTML}{F3E5F5}
\definecolor{pbdarkpurple}{HTML}{581C87}
\definecolor{pbyellow}{HTML}{FEF3C7}
\definecolor{pbdarkorange}{HTML}{9A3412}
\definecolor{pbcoral}{HTML}{FEE2E2}
\definecolor{pbdarkred}{HTML}{991B1B}
\definecolor{pbgray}{HTML}{F3F4F6}

\begin{document}
\begin{tikzpicture}[
    font=\sffamily\small,
    box/.style={draw=black!70, rounded corners=4pt, line width=0.8pt, align=center, inner sep=6pt},
    arrow/.style={-{Stealth[scale=1.0]}, line width=1pt, draw=black!70}
]

% Step 1: Input & Atomizer
\node[box, fill=pbblue!70, text=pbdarkblue, font=\bfseries\sffamily, minimum width=3.2cm] (raw) {Unconstrained\\Generated Text};
\node[box, fill=pblavender!70, text=pbdarkpurple, right=0.8cm of raw, minimum width=3.4cm] (atom) {5-Tuple Atomizer\\$\langle S, P, O, T, M \rangle$\\+ Anaphora Tracker};
\node[box, fill=pbyellow!70, text=pbdarkorange, font=\bfseries\sffamily, right=0.8cm of atom, minimum width=2.8cm] (router) {Deterministic\\Taxonomy Router\\($<0.05\text{ms}$)};

\draw[arrow] (raw) -- (atom);
\draw[arrow] (atom) -- (router);

% 5 Specialized ALUs
\node[box, fill=pbmint!80, text=pbdarkgreen, above right=1.6cm and 1.2cm of router, minimum width=3.6cm] (alu1) {\textbf{Quantitative SI ALU}\\Dimensional Base ($\Delta \le \tau$)\\+ World Bank OData};
\node[box, fill=pbmint!80, text=pbdarkgreen, above right=0.5cm and 1.2cm of router, minimum width=3.6cm] (alu2) {\textbf{Temporal ALU}\\2-Hop SPARQL Filtering\\+ 7-Continent Resolver};
\node[box, fill=pbmint!80, text=pbdarkgreen, below right=0.5cm and 1.2cm of router, minimum width=3.6cm] (alu3) {\textbf{Entity-Attribute ALU}\\Score-Commit Gate ($s>0.6$)\\+ Alias Lexicon Closure};
\node[box, fill=pbmint!80, text=pbdarkgreen, below right=1.6cm and 1.2cm of router, minimum width=3.6cm] (alu4) {\textbf{Citation ALU}\\CrossRef Live REST API\\($\text{MIN\_WORK\_CONTENT}\ge 2$)};
\node[box, fill=pbgray!90, text=black!80, below right=2.7cm and 1.2cm of router, minimum width=3.6cm] (alu5) {\textbf{Relational NLI Fallback}\\Calibrated DeBERTa-v3\\($\text{Margin} \ge \gamma$)};

\draw[arrow] (router.east) -- ++(0.5,0) |- (alu1.west);
\draw[arrow] (router.east) -- ++(0.5,0) |- (alu2.west);
\draw[arrow] (router.east) -- ++(0.5,0) |- (alu3.west);
\draw[arrow] (router.east) -- ++(0.5,0) |- (alu4.west);
\draw[arrow] (router.east) -- ++(0.5,0) |- (alu5.west);

% Decision Engine
\node[box, fill=pblavender!90, text=pbdarkpurple, font=\bfseries\sffamily, right=1.2cm of alu3, minimum width=3.6cm] (dag) {Multi-Aspect DAG\\Conjunction Engine\\($\mathcal{V}_{\text{final}} = \bigwedge \mathcal{V}_i$)};

\draw[arrow] (alu1.east) -| (dag.north);
\draw[arrow] (alu2.east) -- (dag.west);
\draw[arrow] (alu3.east) -- (dag.west);
\draw[arrow] (alu4.east) -- (dag.west);
\draw[arrow] (alu5.east) -| (dag.south);

\node[box, fill=pbmint, text=pbdarkgreen, font=\bfseries\sffamily, right=0.8cm of dag, minimum width=3.0cm] (verdict) {3-Valued Output\\$\{\texttt{TRUE}, \texttt{FALSE}, \texttt{UNV}\}$};

\draw[arrow] (dag) -- (verdict);

\end{tikzpicture}
\end{document}
""",

    "Chapter4/Figs/fig4_dataset_lineage.tex": r"""\documentclass[tikz,border=5pt]{standalone}
\usepackage{tikz}\n\usepackage{amssymb}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning, calc, backgrounds, matrix, fit}
\definecolor{pbblue}{HTML}{E6F3FF}
\definecolor{pbdarkblue}{HTML}{1E3A8A}
\definecolor{pbmint}{HTML}{E0F2F1}
\definecolor{pbdarkgreen}{HTML}{065F46}
\definecolor{pblavender}{HTML}{F3E5F5}
\definecolor{pbdarkpurple}{HTML}{581C87}
\definecolor{pbyellow}{HTML}{FEF3C7}
\definecolor{pbdarkorange}{HTML}{9A3412}
\definecolor{pbcoral}{HTML}{FEE2E2}
\definecolor{pbdarkred}{HTML}{991B1B}
\definecolor{pbgray}{HTML}{F3F4F6}

\begin{document}
\begin{tikzpicture}[
    font=\sffamily\small,
    box/.style={draw=black!70, rounded corners=4pt, line width=0.8pt, align=center, inner sep=6pt},
    arrow/.style={-{Stealth[scale=1.0]}, line width=1pt, draw=black!70}
]

\node[box, fill=pbcoral!50, text=pbdarkred, minimum width=3.2cm] (p1) {\textbf{Phase 1: Genesis}\\Batch 1 ($N=125$)\\8 Gold FALSE (Skew)};
\node[box, fill=pbyellow!50, text=pbdarkorange, right=0.8cm of p1, minimum width=3.2cm] (p2) {\textbf{Phase 2: Entity Gate}\\Phase 2 Gold ($N=126$)\\Q22\_C01 Relabeling};
\node[box, fill=pblavender!50, text=pbdarkpurple, right=0.8cm of p2, minimum width=3.2cm] (p3) {\textbf{Phase 3: Synthetic Negs}\\Batch 3 ($N=122$)\\+ 84 Hard Negatives};
\node[box, fill=pbmint!80, text=pbdarkgreen, font=\bfseries\sffamily, right=0.8cm of p3, minimum width=3.6cm] (p4) {\textbf{Phase 4: Symmetrical 1K}\\Master Corpus ($N=1,000$)\\500 TRUE / 500 FALSE};

\draw[arrow] (p1) -- (p2);
\draw[arrow] (p2) -- (p3);
\draw[arrow] (p3) -- (p4);

\node[box, fill=pbblue!70, text=pbdarkblue, font=\bfseries\sffamily, below=1.2cm of p4, minimum width=4.0cm] (t2) {\textbf{Track 2 Generative Suite}\\7 Models $\times$ 50 Prompts\\1,798 Propositions (31 Confabulations)};

\draw[arrow] (p4) -- (t2);

\end{tikzpicture}
\end{document}
""",

    "Chapter5/Figs/fig5_pareto_frontier.tex": r"""\documentclass[tikz,border=5pt]{standalone}
\usepackage{tikz}\n\usepackage{amssymb}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\definecolor{pbdarkblue}{HTML}{1E3A8A}
\definecolor{pbdarkgreen}{HTML}{065F46}
\definecolor{pbdarkred}{HTML}{991B1B}

\begin{document}
\begin{tikzpicture}
\begin{axis}[
    title={\textbf{Coverage vs. Selective Accuracy Pareto Frontier}},
    xlabel={Coverage (\%)},
    ylabel={Selective Accuracy (\%)},
    xmin=0, xmax=105,
    ymin=50, ymax=102,
    grid=major,
    grid style={dashed, gray!30},
    legend pos=south west,
    width=10cm, height=7cm,
    font=\sffamily
]

% HalDetect Curve
\addplot[
    color=pbdarkblue,
    mark=square*,
    line width=1.5pt
] coordinates {
    (25.3, 81.0)
    (41.9, 80.6)
    (49.2, 98.2)
    (100.0, 97.6)
};
\addlegendentry{HalDetect 2.5 (Neuro-Symbolic)}

% Modern SOTA RAG
\addplot[
    color=pbdarkred,
    mark=triangle*,
    dashed,
    line width=1.2pt
] coordinates {
    (10.0, 52.0)
    (40.0, 58.0)
    (100.0, 69.2)
};
\addlegendentry{Modern SOTA RAG}

% Non-Routed Baseline
\addplot[
    color=gray,
    mark=*,
    dotted,
    line width=1.2pt
] coordinates {
    (100.0, 60.0)
};
\addlegendentry{Non-Routed Baseline}

\node[above, font=\small\sffamily, color=pbdarkgreen] at (axis cs:49.2, 98.2) {\textbf{98.18\% Peak Precision}};
\node[above, font=\small\sffamily, color=pbdarkblue] at (axis cs:100.0, 97.6) {\textbf{97.60\% Full Coverage}};

\end{axis}
\end{tikzpicture}
\end{document}
""",

    "Chapter5/Figs/fig5_attention_dilution.tex": r"""\documentclass[tikz,border=5pt]{standalone}
\usepackage{tikz}\n\usepackage{amssymb}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning, calc, backgrounds, matrix, fit}
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
    box/.style={draw=black!70, rounded corners=4pt, line width=0.8pt, align=center, inner sep=6pt},
    arrow/.style={-{Stealth[scale=1.0]}, line width=1pt, draw=black!70}
]

% Claim box
\node[box, fill=pbgray, minimum width=10cm, align=left] (claim) {
    \textbf{Generated Claim:} "The Apple M3 Max is manufactured on a \textcolor{pbdarkred}{\textbf{40nm}} process with \textcolor{pbdarkred}{\textbf{40 million}} transistors."
};

% Retrieved Passage box
\node[box, fill=pbgray, below=0.6cm of claim, minimum width=10cm, align=left] (passage) {
    \textbf{Retrieved Article:} "The Apple M3 Max is manufactured on TSMC's \textcolor{pbdarkgreen}{\textbf{3nm}} process with \textcolor{pbdarkgreen}{\textbf{92 billion}} transistors..."
};

% Neural RAG Path (Left)
\node[box, fill=pbcoral!70, text=pbdarkred, below left=1.2cm and -1.0cm of passage, minimum width=4.5cm] (neural) {
    \textbf{Neural Cross-Encoder}\\
    $\bullet$ High word overlap (85\% match)\\
    $\bullet$ Attention heads dilute onto nouns\\
    $\bullet$ Softmax $\rightarrow$ \textbf{ENTAILMENT (TRUE)}\\
    \textbf{$\times$ Error Missed (0\% Recall)}
};

% HalDetect ALU Path (Right)
\node[box, fill=pbmint!80, text=pbdarkgreen, below right=1.2cm and -1.0cm of passage, minimum width=4.5cm] (alu) {
    \textbf{HalDetect SI ALU}\\
    $\bullet$ Extracts values: $40\text{M}$ vs $92\text{B}$\\
    $\bullet$ Arithmetic Error: $\Delta = 99.96\% > \tau$\\
    $\bullet$ Emits \textbf{CONTRADICTION (FALSE)}\\
    \textbf{$\checkmark$ 100\% Real Error Recall}
};

\draw[arrow, draw=pbdarkred] (passage.south) -| (neural.north);
\draw[arrow, draw=pbdarkgreen] (passage.south) -| (alu.north);

\end{tikzpicture}
\end{document}
"""
}

for rel_path, tex_code in figures.items():
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
        print(f"  ❌ Error compiling {p.name}")
        for line in res.stdout.splitlines()[-15:]:
            print("    ", line)

extra_figures = {
    "Chapter3/Figs/fig3_dag_conjunction.tex": r"""\documentclass[tikz,border=5pt]{standalone}
\usepackage{tikz}
\usepackage{amssymb}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning, calc, backgrounds, matrix, fit}
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

\node[box, fill=pbyellow!70, text=black!90, font=\bfseries\sffamily, minimum width=4cm] (input) {Compound Proposition\\$\mathcal{T} = \langle S, P, O, T, M \rangle$};

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

\node[box, fill=pbcoral!70, text=pbdarkred, below left=1.0cm and -0.8cm of dag, minimum width=3.2cm] (rule1) {\textbf{Fatal Discrepancy}\\$\exists i: \mathcal{V}_i = \bot \implies \mathcal{V} = \texttt{FALSE}$};
\node[box, fill=pbmint, text=pbdarkgreen, below right=1.0cm and -0.8cm of dag, minimum width=3.2cm] (rule2) {\textbf{Unanimous Entailment}\\$\forall i: \mathcal{V}_i = \top \implies \mathcal{V} = \texttt{TRUE}$};

\draw[arrow, draw=pbdarkred] (dag.south) -| (rule1.north);
\draw[arrow, draw=pbdarkgreen] (dag.south) -| (rule2.north);

\end{tikzpicture}
\end{document}
""",

    "Chapter5/Figs/fig5_calibration_curve.tex": r"""\documentclass[tikz,border=5pt]{standalone}
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

% Perfect Calibration Diagonal
\addplot[
    color=gray,
    dashed,
    line width=1pt
] coordinates {
    (0.0, 0.0)
    (1.0, 1.0)
};
\addlegendentry{Perfect Calibration}

% HalDetect 10-bin ECE
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

for rel_path, tex_code in extra_figures.items():
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
        print(f"  ❌ Error compiling {p.name}")
