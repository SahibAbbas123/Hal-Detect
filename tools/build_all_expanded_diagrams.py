import os
import subprocess
import matplotlib.pyplot as plt
import numpy as np

out_dir = '/Users/sahibabc/8th Semester Materials/ThesisCode_copy/exported_diagrams_preview/iteration_3_expanded_suite'
os.makedirs(out_dir, exist_ok=True)

# -------------------------------------------------------------------------
# 1. LATEX / TIKZ METHODOLOGY DIAGRAMS
# -------------------------------------------------------------------------

fig3_dag_tex = r"""\documentclass[tikz,border=15pt]{standalone}
\usepackage{tikz}
\usepackage{amssymb}
\usepackage{amsmath}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning, calc, backgrounds, fit, shadows.blur}

\definecolor{navyDark}{HTML}{0B2545}
\definecolor{navyLight}{HTML}{F0F4F8}
\definecolor{navyBorder}{HTML}{134074}

\definecolor{emeraldDark}{HTML}{0E6251}
\definecolor{emeraldLight}{HTML}{E8F8F5}
\definecolor{emeraldBorder}{HTML}{16A085}

\definecolor{purpleDark}{HTML}{512E5F}
\definecolor{purpleLight}{HTML}{F4ECF7}
\definecolor{purpleBorder}{HTML}{8E44AD}

\definecolor{amberDark}{HTML}{7D6608}
\definecolor{amberLight}{HTML}{FEF9E7}
\definecolor{amberBorder}{HTML}{D4AC0D}

\definecolor{crimsonDark}{HTML}{78281F}
\definecolor{crimsonLight}{HTML}{FDF2E9}
\definecolor{crimsonBorder}{HTML}{C0392B}

\definecolor{slateDark}{HTML}{2C3E50}
\definecolor{slateLight}{HTML}{F8F9FA}
\definecolor{slateBorder}{HTML}{BDC3C7}

\begin{document}
\begin{tikzpicture}[
    font=\sffamily,
    >=Stealth,
    card/.style={
        draw=#1Border, fill=white, line width=1.0pt, rounded corners=6pt,
        blur shadow={shadow blur steps=4, shadow xshift=1pt, shadow yshift=-1.5pt, shadow opacity=12},
        align=center, inner sep=7pt
    },
    wire/.style={
        ->, line width=1.2pt, draw=#1Border
    }
]

\node[card=navy, minimum width=7.2cm, text width=6.9cm] (input) at (0, 4.5) {
    \textbf{\color{navyDark}\large Compound Proposition Evaluation}\\
    \vspace{2pt}
    \scriptsize 5-Tuple: $\mathcal{T} = \langle S, P, O, T, M \rangle$\\
    \scriptsize Multi-Aspect Decomposed Query
};

% 3 Parallel Aspect Evaluators
\node[card=emerald, minimum width=4.8cm, text width=4.5cm] (m1) at (-5.4, 2.0) {
    \textbf{\color{emeraldDark} Aspect 1: Quantitative}\\
    \scriptsize SI Tolerance: $\Delta \le 5\%$\\
    \scriptsize Verdict: $\mathcal{V}_1 \in \{\top, \bot, ?\}$
};

\node[card=purple, minimum width=4.8cm, text width=4.5cm] (m2) at (0, 2.0) {
    \textbf{\color{purpleDark} Aspect 2: Temporal}\\
    \scriptsize Wikidata Interval Bounds\\
    \scriptsize Verdict: $\mathcal{V}_2 \in \{\top, \bot, ?\}$
};

\node[card=slate, minimum width=4.8cm, text width=4.5cm] (m3) at (5.4, 2.0) {
    \textbf{\color{slateDark} Aspect 3: Relational}\\
    \scriptsize Cross-Encoder Calibrated NLI\\
    \scriptsize Verdict: $\mathcal{V}_3 \in \{\top, \bot, ?\}$
};

\draw[wire=navy] (input.south) -| (m1.north);
\draw[wire=navy] (input.south) -- (m2.north);
\draw[wire=navy] (input.south) -| (m3.north);

% 3-Valued Conjunction Engine
\node[card=amber, minimum width=8.5cm, text width=8.0cm] (dag) at (0, -0.6) {
    \textbf{\color{amberDark}\large 3-Valued Conjunction Engine}\\
    \vspace{3pt}
    \small $\mathcal{V}_{\text{final}} = \mathcal{V}_1 \wedge \mathcal{V}_2 \wedge \mathcal{V}_3 = \bigwedge_{j=1}^M \mathcal{V}_j$\\
    \vspace{2pt}
    \scriptsize Kleene / HalDetect 3-Valued Epistemic Algebra
};

\draw[wire=emerald] (m1.south) |- ($(dag.west) + (0, 0.2)$);
\draw[wire=purple] (m2.south) -- (dag.north);
\draw[wire=slate] (m3.south) |- ($(dag.east) + (0, 0.2)$);

% Decision Branches
\node[card=crimson, minimum width=6.2cm, text width=5.8cm] (rule1) at (-4.2, -3.2) {
    \textbf{\color{crimsonDark}\large Fatal Discrepancy Gate}\\
    \vspace{2pt}
    \scriptsize $\exists i: \mathcal{V}_i = \bot \implies \mathcal{V}_{\text{final}} = \textbf{\texttt{FALSE}}$\\
    \vspace{2pt}
    \textbf{\color{crimsonDark}\footnotesize Decisive Hallucination Rejection}
};

\node[card=emerald, minimum width=6.2cm, text width=5.8cm] (rule2) at (4.2, -3.2) {
    \textbf{\color{emeraldDark}\large Unanimous Entailment}\\
    \vspace{2pt}
    \scriptsize $\forall i: \mathcal{V}_i = \top \implies \mathcal{V}_{\text{final}} = \textbf{\texttt{TRUE}}$\\
    \vspace{2pt}
    \textbf{\color{emeraldDark}\footnotesize Certified Factual Grounding}
};

\draw[wire=crimson] (dag.south) -| (rule1.north);
\draw[wire=emerald] (dag.south) -| (rule2.north);

\end{tikzpicture}
\end{document}
"""

