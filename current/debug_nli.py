#!/usr/bin/env python3
import os
import sys

def harden_native(threads: int = 1) -> None:
    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[var] = str(threads)
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

harden_native(1)

import torch
torch.set_num_threads(1)

print("Testing safe_nli directly...")
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

name = "cross-encoder/nli-deberta-v3-large"
print(f"Loading {name} with low_cpu_mem_usage=False...")
tok = AutoTokenizer.from_pretrained(name)
model = AutoModelForSequenceClassification.from_pretrained(
    name, low_cpu_mem_usage=False, dtype=torch.float32
)
model.eval()
nli = pipeline("zero-shot-classification", model=model, tokenizer=tok, device=-1)
print("Pipeline constructed successfully.")

premise = "Epyc is a brand of multi-core x86-64 microprocessors designed and sold by AMD."
hypothesis = "The AMD EPYC 9654 server processor features 96 Zen 4 CPU cores."

print("Running inference...")
res = nli(premise, candidate_labels=["entailment", "contradiction", "neutral"])
print("Inference result:", res)
