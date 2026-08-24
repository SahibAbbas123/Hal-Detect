---
name: thesis-latex-tables
description: Use when writing or revising the HalDetect thesis in LaTeX — Chapter 4 results, any results/comparison table, a per-type breakdown, a taxonomy table, or the bibliography. Triggers on producing a .tex table from verifier output, typesetting accuracy/coverage/F1/MCC figures, or compiling the thesis. Encodes the toolchain actually installed on this machine and the reporting conventions a reviewer will attack if they are missing.
---

# Thesis LaTeX: tables that survive review

Load `report-metrics-honestly` alongside this. That skill decides **which** numbers are
reportable; this one decides how they are **typeset**. A correctly formatted table of
indefensible numbers is still indefensible.

## Toolchain actually present (verified 2026-08-25)

| present | missing |
|---|---|
| `pdflatex` `xelatex` `lualatex` `latexmk` `bibtex` `texfot` `chktex` `gs` `tesseract` | **`biber`** **`latexdiff`** **`pandoc`** **`pdftoppm`** |

TeX Live is via Homebrew (`/opt/homebrew/bin`). Consequences:

- **Use `bibtex`, not `biber`.** With biblatex you must write
  `\usepackage[backend=bibtex,style=numeric]{biblatex}`, or just use plain `\bibliography{refs}`.
  A default `\usepackage{biblatex}` assumes biber and **will fail**.
- Compile with `latexmk -pdf main.tex` (add `-xelatex` only if you need system fonts).
  Filter noise with `texfot latexmk -pdf main.tex`.
- Lint before committing a chapter: `chktex -q main.tex`.
- No `pandoc`, so there is no Markdown/DOCX bridge — author `.tex` directly.
- `pdf2image` is installed in `.venv-pdf` but needs poppler's `pdftoppm`, which is **missing**;
  `brew install poppler` if PDF→PNG is ever needed. `pdfplumber` works without it.

There is no `.tex` or `.bib` in the repo yet — the thesis has not been started here.

## Preamble for results tables

```latex
\usepackage{booktabs}   % \toprule \midrule \bottomrule -- never \hline, never vertical rules
\usepackage{siunitx}    % decimal alignment
\usepackage{threeparttable}
\sisetup{table-number-alignment = center, detect-weight = true}
```

Align every numeric column with `S`, so decimal points line up:
`\begin{tabular}{l S[table-format=2.1] S[table-format=2.1]}`. Wrap headers in `{}` to stop
`siunitx` parsing them as numbers. Percent signs must be escaped (`88.2\%`) or moved to the
header (`Accuracy (\%)`) — the header is better, it removes 30 escapes from a table body.

## The four things a reviewer checks, and where they go

1. **Coverage sits next to accuracy, in the same row.** An accuracy without its coverage is
   unreadable — `ct >= 0.65` reached 92.5% while catching **0 of 13** negatives.
2. **Effective n**, as its own column. It is `coverage x n`, not `n`.
3. **A baseline row inside the table**, not in the prose. Always-True is **88.2%**, and the
   non-routed baseline's 69.8% is *18pp below it*. A table whose top row is a system beaten by
   a constant needs that constant visible.
4. **The interval on anything at or near 100%.** Never a bare `100`. Write `100.0` with its
   Wilson CI in the adjacent column; `5/5` is `[56.6, 100]`.

Put the caveat in a `tablenotes`, not a footnote — it travels with the table:

```latex
\begin{threeparttable}
\begin{tabular}{l S[table-format=2.1] S[table-format=2.1] c S[table-format=1.3] r}
\toprule
System & {Cov.\ (\%)} & {Sel.\ acc.\ (\%)} & {95\% CI} & {F1(False)} & {Eff.\ $n$} \\
\midrule
Non-routed, 3d-style  & 77.2 & 69.8 & [64.2, 74.9] & 0.170 & 275 \\
Non-routed, 3e-style  & 53.7 & 81.2 & [75.0, 86.1] & 0.174 & 191 \\
\midrule
\textit{Always-True}  & 100.0 & 88.2 & [84.4, 91.2] & 0.000 & 356 \\
\bottomrule
\end{tabular}
\begin{tablenotes}\footnotesize
\item Pooled gold: 314 True / 13 False / 29 Unverifiable ($n=356$). Always-True is the
  majority-class constant; it attains the highest accuracy while detecting nothing, which is
  why F1(False) is the operative column.
\end{tablenotes}
\end{threeparttable}
```

## Widths, measured — don't chase a phantom overfull

The 6-column results table above was compiled and measured on this machine:

| layout | textwidth | table width | result |
|---|---|---|---|
| `report`, a4, `margin=1in` (thesis) | **452.97pt** | 397.64pt | **fits, 55pt spare** |
| `article` 11pt, default margins | 360.00pt | 397.64pt | overfull by 37.6pt |

At `\small` it is 369.39pt, at `\footnotesize` 347.12pt. So **the table is correct for a
thesis layout and needs no shrinking** — but if you test it in a scratch `article` file you will
be told it is overfull, and that warning does not apply to the thesis. Set the real geometry
before believing any overfull report, and don't reach for `\resizebox` (it desynchronises font
size from the body text and is the usual reason thesis tables look wrong).

## Report 3d and 3e side by side — that is a settled decision

Not one or the other. Coverage is what RQ4 measures, accuracy is what RQ2 compares, and the
**shape of the trade-off is itself a finding** (a stable -22pp coverage for +12pp accuracy).
One row per variant, or paired columns under a `\multicolumn` group:

```latex
\begin{tabular}{l S S S S}
\toprule
& \multicolumn{2}{c}{Phase 3d} & \multicolumn{2}{c}{Phase 3e} \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}
Type & {Cov.} & {Acc.} & {Cov.} & {Acc.} \\
\midrule
Relational & 77.0 & 66.4 & 52.3 & 79.1 \\
\bottomrule
\end{tabular}
```

Cell 57 — the live code — runs a **third** regime (0.55/0.45, margin 0.15) that no results table
scores. If a table is labelled "3e", say which thresholds it means.

## Two things that must appear in the text, not silently in a number

- **Phase 2 twice.** 109 of 356 verdicts are AI-filled. Print pooled results with and without
  Phase 2; if they diverge, the pooled figure is not quotable.
- **In-sample-selected operating points, flagged as such.** The (0.35/0.30) optimum was chosen
  by max-MCC over 225 grid points on the same rows it is scored on.

## Style

- `\midrule` to separate baselines from systems; never a vertical rule.
- Bold the winner only if you also bold it in every comparable table.
- Refer to types in small caps (`\textsc{Relational}`) and keep it consistent — the taxonomy is
  the contribution, so its five names are proper nouns.
- Never let a table cross a page without `\caption` repetition; use `longtable` for the
  per-claim appendix, `tabular` for everything in Chapter 4.
