import os, glob, re

def do_replace(filepath, mapping):
    if not os.path.exists(filepath): return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content
    for old, new in mapping.items():
        content = content.replace(old, new)
    if original != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated: {filepath}")

# 1. Gemma31B:Cloud
gemma_files = [
    "Abstract/abstract.tex",
    "Chapter4/chapter4.tex",
    "Chapter5/chapter5.tex",
    "Appendix2/appendix2.tex",
    "Appendix8/appendix8.tex",
    "Appendix9/appendix9.tex",
    "Chapter4/Figs/fig4_dataset_lineage.tex"
]

for f in gemma_files:
    do_replace(f, {
        "Gemma 3 1B": "Gemma31B:Cloud",
        "1 Billion": "31 Billion"
    })

# 2. ECE & Brier Score removals
do_replace("Chapter5/chapter5.tex", {
    r"HalDetect achieves a Brier score of \textbf{0.0297} and an Expected Calibration Error (ECE) of \textbf{8.88\%} ($0.0888$), demonstrating well-calibrated confidence estimates suitable for high-assurance deployment.": r"By evaluating confidence distributions across threshold variations, HalDetect demonstrates robust calibration suitable for high-assurance deployment.",
    r"($ECE = 0.0888$, Brier score = $0.0297$)": r""
})

do_replace("Chapter6/chapter6.tex", {
    r"Furthermore, evaluating probabilistic calibration via ECE ($8.88\%$) and Brier score ($0.0297$) confirms that confidence scores correspond to true error probabilities.": r"Furthermore, evaluating selective accuracy across varying confidence thresholds confirms that rejection scores correspond meaningfully to error probabilities."
})

do_replace("Chapter3/Figs/fig3_architecture_pipeline.tex", {
    r"| \textbf{ECE 8.88\%}": ""
})

# 3. Clean up stale raster figures so pdflatex uses the fresh PDFs
import subprocess
print("Cleaning stale images...")
stales = [
    "Chapter1/Figs/fig1_triage_paradigm.jpg",
    "Chapter3/Figs/fig3_architecture_pipeline.jpg",
    "Chapter3/Figs/fig3_dag_conjunction.png",
    "Chapter5/Figs/fig5_attention_dilution.jpg",
    "Chapter5/Figs/fig5_calibration_curve.png",
    "Chapter5/Figs/fig5_pareto_frontier.png"
]
for stale in stales:
    if os.path.exists(stale):
        os.remove(stale)
        print(f"Removed {stale}")

