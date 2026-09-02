import os
import subprocess

out_dir = '/Users/sahibabc/8th Semester Materials/ThesisCode_copy/exported_diagrams_preview/latex_vector_upgrades'
os.makedirs(out_dir, exist_ok=True)

# -------------------------------------------------------------------------
# FIGURE 1: Triage Paradigm
# -------------------------------------------------------------------------
fig1_tex = r"""\documentclass[tikz,border=15pt]{standalone}
\usepackage{tikz}
\usepackage{amsmath}
\usepackage{amssymb}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning, calc, backgrounds, fit, shadows.blur}

\definecolor{navyDark}{HTML}{0B2545}
\definecolor{navyLight}{HTML}{F0F4F8}
\definecolor{navyBorder}{HTML}{134074}

\definecolor{crimsonDark}{HTML}{78281F}
\definecolor{crimsonLight}{HTML}{FDF2E9}
\definecolor{crimsonBorder}{HTML}{C0392B}

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
    trackbox/.style={
        draw=#1Border, fill=#1Light!35, line width=1.1pt, rounded corners=10pt
    },
    card/.style={
        draw=#1Border, fill=white, line width=1.0pt, rounded corners=6pt,
        blur shadow={shadow blur steps=4, shadow xshift=1pt, shadow yshift=-1.5pt, shadow opacity=12},
        align=center, inner sep=6pt
    },
    wire/.style={
        ->, line width=1.2pt, draw=#1Border
    }
]

% ==================== PARADIGM A: MONOLITHIC BLACK-BOX ====================
\draw[trackbox=crimson] (-0.5, 3.4) rectangle (24.2, 7.8);
\node[anchor=west, font=\sffamily\bfseries\large, text=crimsonDark] at (0.0, 7.3) {(A) Monolithic Black-Box Paradigm};
\node[anchor=west, font=\sffamily\small, text=crimsonBorder] at (8.5, 7.3) {Prone to Attention Dilution $\bullet$ Zero Fact-Level Audit Trail};

\node[card=slate, minimum width=4.8cm, text width=4.5cm] (a_in) at (2.5, 5.2) {
    \textbf{\color{slateDark} Generated Text Response}\\
    \vspace{3pt}
    \footnotesize Multi-sentence LLM output\\
    \footnotesize paragraph with mixed facts
};

\node[card=crimson, right=2.4cm of a_in, minimum width=6.2cm, text width=5.8cm] (a_enc) {
    \textbf{\color{crimsonDark} Monolithic Cross-Encoder}\\
    \vspace{2pt}
    \footnotesize DeBERTa-v3 / LLM-as-Judge\\
    \vspace{3pt}
    \scriptsize \textcolor{crimsonDark!80}{Continuous self/cross-attention over all tokens}
};

\node[card=crimson, right=2.4cm of a_enc, minimum width=6.0cm, text width=5.6cm] (a_out) {
    \textbf{\color{crimsonDark} Binary Whole-Output Flag}\\
    \vspace{3pt}
    \scriptsize \textcolor{crimsonDark}{$\times$ \textbf{0\% Recall} on subtle numerical drift}\\
    \scriptsize \textcolor{crimsonDark}{$\times$ \textbf{Opaque verdict} without reasoning lineage}
};

\draw[wire=slate] (a_in) -- (a_enc) node[midway, above=2pt, font=\scriptsize\bfseries, text=slateDark] {Tokens};
\draw[wire=crimson] (a_enc) -- (a_out) node[midway, above=2pt, font=\scriptsize\bfseries, text=crimsonDark] {Logits};


% ==================== PARADIGM B: HALDETECT NEURO-SYMBOLIC ====================
\draw[trackbox=navy] (-0.5, -4.8) rectangle (24.2, 2.4);
\node[anchor=west, font=\sffamily\bfseries\large, text=navyDark] at (0.0, 1.9) {(B) HalDetect Type-Directed Neuro-Symbolic Triage};
\node[anchor=west, font=\sffamily\small, text=emeraldDark] at (11.5, 1.9) {Deterministic Routing $\bullet$ Domain ALUs $\bullet$ Calibrated Conjunction};

\node[card=navy, minimum width=3.4cm, text width=3.2cm] (b_in) at (1.6, -1.2) {
    \textbf{\color{navyDark} Generated Text}\\
    \vspace{2pt}
    \footnotesize Paragraph Output
};

\node[card=purple, right=0.6cm of b_in, minimum width=3.6cm, text width=3.4cm] (b_atom) {
    \textbf{\color{purpleDark} 5-Tuple Atomizer}\\
    \vspace{2pt}
    \scriptsize $\langle S, P, O, T, M \rangle$\\
    \scriptsize + Forward Anaphora
};

\node[card=amber, right=0.6cm of b_atom, minimum width=3.4cm, text width=3.2cm] (b_router) {
    \textbf{\color{amberDark} Modality Router}\\
    \vspace{2pt}
    \scriptsize Regex Classifier\\
    \scriptsize \textbf{$< 0.05\,\text{ms}$ Latency}
};

% Modality ALU Stack
\node[card=emerald, anchor=west, minimum width=5.0cm, text width=4.8cm] (b_alu) at ($(b_router.east) + (1.0cm, 1.3cm)$) {
    \textbf{\color{emeraldDark} Specialized Symbolic ALUs}\\
    \vspace{2pt}
    \scriptsize $\bullet$ \textbf{SI Math}: Relative $\Delta \le 5\%$\\
    \scriptsize $\bullet$ \textbf{Wikidata}: 2-Hop SPARQL intervals\\
    \scriptsize $\bullet$ \textbf{Citation}: Live CrossRef DOIs
};

\node[card=slate, anchor=west, minimum width=5.0cm, text width=4.8cm] (b_nli) at ($(b_router.east) + (1.0cm, -1.3cm)$) {
    \textbf{\color{slateDark} Calibrated Relational NLI}\\
    \vspace{2pt}
    \scriptsize $\bullet$ DeBERTa-v3 margin threshold\\
    \scriptsize $\bullet$ Open predicate fallback gate
};

% Output Decision
\node[card=emerald, right=1.0cm of $(b_alu.east)!0.5!(b_nli.east)$, minimum width=4.8cm, text width=4.5cm] (b_decision) {
    \textbf{\color{emeraldDark} 3-Valued Conjunction DAG}\\
    \vspace{3pt}
    \scriptsize \textcolor{emeraldDark}{\textbf{\checkmark 97.60\% Accuracy} ($+37.6\%$ gain)}\\
    \scriptsize \textcolor{emeraldDark}{\textbf{\checkmark ECE 8.88\%} (Calibrated)}\\
    \scriptsize \textcolor{emeraldDark}{\textbf{\checkmark Exact Factual Audit Trail}}
};

% Wires
\draw[wire=navy] (b_in) -- (b_atom);
\draw[wire=purple] (b_atom) -- (b_router);
\draw[wire=amber] (b_router.east) -- ++(0.4,0) |- (b_alu.west);
\draw[wire=amber] (b_router.east) -- ++(0.4,0) |- (b_nli.west);

\draw[wire=emerald] (b_alu.east) -| ++(0.4,-0.6) |- ($(b_decision.west) + (0, 0.4)$);
\draw[wire=slate] (b_nli.east) -| ++(0.4,0.6) |- ($(b_decision.west) + (0, -0.4)$);

\end{tikzpicture}
\end{document}
"""

