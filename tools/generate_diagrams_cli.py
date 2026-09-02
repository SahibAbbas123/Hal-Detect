#!/usr/bin/env python3
"""
Thesis Diagram Studio CLI (Powered by PaperBanana & Gemini)
Generate and preview publication-quality academic diagrams for thesis and papers.
"""

import os
import sys
import argparse
import subprocess
import json
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
EXPORT_DIR = BASE_DIR / "exported_diagrams_preview"
AI_EXPORT_DIR = EXPORT_DIR / "ai_visual_renders"
VECTOR_EXPORT_DIR = EXPORT_DIR / "latex_vector_upgrades"
API_KEY_FILE = BASE_DIR / "geminiAPI.txt"

def load_gemini_key():
    """Safely load API key without printing or exposing."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key and API_KEY_FILE.exists():
        with open(API_KEY_FILE, "r", encoding="utf-8") as f:
            api_key = f.read().strip()
    return api_key

def ensure_dirs():
    AI_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    VECTOR_EXPORT_DIR.mkdir(parents=True, exist_ok=True)

def list_diagrams():
    print("=" * 60)
    print("  Available Thesis Diagrams & Export Status")
    print("=" * 60)
    
    diagrams = [
        ("Figure 1", "fig1_triage_paradigm", "Chapter 1: HalDetect Neuro-Symbolic Triage vs. Monolithic Black-Box"),
        ("Figure 3", "fig3_architecture_pipeline", "Chapter 3: Full 3-Module Architecture & Modality Triage Pipeline"),
        ("Figure 4", "fig4_dataset_lineage", "Chapter 4: Benchmark Corpus Evolution & Multi-LLM Road Test"),
        ("Figure 5", "fig5_attention_dilution", "Chapter 5: Attention Dilution Mechanism & Symbolic Math Contrast"),
    ]
    
    for tag, name, desc in diagrams:
        ai_file = AI_EXPORT_DIR / f"{name}.jpg"
        vec_pdf = VECTOR_EXPORT_DIR / f"{name}_upgraded.pdf"
        vec_png = VECTOR_EXPORT_DIR / f"{name}_upgraded_preview-1.png"
        
        ai_status = "✓ Ready" if ai_file.exists() else "✗ Not Generated"
        vec_status = "✓ Ready" if vec_pdf.exists() and vec_png.exists() else "✗ Missing"
        
        print(f"\n▶ [{tag}] {desc}")
        print(f"    Identifier: {name}")
        print(f"    AI Visual Render:    {ai_status} ({ai_file.name if ai_file.exists() else ''})")
        print(f"    Vector LaTeX Render: {vec_status} ({vec_pdf.name if vec_pdf.exists() else ''})")
    
    print("\n" + "=" * 60)
    print(f"Dedicated Export Directory: {EXPORT_DIR.relative_to(BASE_DIR)}/")
    print("=" * 60)

def compile_vector_diagrams(target=None):
    ensure_dirs()
    print("Building and compiling LaTeX vector diagrams...")
    builder = BASE_DIR / "tools" / "build_latex_upgrades.py"
    if builder.exists():
        subprocess.run([sys.executable, str(builder)], cwd=str(BASE_DIR), check=True)
    print(f"\nAll vector diagrams compiled to: {VECTOR_EXPORT_DIR.relative_to(BASE_DIR)}/")

def main():
    parser = argparse.ArgumentParser(description="Thesis Diagram Studio CLI")
    parser.add_argument("--list", action="store_true", help="List all available thesis diagrams and status")
    parser.add_argument("--build-vector", action="store_true", help="Compile all upgraded TikZ vector diagrams (PDF + 300 DPI PNG)")
    parser.add_argument("--output-dir", type=str, default=str(EXPORT_DIR), help="Output directory for exported previews")
    
    args = parser.parse_args()
    
    if len(sys.argv) == 1 or args.list:
        list_diagrams()
    elif args.build_vector:
        compile_vector_diagrams()
        list_diagrams()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
