import re

with open("thesis_latex/Chapter5/chapter5.tex", "r") as f:
    text = f.read()

# Add Youden's J to Table 5.1
target_table = r"""\begin{tabular}{lcccccc}
\toprule
\textbf{Architecture} & \textbf{Coverage} & \textbf{Selective Acc.} & \textbf{Precision(F)} & \textbf{Recall(F)} & \textbf{MCC} & \textbf{Latency} \\
\midrule
Non-Routed Baseline & 100.0\% & 60.00\% $\pm$ 3.0\% & 0.582 & 0.702 & +0.260 & 450.0 ms \\
Modern SOTA RAG & 100.0\% & 69.20\% $\pm$ 2.8\% & 0.654 & 0.550 & +0.400 & 578.5 ms \\
Semi-Routed Baseline & 100.0\% & 73.60\% $\pm$ 2.7\% & 0.742 & 0.724 & +0.473 & 185.0 ms \\
\textbf{HalDetect 2.5 (Evolved)} & \textbf{100.0\%} & \textbf{97.60\% $\pm$ 0.9\%} & \textbf{0.974} & \textbf{0.978} & \textbf{+0.952} & \textbf{24.3 ms} \\
\bottomrule
\end{tabular}"""

new_table = r"""\begin{tabular}{lccccccc}
\toprule
\textbf{Architecture} & \textbf{Coverage} & \textbf{Selective Acc.} & \textbf{Precision(F)} & \textbf{Recall(F)} & \textbf{MCC} & \textbf{Youden's J} & \textbf{Latency} \\
\midrule
Non-Routed Baseline & 100.0\% & 60.00\% $\pm$ 3.0\% & 0.582 & 0.702 & +0.260 & 0.200 & 450.0 ms \\
Modern SOTA RAG & 100.0\% & 69.20\% $\pm$ 2.8\% & 0.654 & 0.550 & +0.400 & 0.384 & 578.5 ms \\
Semi-Routed Baseline & 100.0\% & 73.60\% $\pm$ 2.7\% & 0.742 & 0.724 & +0.473 & 0.472 & 185.0 ms \\
\textbf{HalDetect 2.5 (Evolved)} & \textbf{100.0\%} & \textbf{97.60\% $\pm$ 0.9\%} & \textbf{0.974} & \textbf{0.978} & \textbf{+0.952} & \textbf{0.952} & \textbf{24.3 ms} \\
\bottomrule
\end{tabular}"""

text = text.replace(target_table, new_table)

with open("thesis_latex/Chapter5/chapter5.tex", "w") as f:
    f.write(text)
