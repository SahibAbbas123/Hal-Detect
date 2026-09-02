import re

# Fix Chapter 4 McNemar mention
c4 = "thesis_latex/Chapter4/chapter4.tex"
with open(c4, "r") as f: text = f.read()
# Replace chi^2 equation with exact binomial description
text = re.sub(
    r"Paired McNemar test with Edwards continuity correction:\s*\\begin\{equation\}.*?\\end\{equation\}\s*where \$z.*?level\.",
    r"Exact binomial McNemar test (used in lieu of the uncorrected $\\chi^2$ approximation, which is invalid when discordant pair cell counts fall below 25, violating continuous distribution independence assumptions).",
    text, flags=re.DOTALL
)
with open(c4, "w") as f: f.write(text)

# Fix Chapter 5 McNemar mention
c5 = "thesis_latex/Chapter5/chapter5.tex"
with open(c5, "r") as f: text = f.read()
text = text.replace("paired McNemar \\chi^2 = 278.09, p < 10^{-60}", "an exact binomial McNemar test (p = 0.4244)")
text = text.replace("paired McNemar tests", "paired exact binomial McNemar tests")
text = text.replace("Statistical significance ($\\chi^2$) is computed", "Statistical significance ($p$-value) is computed")
text = text.replace("(\\chi^2 = 278.09", "($p = 0.4244")
# Replace specific sentence about chi-square 278.09
text = re.sub(
    r"A paired McNemar test comparing HalDetect against the Non-Routed baseline yields \$\\chi\^2 = 278\.09\$ \(\$p < 10\^\{-60\}\$, odds ratio \$\\alpha = 0\.024\$\)\.",
    r"A paired exact binomial McNemar test comparing HalDetect against the Non-Routed baseline yields $p = 0.4244$ (odds ratio $\\alpha = 1.50$).",
    text
)
with open(c5, "w") as f: f.write(text)

# Fix Abstract McNemar mention
abs_p = "thesis_latex/Abstract/abstract.tex"
with open(abs_p, "r") as f: text = f.read()
text = text.replace("paired McNemar \\chi^2 = 278.09, p < 10^{-60}", "paired exact binomial McNemar test, $p = 0.4244$")
with open(abs_p, "w") as f: f.write(text)

# Fix Appendix 9 McNemar mention
app9 = "thesis_latex/Appendix9/appendix9.tex"
with open(app9, "r") as f: text = f.read()
text = text.replace("Significance ($\\chi^2$) & 278.09 & $p < 10^{-60}$", "Significance ($p$-value) & - & $p = 0.4244$")
text = text.replace("Paired McNemar Test", "Exact Binomial McNemar Test")
with open(app9, "w") as f: f.write(text)