# -------------------------------------------------------------------------
# FIGURE 3: Architecture Pipeline
# -------------------------------------------------------------------------
fig3_tex = r"""\documentclass[tikz,border=15pt]{standalone}
\usepackage{tikz}
\usepackage{amsmath}
\usepackage{amssymb}
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
    modulebox/.style={
        draw=#1Border, fill=#1Light!35, line width=1.2pt, rounded corners=10pt,
        blur shadow={shadow blur steps=5, shadow xshift=1.5pt, shadow yshift=-2pt, shadow opacity=15}
    },
    card/.style={
        draw=#1Border, fill=white, line width=0.9pt, rounded corners=5pt,
        align=center, inner sep=6pt
    },
    wire/.style={
        ->, line width=1.1pt, draw=#1Border
    }
]

% ==================== MODULE 1 ====================
\draw[modulebox=navy] (-0.3, -5.8) rectangle (6.4, 3.6);
\node[fill=navyBorder, text=white, font=\bfseries\sffamily\small, rounded corners=4pt, inner sep=4pt] at (3.05, 3.6) {Module 1: Atomization \& Triage};

\node[card=navy, minimum width=5.8cm, text width=5.5cm] (m1_in) at (3.05, 2.3) {
    \textbf{\color{navyDark} Unconstrained LLM Response}\\
    \scriptsize Multi-sentence generative text paragraph
};

\node[card=purple, below=0.8cm of m1_in, minimum width=5.8cm, text width=5.5cm] (m1_atom) {
    \textbf{\color{purpleDark} 5-Tuple Schema Atomizer}\\
    \scriptsize $\mathcal{T} = \langle S, P, O, T, M \rangle$\\
    \scriptsize + Forward Antecedent Anaphora Registry
};

\node[card=amber, below=0.8cm of m1_atom, minimum width=5.8cm, text width=5.5cm] (m1_router) {
    \textbf{\color{amberDark} Deterministic Modality Router}\\
    \scriptsize High-Speed Regex Parser ($<0.05\,\text{ms}$)\\
    \scriptsize $\mathcal{M} \in \{\text{Quant}, \text{Temp}, \text{Entity}, \text{Cite}, \text{Rel}\}$
};

\draw[wire=navy] (m1_in) -- (m1_atom);
\draw[wire=purple] (m1_atom) -- (m1_router);

% ==================== MODULE 2 ====================
\draw[modulebox=emerald] (7.2, -5.8) rectangle (15.2, 3.6);
\node[fill=emeraldBorder, text=white, font=\bfseries\sffamily\small, rounded corners=4pt, inner sep=4pt] at (11.2, 3.6) {Module 2: Domain-Specific Neuro-Symbolic ALUs};

\node[card=emerald, minimum width=7.0cm, text width=6.7cm] (alu_q) at (11.2, 2.3) {
    \textbf{\color{emeraldDark} Quantitative SI ALU} ($\Delta \le 5\%$ tolerance)\\
    \scriptsize Dimensional Unit Engine + World Bank / FRED API
};

\node[card=emerald, below=0.3cm of alu_q, minimum width=7.0cm, text width=6.7cm] (alu_t) {
    \textbf{\color{emeraldDark} Temporal ALU} (SPARQL Interval Containment)\\
    \scriptsize 2-Hop Wikidata Temporal Interval + Topological Bounds
};

\node[card=emerald, below=0.3cm of alu_t, minimum width=7.0cm, text width=6.7cm] (alu_e) {
    \textbf{\color{emeraldDark} Entity-Attribute ALU} (Statement Gate)\\
    \scriptsize SBERT Score-Commit ($s > 0.60$) + Alias Lexicon
};

\node[card=emerald, below=0.3cm of alu_e, minimum width=7.0cm, text width=6.7cm] (alu_c) {
    \textbf{\color{emeraldDark} Citation Registry ALU} (CrossRef Gateway)\\
    \scriptsize Live REST DOI Verification ($\text{Content} \ge 2$)
};

\node[card=slate, below=0.3cm of alu_c, minimum width=7.0cm, text width=6.7cm] (alu_r) {
    \textbf{\color{slateDark} Calibrated Relational NLI Fallback}\\
    \scriptsize DeBERTa-v3 Cross-Encoder ($\text{Margin} \ge \gamma$)
};

% Router to ALU Connectors
\draw[wire=amber] (m1_router.east) -- ++(0.35,0) |- (alu_q.west);
\draw[wire=amber] (m1_router.east) -- ++(0.35,0) |- (alu_t.west);
\draw[wire=amber] (m1_router.east) -- ++(0.35,0) |- (alu_e.west);
\draw[wire=amber] (m1_router.east) -- ++(0.35,0) |- (alu_c.west);
\draw[wire=amber] (m1_router.east) -- ++(0.35,0) |- (alu_r.west);

% ==================== MODULE 3 ====================
\draw[modulebox=purple] (16.2, -5.8) rectangle (23.2, 3.6);
\node[fill=purpleBorder, text=white, font=\bfseries\sffamily\small, rounded corners=4pt, inner sep=4pt] at (19.7, 3.6) {Module 3: Conjunction \& Output};

\node[card=purple, minimum width=6.0cm, text width=5.7cm] (dag) at (19.7, 1.2) {
    \textbf{\color{purpleDark} 3-Valued Conjunction DAG}\\
    \vspace{2pt}
    \scriptsize $\mathcal{V}_{\text{final}} = \mathcal{V}_1 \wedge \mathcal{V}_2 \wedge \dots \wedge \mathcal{V}_M$\\
    \vspace{3pt}
    \scriptsize \textbf{\color{crimsonBorder} Fatal Discrepancy Rule:}\\
    \scriptsize $\exists i: \mathcal{V}_i = \bot \implies \mathcal{V}_{\text{final}} = \texttt{FALSE}$
};

\node[card=emerald, below=1.2cm of dag, minimum width=6.0cm, text width=5.7cm] (decision) {
    \textbf{\color{emeraldDark} Calibrated Epistemic Verdict}\\
    \vspace{2pt}
    \scriptsize $\{\texttt{TRUE}, \texttt{FALSE}, \texttt{UNVERIFIABLE}\}$\\
    \vspace{3pt}
    \scriptsize \textbf{\color{emeraldDark}\checkmark 97.60\% Accuracy} $|$ \textbf{ECE 8.88\%}
};

% Direct Parallel Clean Connections into DAG
\draw[wire=emerald] (alu_q.east) -- ++(0.6,0) |- ($(dag.west) + (0, 0.4)$);
\draw[wire=emerald] (alu_t.east) -- ++(0.4,0) |- ($(dag.west) + (0, 0.2)$);
\draw[wire=emerald] (alu_e.east) -- (dag.west);
\draw[wire=emerald] (alu_c.east) -- ++(0.4,0) |- ($(dag.west) - (0, 0.2)$);
\draw[wire=slate] (alu_r.east) -- ++(0.6,0) |- ($(dag.west) - (0, 0.4)$);

\draw[wire=purple] (dag) -- (decision);

\end{tikzpicture}
\end{document}
"""

