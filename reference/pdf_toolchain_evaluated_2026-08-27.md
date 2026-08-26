# Four PDF tools evaluated — all four declined, and the capability was already installed

**Date:** 2026-08-27 · **Trigger:** the author supplied four candidate tools and a conditional
authorization — *"any of these seem helpful? if token-friendly themselves, install globally"*.

> **Provenance.** Everything below was measured on this machine against
> `papers_analysis/downloaded_pdfs/`. **Zero API calls, zero model calls, zero web requests.**
> One package (`pymupdf` 1.28.2) was installed into the main checkout's `.venv`, tested, and
> **uninstalled**; the venv is verified back to baseline (§5). No thesis number is touched by
> anything here.

---

## 0. The verdict, and the reason it is not the interesting part

| # | tool | verdict | the measured reason |
|---|---|---|---|
| 1 | **`pymupdf4llm`** | **DECLINED** as a stack; **core tested and REMOVED** | The wrapper hard-requires `pymupdf_layout==1.28.2`, which pulls **onnxruntime 1.29.0 + protobuf 7.36.0 + flatbuffers + tabulate** — **7 new packages** into a `.venv` running torch 2.12 / transformers 5.9. The zero-dependency core (`pymupdf` alone, **1 package, requires NONE**) *was* installed and measured, and it **lost to the already-installed `pdftotext`** on this corpus — §2. |
| 2 | **`marker`** | **DECLINED** | Multi-GB Surya model weights. Its edge is **scanned / OCR'd** documents; **all 42 files here are born-digital** with an embedded text layer — demonstrated, not assumed: `pdftotext` returns clean text for every one of the 42 (that sweep is what found the 5 wrong papers). Paying GB of weights for OCR on documents that need no OCR. |
| 3 | **`Docling`** | **DECLINED, held as escalation** | 0.5–1 GB weights for layout/table models. Same born-digital argument. **Reconsider only if a specific table resists BOTH `pdftotext` modes** — that has not happened yet on any of the 42. |
| 4 | **`pdf-mcp`** | **DECLINED — and it fails the author's own criterion** | An MCP server's tool schemas are injected into **every session's** context whether a PDF is opened or not. That is a **standing per-session token cost** — the opposite of token-friendly — bought for a capability that is **already free via Bash**. The criterion was *"if token-friendly themselves"*, and a resident tool schema is the one form of cost that cannot be sliced or avoided. |

**None of the four is installed. The finding that matters is §1: the capability already existed
and was being called the wrong way.**

---

## 1. THE ACTUAL FINDING — mode choice beats tool choice, and the two modes are opposites

`pdftotext` has two text modes and **they fail in opposite directions on a two-column paper.**
This was measured on `FinGround_FinancialFactuality_2024.pdf` (14 pp, ACL two-column) and
`SemanticEntropy_Nature_2024.pdf` (12 pp, Springer).

| mode | on two-column **prose** | on **tables** |
|---|---|---|
| **default ("flow")** | **CORRECT.** Reconstructs reading order; a paragraph spanning a column break comes out as one paragraph. | Collapses alignment — column structure lost. |
| **`-layout`** | **MANGLED.** Preserves *physical* position, so the left and right columns interleave **line by line**. FinGround p9 came out as the bibliography and the appendix body braided together. | **NEAR-PERFECT.** Aligned columns, values intact, readable as-is. |

**The rule: flow for prose, `-layout` for tables, and never the reverse.**

This is not academic. The `-layout` interleave is what produced the earlier garbled read
`"attribution without / tilled detector retains 91.4% F1 at 18× lower / structure-aw"` — three
different columns spliced into one line, which is exactly the shape of a misquotation. **A tool
that silently braids two columns together is more dangerous than one that fails**, because the
output is fluent.

### Page slicing works, and it is the whole token story

`-f N -l N` genuinely slices — verified by distinct per-page content and per-page char counts
(FinGround: 7558 / 5869 / 6406 / 1387 chars on pp. 1 / 3 / 7 / 14). **A 14-page paper read whole
is roughly 10–15k tokens; one page is 1.4–7.6k characters.** So **token-friendliness is a property
of how a PDF tool is CALLED, not of which tool it is** — which is why "install a better extractor
to save tokens" was the wrong frame from the start. **Slice by page. Never dump a whole paper.**