fig3_anaphora_tex = r"""\documentclass[tikz,border=15pt]{standalone}
\usepackage{tikz}
\usepackage{amssymb}
\usepackage{amsmath}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning, calc, backgrounds, fit, shadows.blur}

\definecolor{navyDark}{HTML}{0B2545}
\definecolor{navyLight}{HTML}{F0F4F8}
\definecolor{navyBorder}{HTML}{134074}

\definecolor{emeraldDark}{HTML}{0E6251}
\definecolor{emeraldLight}{HTML}{E8F8F5}
\definecolor{emeraldBorder}{HTML}{16A085}

\definecolor{purpleDark}{HTML}{512E5F}
\definecolor{purpleLight}{HTML}{F4ECF7}
\definecolor{purpleBorder}{HTML}{8E44AD}

\definecolor{amberDark}{HTML}{7D6608}
\definecolor{amberLight}{HTML}{FEF9E7}
\definecolor{amberBorder}{HTML}{D4AC0D}

\definecolor{slateDark}{HTML}{2C3E50}
\definecolor{slateLight}{HTML}{F8F9FA}
\definecolor{slateBorder}{HTML}{BDC3C7}

\begin{document}
\begin{tikzpicture}[
    font=\sffamily,
    >=Stealth,
    zonebox/.style={
        draw=#1Border, fill=#1Light!30, line width=1.1pt, rounded corners=8pt,
        blur shadow={shadow blur steps=4, shadow xshift=1pt, shadow yshift=-1.5pt, shadow opacity=12}
    },
    card/.style={
        draw=#1Border, fill=white, line width=0.9pt, rounded corners=5pt,
        align=center, inner sep=6pt
    },
    wire/.style={
        ->, line width=1.1pt, draw=#1Border
    }
]

% Phase 1: Sentence Parsing & Entity Linking
\draw[zonebox=navy] (-0.4, -3.8) rectangle (6.2, 3.2);
\node[fill=navyBorder, text=white, font=\bfseries\sffamily\scriptsize, rounded corners=3pt, inner sep=3pt] at (2.9, 3.2) {Stage 1: Discourse \& Anaphora};

\node[card=navy, minimum width=5.6cm, text width=5.2cm] (raw_text) at (2.9, 2.0) {
    \textbf{\color{navyDark} Input Paragraph Stream}\\
    \scriptsize \textit{``The processor was released in 2023.}\\
    \scriptsize \textit{\textbf{\color{purpleDark}It} features 92B transistors.''}
};

\node[card=purple, below=0.6cm of raw_text, minimum width=5.6cm, text width=5.2cm] (anaphora_reg) {
    \textbf{\color{purpleDark} Antecedent Registry ($\mathcal{A}$)}\\
    \scriptsize Pronoun Resolution: $\text{`It'} \mapsto \text{`M3 Max'}$\\
    \scriptsize Forward Pointer Cache
};

\node[card=slate, below=0.6cm of anaphora_reg, minimum width=5.6cm, text width=5.2cm] (resolved_text) {
    \textbf{\color{slateDark} Grounded Sentence Pairs}\\
    \scriptsize Disambiguated Canonical Surface
};

\draw[wire=navy] (raw_text) -- (anaphora_reg);
\draw[wire=purple] (anaphora_reg) -- (resolved_text);


% Phase 2: 5-Tuple Schema Extraction
\draw[zonebox=purple] (7.0, -3.8) rectangle (13.6, 3.2);
\node[fill=purpleBorder, text=white, font=\bfseries\sffamily\scriptsize, rounded corners=3pt, inner sep=3pt] at (10.3, 3.2) {Stage 2: 5-Tuple Serialization};

\node[card=purple, minimum width=5.6cm, text width=5.2cm] (slot_s) at (10.3, 2.0) {
    \textbf{\color{purpleDark} Subject ($S$) \& Predicate ($P$)}\\
    \scriptsize $S = \text{``Apple M3 Max''}, \quad P = \text{``transistor count''}$
};

\node[card=purple, below=0.6cm of slot_s, minimum width=5.6cm, text width=5.2cm] (slot_o) {
    \textbf{\color{purpleDark} Object ($O$) \& Temporal ($T$)}\\
    \scriptsize $O = 92\times 10^9, \quad T = [2023, \text{present}]$
};

\node[card=amber, below=0.6cm of slot_o, minimum width=5.6cm, text width=5.2cm] (slot_m) {
    \textbf{\color{amberDark} Modality Class ($\mathcal{M}$)}\\
    \scriptsize $\mathcal{M} = \textbf{\texttt{QUANTITATIVE\_SI}}$ ($<0.05\,\text{ms}$)
};

\draw[wire=purple] (slot_s) -- (slot_o);
\draw[wire=purple] (slot_o) -- (slot_m);

\draw[wire=slate] (resolved_text.east) -- (slot_s.west);


% Phase 3: Symbolic Verifier & Grounding
\draw[zonebox=emerald] (14.4, -3.8) rectangle (21.0, 3.2);
\node[fill=emeraldBorder, text=white, font=\bfseries\sffamily\scriptsize, rounded corners=3pt, inner sep=3pt] at (17.7, 3.2) {Stage 3: Deterministic ALU Grounding};

\node[card=emerald, minimum width=5.6cm, text width=5.2cm] (api_query) at (17.7, 2.0) {
    \textbf{\color{emeraldDark} Ground Truth Fetch}\\
    \scriptsize SPARQL / Live FRED / SI Registry
};

\node[card=emerald, below=0.6cm of api_query, minimum width=5.6cm, text width=5.2cm] (error_calc) {
    \textbf{\color{emeraldDark} Math ALU Evaluation}\\
    \scriptsize $\Delta = \frac{|40\text{M} - 92\text{B}|}{92\text{B}} = 99.96\% > 5\%$
};

\node[card=emerald, below=0.6cm of error_calc, minimum width=5.6cm, text width=5.2cm] (epistemic_out) {
    \textbf{\color{emeraldDark} Atomic Verdict: $\mathcal{V}_k = \bot$}\\
    \scriptsize \textbf{\color{crimsonDark}\checkmark Fatal Hallucination Flagged}
};

\draw[wire=emerald] (api_query) -- (error_calc);
\draw[wire=emerald] (error_calc) -- (epistemic_out);

\draw[wire=amber] (slot_m.east) -- (api_query.west);

\end{tikzpicture}
\end{document}
"""

