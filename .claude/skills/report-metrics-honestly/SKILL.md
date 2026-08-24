---
name: report-metrics-honestly
description: Use whenever reporting, tabulating, or interpreting any HalDetect evaluation number — accuracy, coverage, precision/recall/F1, MCC, AURAC — or writing a results table for the thesis. Triggers on running a verifier's --diagnose, comparing routed vs non-routed, quoting a per-type figure, or writing any percentage into CLAUDE.md, WORKLOG, or Chapter 4. Encodes the class-imbalance trap and the confidence-interval rules this project has already been burned by.
---

# Report metrics honestly

Use `current/metrics.py` — it implements all four rules and prints the baselines next to
every result, so the comparison cannot be skipped.

## 1. Accuracy is the wrong headline. Always print the baselines.

Pooled gold is **314 TRUE / 13 FALSE / 29 UNVERIFIABLE of 356**, so an unconditional "TRUE"
scores **88.2%** [84.4%, 91.2%] with F1(FALSE) = 0.00 and MCC = 0.000. On Batch 3 alone it
scores 94.3%.

The non-routed baseline scores **69.8%** — *18pp below* Always-True. Any table that leads with
accuracy is trivially attacked.

**Lead with F1(FALSE) and MCC.** Quote accuracy only next to Always-True / Always-False /
Random, and never without coverage.

## 2. Never write a bare 100% — compute the Wilson interval

Every 100% in this project was audited and several could not carry the weight put on them:

| claim | k/n | 95% CI | verdict |
|---|---|---|---|
| RELATIONAL precision | 36/36 | [90.4%, 100%] | holds |
| QUANTITATIVE accuracy | 8/8 | [67.6%, 100%] | n too small |
| tier-1 Wikidata, Batch 3 | 5/5 | **[56.6%, 100%]** | meaningless as "100%" |
| tier-1, negatives | 2/2 | **[34.2%, 100%]** | meaningless |

`5/5` has a lower bound of **56.6%** — barely better than a coin flip — and had been quoted as
the strongest evidence for the tiering argument. Write `5/5 [56.6%, 100%]`, never "100%".

```bash
.venv/bin/python -c "
import sys,math
k,n=int(sys.argv[1]),int(sys.argv[2]); z=1.959963985
p=k/n; d=1+z*z/n
c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
print(f'{k}/{n} = {100*p:.1f}%  95% CI [{100*max(0,c-h):.1f}%, {100*min(1,c+h):.1f}%]')
" <k> <n>
```

## 3. Effective n is `coverage x dataset n`, not dataset n

RELATIONAL's "80.77%" rested on ~26 covered claims → CI [62.1%, 91.5%], which **cannot
separate 80% from 65%**. Pooling to 174 routed claims gave 79.1% @ 52.3% on 91 covered and
tightened it to ~±8pp. **Never quote accuracy without coverage and effective n.**

An accuracy that climbs while coverage falls is not an improvement. In the threshold sweep,
`ct >= 0.65` reached **92.5% accuracy while catching 0 of 13 negatives** — purely by
abstaining.

## 4. Coverage up + precision down is the project's signature regression

It has happened twice: the property resolver's first pass hit 47.1% coverage at ~31%
precision, re-introducing ~11 confident-wrong verdicts. **Coverage is not correctness.**
A `--diagnose` coverage figure far *above* its predicted band is a warning, not a win.

Conversely, honest UNVERIFIABLE beats a confident-wrong verdict. Post-QID-fix TEMPORAL/EA
produce zero confident-wrong verdicts on Batch 3.

## 5. Never merge gold UNVERIFIABLE with predicted UNVERIFIABLE

Gold = not checkable in principle. Predicted = couldn't reach evidence. A confident verdict on
a gold-UNVERIFIABLE claim is an **error, not a hit**.

## 6. Where gold negatives don't exist, measure discrimination by perturbation

**13 gold negatives across 356 claims is the binding constraint on every detection claim in
the thesis.** TEMPORAL and EA have zero negatives in Batch 3; EA's MCC is 0.000 everywhere,
so its 97.4% accuracy is uninformative *by construction*.

Accuracy on a zero-negative slice is not evidence. Use controlled perturbation instead —
`quantitative_verifier.py --sensitivity` is the model: **8/8 flip TRUE→FALSE at ≤1% claimed-value
change, median 1%, nothing flips inside the 0.5% tolerance.** That is genuine discrimination
and the project's first validated detection result.

## 7. Report Phase 2 twice, and say which

109 of 356 verdicts rest on AI-filled labels. The 31 highest-risk flips were reviewed against
primary sources and all confirmed TRUE, but 45 fills + 33 unchanged remain unreviewed. Print
every pooled result **both with and without Phase 2**; if they diverge, the pooled figure is
not quotable. (Robustness check passed once already: all-labeled 69.8% vs human-only 71.6%.)

## 8. Don't quote per-type tuned thresholds

The per-type optima were selected by max-MCC over 225 grid points **on the same rows they are
scored on**, with only 13 negatives total. Three findings *are* stable: QUANTITATIVE wants
strict contradiction (0.50), CITATION permissive (0.30), and **CITATION has negative MCC at
the shipped threshold** (−0.115) — worse than chance.

Flag any in-sample-selected operating point as such.