### A false alarm worth recording as method

`"91.4"` appeared on **12 of 14** pages, which looked like page slicing silently ignoring its
range. It was not: the number genuinely recurs (abstract, results, appendix). **But the check was
right to run** — a page-scan result is worthless until slicing is proven to slice, and the proof
is distinct content per page, not a plausible-looking hit list.

---

## 2. The measured negative result on `pymupdf.find_tables()` — the load-bearing part

This is the one claim that could otherwise be re-litigated forever, so it was tested rather than
argued. Target: **FinGround p6**, which carries Tables 2–5 including the main end-to-end results
table — the page where `pdftotext -layout` produced aligned, intact output (`34.7±1.8`,
`68.2±1.4`, … all correct, 9 system rows × 8 numeric columns).

| `find_tables(strategy=…)` | tables found | quality |
|---|---|---|
| default (`lines`) | **0** | nothing, plus a nag: *"Consider using the pymupdf_layout package for a greatly improved page layout analysis."* |
| `lines_strict` | **0** | nothing |
| `text` | 1 | **garbage** — a **63-row × 6-column** grid for a 9-row table; `34.7±1.8` **split across two cells** (`'34.7±'` / `'1.8'`); three source columns merged into one (`'71.4±1.2 43.8±4.1 52'`) |

**Why it fails, and why the failure generalises to this whole corpus:** ACL/`booktabs` tables are
**borderless** — horizontal rules only, often no vector lines at all — so every ruling-line
strategy finds nothing, and the text strategy has to guess column boundaries against `±`-joined
values and guesses wrong. **The corpus is almost entirely ACL/arXiv preprints, so this is the
common case here, not an edge case.**

**And the vendor's own fix is the dependency that was declined:** the nag points at
`pymupdf_layout`, i.e. onnxruntime + protobuf 7.x. So the choice is not "1 package vs 7" — it is
**"7 packages to maybe reach parity with a binary already on the machine."**

**The genuinely hardest case also passes without it.** `SemanticEntropy_Nature_2024.pdf` p4
Table 1 is a 5-column Springer table with **multi-line wrapped cells**; `pdftotext -layout`
renders it readably (question / model answer / reference answer / generations / prediction all
separable). If poppler survives that, the table gap this install was meant to close does not
exist for **reading and quoting** purposes.

**Scope of the claim, stated precisely:** `find_tables` is worse *for this corpus and for my use*,
which is **reading numbers in order to quote them** — not parsing tables into typed data. A
project needing machine-readable cells might still want a layout model. Nothing here says
PyMuPDF is a bad library; it says **it loses to the incumbent on borderless academic tables, and
the incumbent is already installed.**

---

## 3. Two collateral corrections to the existing record

**(a) FinGround's granularity ablation is PROSE, not a table, and it is on page 9 — not page 3.**
The earlier note placed it near `"Appendix A"` (p3). The numbers live in **Appendix A on p9**,
extracted verbatim in flow mode:

> **Granularity.** We compare against a 3-type taxonomy (Numerical, Textual, Derived) and a
> 10-type taxonomy. The 6-type achieves 91.4% F1; the 3-type achieves 87.1% (−4.3, p < 0.01);
> the 10-type achieves 91.7% (+0.3, p = 0.23), supporting the 6-type as the preferred
> accuracy-complexity trade-off.

**All five figures CLAUDE.md §7 quotes reproduce exactly** (91.4 / 87.1 / −4.3, p<0.01 / 91.7 /
+0.3, p=0.23). **And the paper's own closing clause independently vindicates the REGIME framing:**
it claims *"the preferred accuracy-complexity trade-off"* for **its own 6 types** — it never
claims a global optimum, and never tests 5. So §7's refusal to write *"this proves 5 is optimal"*
is the paper's own position, not a hedge added on top of it.

