import json
import time
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="nli_rescore_worklist_both.json")
    parser.add_argument("--output", default="nli_rescore_scores_both_deberta.json")
    args = parser.parse_args()

    # Load worklist
    print(f"Loading {args.input}...")
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    meta = data["meta"]
    items = data["items"]
    
    # Generate unique pairs
    pairs = []
    seen = set()
    for row in items:
        claim = row["claim"]
        passage = row["passage"]
        # The key format is usually claim + "|||" + passage
        key = claim + "|||" + passage
        if key not in seen:
            pairs.append((claim, passage, key))
            seen.add(key)
            
    print(f"Found {len(items)} rows, resolving to {len(pairs)} unique premise-hypothesis pairs.")

    # Load DeBERTa
    model_name = "cross-encoder/nli-deberta-v3-large"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading {model_name} on {device}...")
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name).to(device)
    model.eval()

    # Score
    scores = {}
    print("Scoring...")
    t0 = time.time()
    
    with torch.no_grad():
        for n, (claim, passage, key) in enumerate(pairs, 1):
            if n % 10 == 0:
                print(f"  Processed {n}/{len(pairs)}...")
                
            # DeBERTa expects (premise, hypothesis) -> (passage, claim)
            inputs = tokenizer(passage, claim, truncation=True, return_tensors="pt").to(device)
            outputs = model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=1).squeeze().cpu().tolist()
            
            # id2label mapping for cross-encoder/nli-deberta-v3-large:
            # 0: contradiction, 1: entailment, 2: neutral
            scores[key] = {
                "contradict": probs[0],
                "entail": probs[1],
                "neutral": probs[2]
            }

    print(f"Done in {time.time() - t0:.1f}s")
    
    # Save payload
    payload = {
        "meta": {
            "model": model_name,
            "device": device,
            "pairs": len(scores),
            "rows": len(items)
        },
        "scores": scores
    }
    
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1)
        
    print(f"Wrote {args.output}")

if __name__ == "__main__":
    main()