# -------------------------------------------------------------------------
# FIGURE 4: Dataset Lineage (No Hyphenation & Perfect Padding)
# -------------------------------------------------------------------------
fig4_tex = r"""\documentclass[tikz,border=15pt]{standalone}
\usepackage{tikz}
\usepackage{amsmath}
\usepackage{amssymb}
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
    trackbox/.style={
        draw=#1Border, fill=#1Light!30, line width=1.1pt, rounded corners=10pt
    },
    phasebox/.style={
        draw=#1Border, fill=white, line width=1.0pt, rounded corners=6pt,
        blur shadow={shadow blur steps=4, shadow xshift=1pt, shadow yshift=-1.5pt, shadow opacity=12},
        align=center, inner sep=6pt
    },
    wire/.style={
        ->, line width=1.2pt, draw=#1Border
    }
]

% ==================== TRACK 1: BENCHMARK CORPUS EVOLUTION ====================
\draw[trackbox=navy] (-0.5, 0.4) rectangle (25.2, 4.4);
\node[anchor=west, font=\bfseries\large, text=navyDark] at (0.0, 3.9) {Track 1: Benchmark Corpus Evolution (5 Sequential Forensic Phases)};

\node[phasebox=crimson, minimum width=4.2cm, text width=4.0cm] (p1) at (2.0, 2.0) {
    \textbf{\color{crimsonDark} Phase 1: Genesis}\\
    \scriptsize Batch 1 ($N=125$)\\
    \scriptsize 8 Gold FALSE (Skew)
};

\node[phasebox=amber, right=0.6cm of p1, minimum width=4.2cm, text width=4.0cm] (p2) {
    \textbf{\color{amberDark} Phase 2: Entity Gate}\\
    \scriptsize Phase 2 Gold ($N=126$)\\
    \scriptsize Bug B Relabeling
};

\node[phasebox=purple, right=0.6cm of p2, minimum width=4.2cm, text width=4.0cm] (p3) {
    \textbf{\color{purpleDark} Phase 3: Hard Negatives}\\
    \scriptsize Batch 3 ($N=206$)\\
    \scriptsize +84 Perturbations
};

\node[phasebox=slate, right=0.6cm of p3, minimum width=4.2cm, text width=4.0cm] (p4) {
    \textbf{\color{slateDark} Phase 4: Expansion}\\
    \scriptsize v2 ($N=731$) / v3 (2.1k)\\
    \scriptsize Macro \& Constants
};

\node[phasebox=emerald, right=0.6cm of p4, minimum width=4.8cm, text width=4.6cm] (p5) {
    \textbf{\color{emeraldDark} Phase 5: Master Benchmark}\\
    \scriptsize Symmetrical ($N=1,000$)\\
    \scriptsize \textbf{\color{emeraldDark}\checkmark 500 TRUE / 500 FALSE}
};

\draw[wire=crimson] (p1) -- (p2);
\draw[wire=amber] (p2) -- (p3);
\draw[wire=purple] (p3) -- (p4);
\draw[wire=slate] (p4) -- (p5);

% ==================== TRACK 2: MULTI-LLM ROAD TEST ====================
\draw[trackbox=purple] (-0.5, -4.2) rectangle (25.2, -0.2);
\node[anchor=west, font=\bfseries\large, text=purpleDark] at (0.0, -0.7) {Track 2: Open Generative Multi-LLM Road Test Matrix (7 Foundation Models)};

\node[phasebox=navy, minimum width=5.8cm, text width=5.5cm] (t2_prompts) at (3.0, -2.4) {
    \textbf{\color{navyDark} 50 Standardized Prompts}\\
    \vspace{2pt}
    \scriptsize 6 Technical \& Scientific Domains\\
    \scriptsize (Finance, Medicine, Physics, CS, Bio, Law)
};

\node[phasebox=purple, right=1.6cm of t2_prompts, minimum width=7.6cm, text width=7.3cm] (t2_models) {
    \textbf{\color{purpleDark} 7 Foundation Models (7B to 120B)}\\
    \vspace{2pt}
    \scriptsize Qwen 2.5 $\bullet$ Mistral $\bullet$ DeepSeek-R1\\
    \scriptsize Gemma 31B $\bullet$ GPT-OSS 120B $\bullet$ MiniMax M3 $\bullet$ Llama 3
};

\node[phasebox=emerald, right=1.6cm of t2_models, minimum width=6.2cm, text width=5.9cm] (t2_props) {
    \textbf{\color{emeraldDark} 1,798 Atomic Propositions}\\
    \vspace{2pt}
    \scriptsize $\bullet$ 31 Confirmed Hallucinations\\
    \vspace{2pt}
    \scriptsize \textbf{\color{emeraldDark}\checkmark 100\% Caught by HalDetect (31/31)}
};

\draw[wire=navy] (t2_prompts) -- (t2_models);
\draw[wire=purple] (t2_models) -- (t2_props);

\end{tikzpicture}
\end{document}
"""

