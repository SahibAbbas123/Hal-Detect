#!/usr/bin/env python3
"""
HalDetect 2.0 Grand Vision Architectural System Figure Generator
==============================================================
Generates a publication-grade, 300-DPI architectural vector-style figure:
  - current/fig_grand_vision_architecture.png
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT_PATH = HERE / "fig_grand_vision_architecture.png"

plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["font.family"] = "sans-serif"

fig, ax = plt.subplots(figsize=(14, 10), dpi=300)
ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis("off")

# Background style
fig.patch.set_facecolor("#FAFAFC")
ax.set_facecolor("#FAFAFC")

# Helper function to draw rounded boxes
def draw_box(x, y, w, h, title, subtitle="", bgcolor="#FFFFFF", bordercolor="#CBD5E1", titlecolor="#0F172A", textcolor="#475569", rad=0.2, lw=1.5):
    box = patches.FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.08,rounding_size={rad}", facecolor=bgcolor, edgecolor=bordercolor, linewidth=lw, zorder=2)
    ax.add_patch(box)
    if title:
        ax.text(x + w/2, y + h - 0.35 if subtitle else y + h/2, title, ha="center", va="center", fontsize=11, fontweight="bold", color=titlecolor, zorder=3)
    if subtitle:
        ax.text(x + w/2, y + 0.35, subtitle, ha="center", va="center", fontsize=8.5, color=textcolor, zorder=3)

def draw_arrow(x1, y1, x2, y2, label="", color="#64748B"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->,head_width=0.4,head_length=0.6", color=color, lw=2.0), zorder=4)
    if label:
        ax.text((x1+x2)/2 + 0.15, (y1+y2)/2, label, fontsize=8.5, fontweight="semibold", color="#334155", va="center", zorder=5)

# 1. USER INPUT LAYER
draw_box(4.5, 8.8, 5.0, 0.8, "USER PROMPT / CONSUMER QUERY", "Complex multi-sentence query spanning science, economics, biography", "#EFF6FF", "#3B82F6", "#1D4ED8", "#1E40AF", rad=0.15, lw=2)

draw_arrow(7.0, 8.8, 7.0, 7.8, "Natural Language Prompt")

# 2. GENERATIVE FOUNDATION LLM
draw_box(3.8, 6.8, 6.4, 1.0, "GENERATIVE FOUNDATION LLM (e.g. Qwen 2.5 / DeepSeek-R1 / GPT-4o)", "Excels at Creative Narrative Synthesis, Fluency & Contextual Reasoning", "#F8FAFC", "#94A3B8", "#0F172A", "#475569", rad=0.15, lw=2)

draw_arrow(7.0, 6.8, 7.0, 5.8, "Multi-Sentence Response Draft")

# 3. HALDETECT 2.0 NEURO-SYMBOLIC CORE (BIG CONTAINER)
container = patches.FancyBboxPatch((0.8, 1.8), 12.4, 3.8, boxstyle="round,pad=0.12,rounding_size=0.3", facecolor="#F0FDF4", edgecolor="#16A34A", linewidth=2.5, linestyle="--", zorder=1)
ax.add_patch(container)
ax.text(1.2, 5.3, "HALDETECT 2.0 -- AUTOMATED NEURO-SYMBOLIC FACTUALITY FIREWALL", fontsize=12, fontweight="bold", color="#15803D", zorder=3)

# 3a. Proposition Atomization
draw_box(1.2, 3.6, 3.5, 1.3, "1. Schema 5-Tuple Atomizer", "Deconstructs prose into\n<S, P, O, T, M> propositions\nPreserves scope & polarity", "#FFFFFF", "#86EFAC", "#14532D", "#166534")

# 3b. Modality Router
draw_box(5.2, 3.6, 3.6, 1.3, "2. 5-Modality Taxonomy Router", "• Quantitative (Math/Units)\n• Temporal (State/Intervals)\n• Entity-Attribute / Citations", "#FFFFFF", "#86EFAC", "#14532D", "#166534")

# 3c. Symbolic Engines
draw_box(9.3, 3.6, 3.5, 1.3, "3. Multi-Tier Grounding", "• Wikidata SPARQL (Tier 1)\n• World Bank OData API (Tier 2)\n• CrossRef DOI Registry\n• Wikipedia Semantic Summary", "#FFFFFF", "#86EFAC", "#14532D", "#166534")

# Internal arrows
draw_arrow(4.7, 4.25, 5.2, 4.25, "", "#16A34A")
draw_arrow(8.8, 4.25, 9.3, 4.25, "", "#16A34A")

# 3d. Reasoning & 3-Valued Logic
draw_box(2.5, 2.0, 9.0, 1.1, "4. Truth-Functional & Dimensional Reasoning", "Typed SI Units (77K <-> -196C) • Temporal Invariants (2009-2017) • Calibrated 3-Valued Logic [TRUE / FALSE / UNVERIFIABLE]", "#DCFCE7", "#22C55E", "#14532D", "#166534")

draw_arrow(7.0, 3.6, 7.0, 3.1, "", "#16A34A")

# Arrow out of HalDetect
draw_arrow(7.0, 1.8, 7.0, 1.1, "Audited Propositions & Symbolic Verdicts")

# 4. FINAL TRUSTWORTHY OUTPUT
draw_box(3.5, 0.2, 7.0, 0.9, "100% TRUSTWORTHY RESPONSE TO CONSUMER", "[+] Verified Facts Confirmed  |  [-] Hallucinations Rectified with Ground Truth Proof", "#FEF3C7", "#F59E0B", "#92400E", "#78350F", rad=0.15, lw=2)

plt.tight_layout()
plt.savefig(OUT_PATH, dpi=300, bbox_inches="tight")
print(f"Grand Vision Figure successfully generated at: {OUT_PATH}")