tikz_diagrams = [
    ('fig3_dag_conjunction_upgraded', fig3_dag_tex),
    ('fig3_anaphora_lifecycle_upgraded', fig3_anaphora_tex),
]

for name, code in tikz_diagrams:
    tex_path = os.path.join(out_dir, f"{name}.tex")
    with open(tex_path, "w") as f:
        f.write(code)
    print(f"Compiling {name}...")
    res = subprocess.run(["pdflatex", "-interaction=nonstopmode", f"{name}.tex"], cwd=out_dir, capture_output=True, text=True)
    if res.returncode == 0:
        subprocess.run(["pdftoppm", "-png", "-r", "300", f"{name}.pdf", f"{name}_preview"], cwd=out_dir, check=True)
        print(f"  --> Built {name}.pdf & 300 DPI PNG successfully!")
    else:
        print(f"  --> Error compiling {name}: {res.stdout[-300:]}")


# -------------------------------------------------------------------------
# 2. STATISTICAL PLOTS
# -------------------------------------------------------------------------
plt.rcParams['font.sans-serif'] = 'Helvetica', 'Arial', 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'

# ----------------- PLOT 2: MULTI-METRIC RADAR / BUBBLE (Latency vs Accuracy) -----------------
models = ['HalDetect (Ours)', 'DeBERTa-v3', 'MiniCheck-7B', 'GPT-4 Judge', 'Non-Routed RAG']
accuracy = [97.60, 60.00, 69.20, 78.40, 54.10]
latency_ms = [4.2, 38.5, 420.0, 1850.0, 85.0]
num_recall = [100.0, 0.0, 0.0, 35.5, 12.0]
colors = ['#0E6251', '#134074', '#8E44AD', '#D4AC0D', '#78281F']