**(b) A page-count-free way to find any paper's tables**, worth keeping because it costs one call:
`re.findall(r'Table \d+[:.]', …)` per page over `-layout` output. FinGround's tables are on pp.
4, 6, 10–13; the Nature paper's on pp. 2 and 4; R-Tuning's across pp. 5–9 and 14–20. Cheaper than
reading to find out.

---

## 4. Why "install globally" was not done literally

Homebrew's python is **PEP 668 externally-managed**, so a literal global `pip install` requires
`--break-system-packages`, which is not something to do to the system interpreter for an analysis
convenience. `pipx` is the correct tool for a global **CLI**, but every candidate here is a
**library**, so pipx does not apply. **The project `.venv` is where all analysis runs and is the
only correct target** — and that is where the `pymupdf` test was performed and reversed.

One note kept for the future: **PyMuPDF is AGPL-3.0.** Fine for an offline analysis tool; worth
not importing from any verifier module that ships with the thesis.

---

## 5. Reverse commands and the baseline proof

Nothing needs reversing — the one install was already reversed — but per the standing
*"keep track in case we need to take a few steps back"* rule:

```
# what was done, and undone:
.venv/bin/python -m pip install pymupdf      # -> pymupdf-1.28.2, 1 package, 0 deps pulled
.venv/bin/python -m pip uninstall -y pymupdf # -> "Successfully uninstalled pymupdf-1.28.2"
```

**Baseline verified restored, not assumed:**

```
.venv/bin/python -c "
import importlib.util as u, torch, transformers, sentence_transformers, pypdf
print('pymupdf:', u.find_spec('pymupdf') is not None, 'fitz:', u.find_spec('fitz') is not None)
print(torch.__version__, transformers.__version__, sentence_transformers.__version__, pypdf.__version__)"
# -> pymupdf: False  fitz: False
# -> 2.12.0 5.9.0 5.5.1 6.16.1
.venv/bin/python -m pip list | grep -ci -e pymupdf -e onnx -e protobuf -e tabulate   # -> 0
```

Note the second check exists because the first is not sufficient: `find_spec` answers about two
import names, while the `grep -c 0` answers about the **onnxruntime/protobuf closure** that was
the actual reason for declining option 1.

---

## 6. Reproduce §1 and §2

```
# §1 — the two modes are opposites (flow reads correctly, -layout braids the columns)
python3 -c "
import subprocess
f='papers_analysis/downloaded_pdfs/FinGround_FinancialFactuality_2024.pdf'
for tag,fl in [('FLOW',[]),('LAYOUT',['-layout'])]:
    o=subprocess.run(['pdftotext','-f','9','-l','9']+fl+[f,'-'],capture_output=True,text=True).stdout
    i=o.find('Granularity'); print('='*20,tag,len(o)); print(o[max(0,i-300):i+500])"

# §2 — find_tables loses to -layout on the same page (needs a temporary pymupdf install)
.venv/bin/python -c "
import pymupdf
pg=pymupdf.open('papers_analysis/downloaded_pdfs/FinGround_FinancialFactuality_2024.pdf')[5]
for s in ['lines','text','lines_strict']:
    t=pg.find_tables(strategy=s).tables
    print(s,'->',len(t),'tables', [(len(x.extract()),len(x.extract()[0])) for x in t])"
```

The `-layout` output for that same page 6 is the comparison baseline and needs no install.

---

## 7. What this changes

**No measured thesis number moves.** No verifier, CSV, cache prefix, or result file was touched;
the only environment change was made and reversed. What changes is the **PDF reading protocol**,
recorded compactly in CLAUDE.md §7: flow for prose, `-layout` for tables, slice by page, and
**tier 1 still requires reading the title off page 1** before quoting a file
(`reference/papers_analysis_assessed_2026-08-27.md` §1a — 5 of the 42 files are the wrong paper).

**The reusable lesson is the same shape as R1.** The install request assumed a missing capability.
The capability was present; what was missing was knowing that its two modes fail in opposite
directions. **Before buying a tool to close a gap, measure the gap against the tool already
installed** — here the incumbent won on the exact page the challenger was bought for.
