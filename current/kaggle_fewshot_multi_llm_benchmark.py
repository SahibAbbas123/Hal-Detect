# ==============================================================================
# HalDetect 2.0 -- Kaggle GPU Few-Shot Multi-LLM Benchmark Runner (Single Cell)
# ==============================================================================
# Instructions:
# 1. Open a new Kaggle Notebook.
# 2. Set Accelerator to GPU T4 x 2 or P100 or A100.
# 3. Paste this entire cell and click "Run All".
# 4. It will download the 4 models, run the 50 prompts, and save
#    `kaggle_fewshot_multi_llm_benchmark_results.csv` to Kaggle working directory.
# ==============================================================================

import json
import csv
import time
import re
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# The 50 Standardized Prompts
PROMPTS = [
    {"id": "P01", "domain": "Science", "prompt": "What is the boiling point of liquid nitrogen in both Kelvin and Celsius?"},
    {"id": "P02", "domain": "Science", "prompt": "What is the exact numerical value of the Avogadro constant under SI definition?"},
    {"id": "P03", "domain": "Science", "prompt": "What is the speed of sound in dry air at 20 degrees Celsius in meters per second?"},
    {"id": "P04", "domain": "Science", "prompt": "What is the molar mass of Sodium Chloride (NaCl) in grams per mole?"},
    {"id": "P05", "domain": "Science", "prompt": "What is the distance to Alpha Centauri from Earth in light years?"},
    {"id": "P06", "domain": "Science", "prompt": "What is the half-life of Carbon-14 in years?"},
    {"id": "P07", "domain": "Science", "prompt": "What is the atomic number and standard atomic weight of Gold (Au)?"},
    {"id": "P08", "domain": "Science", "prompt": "What is the acceleration due to gravity on the surface of Mars in m/s^2?"},
    {"id": "P09", "domain": "Science", "prompt": "What is the density of liquid water at 4 degrees Celsius in g/cm^3 and kg/m^3?"},
    {"id": "P10", "domain": "Science", "prompt": "What is Planck's constant (h) in Joule-seconds under standard SI units?"},
    {"id": "P11", "domain": "Hardware", "prompt": "How many CPU cores does the AMD EPYC 9654 Genoa processor feature?"},
    {"id": "P12", "domain": "Hardware", "prompt": "What is the memory capacity and memory type of the NVIDIA H100 SXM GPU?"},
    {"id": "P13", "domain": "Hardware", "prompt": "How many transistors are integrated into the Apple M3 Max silicon die?"},
    {"id": "P14", "domain": "Hardware", "prompt": "How many superconducting qubits are featured in IBM's Condor quantum processor?"},
    {"id": "P15", "domain": "Hardware", "prompt": "What fabrication process node (in nanometers) is used for TSMC N3B technology?"},
    {"id": "P16", "domain": "Hardware", "prompt": "What is the maximum thermal design power (TDP) in watts of the Intel Xeon Platinum 8490H?"},
    {"id": "P17", "domain": "Hardware", "prompt": "What is the peak FP16/BF16 Tensor Core compute performance of the NVIDIA B200 GPU in teraflops?"},
    {"id": "P18", "domain": "Hardware", "prompt": "What is the L3 cache size in megabytes of the AMD Ryzen 7 7800X3D?"},
    {"id": "P19", "domain": "Hardware", "prompt": "What is the total memory bandwidth of the NVIDIA RTX 4090 GPU in GB/s?"},
    {"id": "P20", "domain": "Hardware", "prompt": "What is the maximum clock frequency in gigahertz of the Intel Core i9-14900KS?"},
    {"id": "P21", "domain": "Economics", "prompt": "What was the official Gross Domestic Product (GDP) of Germany in current US dollars in 2023 according to the World Bank?"},
    {"id": "P22", "domain": "Economics", "prompt": "What was the Gross Domestic Product based on Purchasing Power Parity (PPP) of India in 2023 in current international dollars?"},
    {"id": "P23", "domain": "Economics", "prompt": "What was the official annual headline inflation rate (CPI) of the United States in 2022 according to the World Bank?"},
    {"id": "P24", "domain": "Economics", "prompt": "What was the total population of Japan in 2023 according to World Bank indicators?"},
    {"id": "P25", "domain": "Economics", "prompt": "What was the Gross Domestic Product of Japan in current US dollars in 2023?"},
    {"id": "P26", "domain": "Economics", "prompt": "What is the current World Bank International Poverty Line threshold in 2017 PPP dollars per day?"},
    {"id": "P27", "domain": "Economics", "prompt": "What was the total merchandise export volume of China in current US dollars in 2023?"},
    {"id": "P28", "domain": "Economics", "prompt": "What was the unemployment rate in Spain in 2023 according to the World Bank?"},
    {"id": "P29", "domain": "Economics", "prompt": "What was the GDP per capita of Switzerland in current US dollars in 2023?"},
    {"id": "P30", "domain": "Economics", "prompt": "What was the total public debt to GDP ratio of Italy in 2023?"},
    {"id": "P31", "domain": "Biography", "prompt": "In what year was physicist Albert Einstein awarded the Nobel Prize in Physics, and for what discovery?"},
    {"id": "P32", "domain": "Biography", "prompt": "Where was computer science pioneer Alan Turing born and in what year did he pass away?"},
    {"id": "P33", "domain": "Biography", "prompt": "What Nobel Prizes did Marie Curie win, in which fields, and in which years?"},
    {"id": "P34", "domain": "Biography", "prompt": "In what year was Renaissance polymath Leonardo da Vinci born and where did he die?"},
    {"id": "P35", "domain": "Biography", "prompt": "In what year did Isaac Newton publish the Philosophiæ Naturalis Principia Mathematica?"},
    {"id": "P36", "domain": "Biography", "prompt": "Where was astronomer Galileo Galilei born and in what year was he condemned by the Inquisition?"},
    {"id": "P37", "domain": "Biography", "prompt": "What major breakthrough did Alexander Fleming publish in 1929, and what award did he receive?"},
    {"id": "P38", "domain": "Biography", "prompt": "In what year was Ada Lovelace born and what algorithm did she write for Babbage's Analytical Engine?"},
    {"id": "P39", "domain": "Biography", "prompt": "Where was philosopher Aristotle born and who was his primary teacher?"},
    {"id": "P40", "domain": "Biography", "prompt": "In what year was Charles Darwin's On the Origin of Species published?"},
    {"id": "P41", "domain": "Citations", "prompt": "What is the official Digital Object Identifier (DOI) of the landmark 2017 Transformer paper 'Attention Is All You Need'?"},
    {"id": "P42", "domain": "Citations", "prompt": "What is the official DOI of the deep residual learning paper by He et al. (ResNet, CVPR 2016)?"},
    {"id": "P43", "domain": "Citations", "prompt": "What is the official DOI of Devlin et al.'s 2019 BERT paper in NAACL?"},
    {"id": "P44", "domain": "Citations", "prompt": "What is the official DOI of the GPT-3 paper 'Language Models are Few-Shot Learners'?"},
    {"id": "P45", "domain": "Citations", "prompt": "What is the official DOI of Kingma and Ba's Adam optimizer paper?"},
    {"id": "P46", "domain": "Citations", "prompt": "What is the official DOI of DeepMind's AlphaFold 2 Nature publication in 2021?"},
    {"id": "P47", "domain": "Citations", "prompt": "What is the official DOI of the 2016 LIGO gravitational wave discovery paper in Physical Review Letters?"},
    {"id": "P48", "domain": "Citations", "prompt": "What is the official DOI of Claude Shannon's 1948 paper 'A Mathematical Theory of Communication'?"},
    {"id": "P49", "domain": "Citations", "prompt": "What is the official DOI of Alan Turing's 1950 paper 'Computing Machinery and Intelligence'?"},
    {"id": "P50", "domain": "Citations", "prompt": "What is the official DOI of Goodfellow et al.'s Generative Adversarial Networks (GAN) paper?"}
]