fig, ax = plt.subplots(figsize=(9.5, 5.2), dpi=300)
for i, m in enumerate(models):
    ax.scatter(latency_ms[i], accuracy[i], s=num_recall[i]*7 + 90, color=colors[i], alpha=0.85, edgecolors='black', linewidth=1.2, label=m)
    if m == 'HalDetect (Ours)':
        ax.annotate(f"{m}\nAcc: {accuracy[i]}% | Rec: {num_recall[i]}%", (latency_ms[i]*1.25, accuracy[i]-1.5), fontsize=9, fontweight='bold', color=colors[i])
    elif m == 'GPT-4 Judge':
        ax.annotate(f"{m}\nAcc: {accuracy[i]}% | Rec: {num_recall[i]}%", (latency_ms[i]*0.65, accuracy[i]+2.5), fontsize=9, fontweight='bold', color=colors[i])
    else:
        ax.annotate(f"{m}\nAcc: {accuracy[i]}% | Rec: {num_recall[i]}%", (latency_ms[i]*1.1, accuracy[i]+1.8), fontsize=9, fontweight='bold', color=colors[i])

ax.set_xscale('log')
ax.set_xlabel('Inference Latency per Claim (ms, Log Scale)', fontsize=11, fontweight='bold', color='#2C3E50')
ax.set_ylabel('Selective Accuracy (%)', fontsize=11, fontweight='bold', color='#2C3E50')
ax.set_title('Efficiency & Recall Frontier: HalDetect vs. SOTA Verification Paradigms', fontsize=12, fontweight='bold', pad=15, color='#0B2545')
ax.set_ylim(40, 106)
ax.set_xlim(2, 3500)
ax.grid(True, linestyle='--', alpha=0.4)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
fig_path2 = os.path.join(out_dir, 'fig5_cost_latency_tradeoff_preview-1.png')
plt.savefig(fig_path2, bbox_inches='tight')
plt.close()
print("  --> Re-built fig5_cost_latency_tradeoff_preview-1.png successfully!")