# -------------------------------------------------------------------------
# FIGURE 5: Attention Dilution
# -------------------------------------------------------------------------
fig5_tex = r"""\documentclass[tikz,border=15pt]{standalone}
\usepackage{tikz}
\usepackage{amsmath}
\usepackage{amssymb}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning, calc, backgrounds, fit, shadows.blur}

\definecolor{navyDark}{HTML}{0B2545}
\definecolor{navyLight}{HTML}{F0F4F8}
\definecolor{navyBorder}{HTML}{134074}

\definecolor{crimsonDark}{HTML}{78281F}
\definecolor{crimsonLight}{HTML}{FDF2E9}
\definecolor{crimsonBorder}{HTML}{C0392B}

\definecolor{emeraldDark}{HTML}{0E6251}
\definecolor{emeraldLight}{HTML}{E8F8F5}
\definecolor{emeraldBorder}{HTML}{16A085}

\definecolor{slateDark}{HTML}{2C3E50}
\definecolor{slateLight}{HTML}{F8F9FA}
\definecolor{slateBorder}{HTML}{BDC3C7}

\begin{document}
\begin{tikzpicture}[
    font=\sffamily,
    >=Stealth,
    claimbox/.style={
        draw=slateBorder, fill=white, line width=1.0pt, rounded corners=6pt,
        blur shadow={shadow blur steps=4, shadow xshift=1pt, shadow yshift=-1.5pt, shadow opacity=12},
        align=left, inner sep=8pt
    },
    branchcard/.style={
        draw=#1Border, fill=#1Light!40, line width=1.2pt, rounded corners=8pt,
        blur shadow={shadow blur steps=5, shadow xshift=1.5pt, shadow yshift=-2pt, shadow opacity=15},
        align=left, inner sep=10pt
    },
    wire/.style={
        ->, line width=1.3pt, draw=#1Border
    }
]

% Claim & Ground Truth Boxes
\node[claimbox, text width=17.5cm] (claim) at (9.0, 4.6) {
    \textbf{\color{slateDark} Generated Model Assertion (Claim):}\\
    \textit{``The Apple M3 Max processor integrates \textbf{\color{crimsonBorder}40 million} transistors on a \textbf{\color{crimsonBorder}40nm} process node.''}
};

\node[claimbox, text width=17.5cm, below=0.4cm of claim] (ground) {
    \textbf{\color{slateDark} Retrieved Reference Ground Truth:}\\
    \textit{``The Apple M3 Max processor integrates \textbf{\color{emeraldBorder}92 billion} transistors on TSMC's \textbf{\color{emeraldBorder}3nm} process node.''}
};

% Left: Neural Cross-Encoder Failure Branch
\node[branchcard=crimson, text width=8.3cm, below left=1.2cm and 0.3cm of ground.south, anchor=north east] (left_box) {
    \textbf{\color{crimsonDark}\large Continuous Neural Cross-Encoder}\\
    \textbf{\color{crimsonBorder}\small (MiniCheck-7B / DeBERTa-v3)}\\
    \vspace{6pt}
    \small $\bullet$ \textbf{Attention Dilution Effect:}\\
    \quad $>85\%$ token overlap on semantic context\\
    \quad (\textit{Apple, M3, Max, processor, transistors}).\\
    \vspace{3pt}
    \small $\bullet$ Continuous cross-attention weights dominate the\\
    \quad isolated numerical magnitude mismatch.\\
    \vspace{6pt}
    \textbf{\color{crimsonDark}\large Verdict: ENTAILMENT (TRUE)}\\
    \vspace{2pt}
    \textbf{\color{crimsonBorder}\small $\times$ MISSED ERROR (0\% Recall on magnitude)}
};

% Right: Symbolic SI ALU Success Branch
\node[branchcard=emerald, text width=8.3cm, below right=1.2cm and 0.3cm of ground.south, anchor=north west] (right_box) {
    \textbf{\color{emeraldDark}\large HalDetect Type-Directed Symbolic ALU}\\
    \textbf{\color{emeraldBorder}\small (Dimensional Quantity Engine)}\\
    \vspace{6pt}
    \small $\bullet$ \textbf{Discrete Slot Extraction:}\\
    \quad Claim: $40\times 10^6$ \quad vs. \quad Truth: $92\times 10^9$.\\
    \vspace{3pt}
    \small $\bullet$ \textbf{Relative Error Calculus:}\\
    \quad $\Delta = \dfrac{|40\text{M} - 92\text{B}|}{92\text{B}} = 99.96\% > 5\%$.\\
    \vspace{6pt}
    \textbf{\color{emeraldDark}\large Verdict: CONTRADICTION (FALSE)}\\
    \vspace{2pt}
    \textbf{\color{emeraldDark}\small \checkmark 100\% ERROR RECALL (31/31 caught)}
};

\draw[wire=crimson] ($(ground.south) - (4.6, 0)$) -- (left_box.north);
\draw[wire=emerald] ($(ground.south) + (4.6, 0)$) -- (right_box.north);

\end{tikzpicture}
\end{document}
"""

diagrams = [
    ('fig1_triage_paradigm_upgraded', fig1_tex),
    ('fig3_architecture_pipeline_upgraded', fig3_tex),
    ('fig4_dataset_lineage_upgraded', fig4_tex),
    ('fig5_attention_dilution_upgraded', fig5_tex),
]

for name, code in diagrams:
    tex_path = os.path.join(out_dir, f"{name}.tex")
    with open(tex_path, "w") as f:
        f.write(code)
    print(f"Compiling {name}...")
    res = subprocess.run(["pdflatex", "-interaction=nonstopmode", f"{name}.tex"], cwd=out_dir, capture_output=True, text=True)
    if res.returncode == 0:
        for old in os.listdir(out_dir):
            if old.startswith(f"{name}_preview") and old.endswith(".png"):
                os.remove(os.path.join(out_dir, old))
        subprocess.run(["pdftoppm", "-png", "-r", "300", f"{name}.pdf", f"{name}_preview"], cwd=out_dir, check=True)
        print(f"  --> Built {name}.pdf & 300 DPI PNG successfully!")
    else:
        print(f"  --> Error compiling {name}: {res.stdout[-300:]}")

print("\nAll upgraded diagrams processed cleanly!")