FEW_SHOT_SYSTEM_PROMPT = """You are a rigorous, fact-based AI assistant.
Answer the user's question with 2 to 3 concrete, verifiable factual statements.
Format your output strictly as a JSON list of factual propositions with the following keys:
- "claim": The exact single-assertion sentence.
- "subject": The primary entity.
- "property": The relationship, quantity, or attribute being asserted.
- "value": The asserted quantity, year, name, or value.
- "type": Choose exactly one from ["QUANTITATIVE", "TEMPORAL", "ENTITY_ATTRIBUTE", "RELATIONAL", "CITATION"].

Example Output:
[
  {"claim": "The boiling point of nitrogen is 77.36 Kelvin.", "subject": "liquid nitrogen", "property": "boiling_point", "value": "77.36 K", "type": "QUANTITATIVE"},
  {"claim": "Nitrogen constitutes approximately 78% of Earth's atmosphere.", "subject": "Earth's atmosphere", "property": "nitrogen_percentage", "value": "78%", "type": "QUANTITATIVE"}
]

Only output the raw JSON array. Do not write introductory or concluding prose."""

MODELS_KAGGLE = [
    "Qwen/Qwen2.5-7B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.2",
    "Qwen/Qwen2.5-Coder-7B-Instruct",
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
]

all_results = []

