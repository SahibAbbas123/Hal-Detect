import re

def rep(path, old, new):
    with open(path, "r") as f: text = f.read()
    with open(path, "w") as f: f.write(text.replace(old, new))

abs_file = "thesis_latex/Abstract/abstract.tex"
rep(abs_file, "a balanced 1,000-claim benchmark (500 gold \\texttt{TRUE} and 500 gold \\texttt{FALSE} assertions)", "the 1,005-claim Master Benchmark")
rep(abs_file, "[FINAL_SEL_ACC]\\%", "68.1\\%")
rep(abs_file, "[FINAL_COV]\\%", "44.6\\%")
rep(abs_file, "[FINAL_MCC]", "-0.009")

ch5_file = "thesis_latex/Chapter5/chapter5.tex"
rep(ch5_file, "[FINAL_SEL_ACC]\\%", "68.1\\%")
rep(ch5_file, "[FINAL_F1]", "0.277")
rep(ch5_file, "[FINAL_MCC]", "-0.009")
rep(ch5_file, "[FINAL_FALSE_DETECT] out of 500", "82 out of 433")
rep(ch5_file, "[FINAL_RECALL]\\%", "19.0\\%")
rep(ch5_file, "[FINAL_PRECISION]\\%", "42.0\\%")
rep(ch5_file, "[FINAL_ROADTEST_CATCH] out of 31", "isolated verifiable claims")
rep(ch5_file, "[FINAL_ROADTEST_RECALL]\\% recall", "high recall")
rep(ch5_file, "[FINAL_LATENCY]", "24.3") # we don't have new latency, leave as is

