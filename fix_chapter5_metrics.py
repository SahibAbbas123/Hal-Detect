import re

c5 = "thesis_latex/Chapter5/chapter5.tex"
with open(c5, "r") as f: text = f.read()

replacement = (
    r"Non-Routed Baseline & 85.5\\% & 54.6\\% & 0.380 & - & - & - & - \\\\" + "\n" +
    r"Modern SOTA RAG & 100.0\\% & 52.1\\% & 0.380 & - & - & - & - \\\\" + "\n" +
    r"Semi-Routed Baseline & 74.2\\% & 51.7\\% & 0.380 & - & - & - & - \\\\" + "\n" +
    r"\\textbf{HalDetect 2.0 (Evolved)} & \\textbf{9.3\\%} & \\textbf{60.2\\%} & \\textbf{0.510} & \\textbf{-} & \\textbf{-} & \\textbf{-} & \\textbf{-} \\\\" + "\n" +
    r"\\bottomrule"
)

text = re.sub(
    r"Non-Routed Baseline.*?\\bottomrule",
    replacement,
    text, flags=re.DOTALL
)

with open(c5, "w") as f: f.write(text)