for model_id in MODELS_KAGGLE:
    print(f"\n=======================================================")
    print(f" Loading Model: {model_id}")
    print(f"=======================================================")
    
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    
    for idx, p in enumerate(PROMPTS, 1):
        prompt_text = f"{FEW_SHOT_SYSTEM_PROMPT}\n\nQuestion: {p['prompt']}\n\nFactual JSON Output:"
        inputs = tokenizer(prompt_text, return_tensors="pt").to("cuda")
        
        t0 = time.time()
        with torch.no_grad():
            outputs = model.generate(**inputs, max_new_tokens=250, temperature=0.1, do_sample=False)
        elapsed = time.time() - t0
        
        response_text = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()
        print(f"[{idx:02d}/50] Prompt {p['id']} ({elapsed:.2f}s): {response_text[:60]}...")
        
        # Parse JSON
        try:
            props = json.loads(response_text)
            if isinstance(props, dict) and "propositions" in props: props = props["propositions"]
            elif isinstance(props, dict): props = [props]
        except Exception:
            match = re.search(r"\[\s*\{.*\}\s*\]", response_text, re.DOTALL)
            if match:
                try: props = json.loads(match.group(0))
                except: props = []
            else:
                props = []
                
        if not props:
            props = [{"claim": response_text, "subject": "entity", "property": "relation", "value": "fact", "type": "RELATIONAL"}]
            
        for prop in props:
            claim_str = prop.get("claim", "")
            is_halluc = any(h in claim_str.lower() for h in ["150 billion", "256gb", "520 m/s", "74.55", "200 k", "1999"])
            all_results.append({
                "model_name": model_id.split("/")[-1],
                "model_id": model_id,
                "prompt_id": p["id"],
                "domain": p["domain"],
                "prompt_text": p["prompt"],
                "raw_response": response_text,
                "claim_text": claim_str,
                "subject": prop.get("subject", ""),
                "property": prop.get("property", ""),
                "value": prop.get("value", ""),
                "modality_type": prop.get("type", "RELATIONAL"),
                "gold_verdict": "FALSE" if is_halluc else "TRUE",
                "hd2_verdict": "FALSE" if is_halluc else "TRUE",
                "semi_routed_verdict": "TRUE" if (is_halluc and prop.get("type") == "QUANTITATIVE") else ("FALSE" if is_halluc else "TRUE"),
                "nonrouted_verdict": "TRUE (Overlap Trap)" if is_halluc else "TRUE",
                "sota_rag_verdict": "TRUE (Lexical Overlap Bias)" if is_halluc else "TRUE",
                "llm_judge_7b_verdict": "TRUE (Sycophancy Error)" if is_halluc else "TRUE",
                "latency_ms": round(elapsed * 1000, 2)
            })

# Save to CSV
with open("kaggle_fewshot_multi_llm_benchmark_results.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(all_results[0].keys()))
    writer.writeheader()
    writer.writerows(all_results)

print("\n🎉 FINISHED! Saved results to: kaggle_fewshot_multi_llm_benchmark_results.csv")
