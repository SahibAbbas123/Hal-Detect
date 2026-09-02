path = "thesis_latex/Chapter5/chapter5.tex"
with open(path, "r") as f: text = f.read()

# Replace 97.60% occurrences
text = text.replace("97.60\\%", "[FINAL_SEL_ACC]\\%")
text = text.replace("0.976", "[FINAL_F1]")
text = text.replace("+0.952", "[FINAL_MCC]")
text = text.replace("489 out of 500", "[FINAL_FALSE_DETECT] out of 500")
text = text.replace("97.80\\%", "[FINAL_RECALL]\\%")
text = text.replace("97.41\\%", "[FINAL_PRECISION]\\%")
text = text.replace("31 out of 31", "[FINAL_ROADTEST_CATCH] out of 31")
text = text.replace("100.0\\% recall", "[FINAL_ROADTEST_RECALL]\\% recall")
text = text.replace("24.3 ms", "[FINAL_LATENCY] ms")

with open(path, "w") as f: f.write(text)
