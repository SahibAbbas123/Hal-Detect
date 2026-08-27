#!/usr/bin/env python3
"""
HalDetect -- Master Publication Plot Generator
==============================================
Generates high-resolution (300 DPI) publication-grade figures for the thesis:
1. Fig 1: 4-Way System Comparison (Coverage vs Selective Accuracy vs False F1)
2. Fig 2: Modality-by-Modality Selective Accuracy Breakdown
3. Fig 3: Latency vs Selective Accuracy Trade-off (HalDetect vs RAG vs Neural)
4. Fig 4: Master Ablation Hierarchy (Full-Routed vs Tier 1 vs Semi vs Non-Routed)
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Set styling
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.size"] = 11
plt.rcParams["axes.labelsize"] = 12
plt.rcParams["axes.titlesize"] = 14
plt.rcParams["xtick.labelsize"] = 10
plt.rcParams["ytick.labelsize"] = 10
plt.rcParams["legend.fontsize"] = 10
plt.rcParams["figure.titlesize"] = 16

# ---------------------------------------------------------------------------
# FIGURE 1: 4-WAY SYSTEM COMPARISON
# ---------------------------------------------------------------------------
def plot_fig1():
    systems = ["HalDetect\n(Ours)", "Web-Search\nRAG", "Uniform\nDeBERTa-v3", "Uniform\nMiniCheck"]
    coverage = [39.3, 3.2, 79.0, 99.1]
    sel_acc = [77.7, 59.4, 51.6, 51.2]
    p_false = [56.9, 58.6, 64.8, 42.7]

    x = np.arange(len(systems))
    width = 0.25

    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=300)
    rects1 = ax.bar(x - width, coverage, width, label="Coverage (%)", color="#2b5c8f", alpha=0.9)
    rects2 = ax.bar(x, sel_acc, width, label="Selective Accuracy (%)", color="#2ca02c", alpha=0.9)
    rects3 = ax.bar(x + width, p_false, width, label="Precision on FALSE (%)", color="#d62728", alpha=0.9)

    ax.set_ylabel("Percentage (%)")
    ax.set_title("Master 4-Way Fact-Checking Paradigm Comparison (N = 1,005)", pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(systems, fontweight="bold")
    ax.legend(loc="upper left", frameon=True)
    ax.set_ylim(0, 115)
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    # Annotate bars
    for rects in [rects1, rects2, rects3]:
        for rect in rects:
            height = rect.get_height()
            if height > 0:
                ax.annotate(f"{height:.1f}%",
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha="center", va="bottom", fontsize=8.5)

    plt.tight_layout()
    out_path = HERE / "fig1_4way_system_comparison.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")

# ---------------------------------------------------------------------------
# FIGURE 2: MODALITY-BY-MODALITY SELECTIVE ACCURACY
# ---------------------------------------------------------------------------
def plot_fig2():
    modalities = ["Quantitative", "Citation", "Entity Attr.", "Temporal", "Relational"]
    haldetect = [97.8, 90.9, 81.3, 78.8, 66.4]
    minicheck = [55.0, 52.8, 41.4, 60.8, 50.2]
    deberta = [55.6, 52.1, 38.4, 60.6, 58.2]

    x = np.arange(len(modalities))
    width = 0.26

    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
    r1 = ax.bar(x - width, haldetect, width, label="HalDetect Neuro-Symbolic (Ours)", color="#1f77b4", edgecolor="black", linewidth=0.8)
    r2 = ax.bar(x, minicheck, width, label="Uniform MiniCheck-7B (EMNLP '24)", color="#ff7f0e", alpha=0.85)
    r3 = ax.bar(x + width, deberta, width, label="Uniform DeBERTa-v3", color="#9467bd", alpha=0.85)

    ax.set_ylabel("Selective Accuracy (%)")
    ax.set_title("Selective Accuracy Breakdown by Claim Modality (N = 1,005)", pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(modalities, fontweight="bold")
    ax.axhline(50.0, color="gray", linestyle=":", label="Random Guess (50%)")
    ax.legend(loc="upper right", frameon=True)
    ax.set_ylim(0, 115)
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    for rects in [r1, r2, r3]:
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f"{height:.1f}%",
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha="center", va="bottom", fontsize=8.5)

    plt.tight_layout()
    out_path = HERE / "fig2_modality_selective_accuracy.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")

# ---------------------------------------------------------------------------
# FIGURE 3: LATENCY VS ACCURACY SCATTER PLOT
# ---------------------------------------------------------------------------
def plot_fig3():
    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=300)

    systems_data = [
        ("HalDetect (Ours)", 22.4, 77.7, "#1f77b4", 250, "star"),
        ("Web-Search RAG", 221.1, 59.4, "#d62728", 120, "circle"),
        ("Uniform DeBERTa-v3", 42.1, 51.6, "#9467bd", 120, "square"),
        ("Uniform MiniCheck", 67.8, 51.2, "#ff7f0e", 150, "triangle"),
        ("End-to-End LLM Search\n(Est. Gemini/Perplexity)", 2500.0, 68.5, "#7f7f7f", 100, "diamond"),
    ]

    for name, lat, acc, color, size, shape in systems_data:
        marker = "*" if shape == "star" else "o" if shape == "circle" else "s" if shape == "square" else "^" if shape == "triangle" else "D"
        ax.scatter([lat], [acc], color=color, s=size, label=name.replace("\n", " "), marker=marker, edgecolors="black", linewidth=0.8, zorder=5)
        offset_y = 2.0 if "HalDetect" in name else -3.5 if "MiniCheck" in name else 1.5
        ax.annotate(name, (lat, acc + offset_y), fontsize=9, ha="center", fontweight="bold" if "Ours" in name else "normal")

    ax.set_xscale("log")
    ax.set_xlabel("Verification Latency per Claim (ms, Log Scale)")
    ax.set_ylabel("Selective Accuracy (%)")
    ax.set_title("Pareto Frontier: Verification Latency vs Selective Accuracy", pad=15)
    ax.set_ylim(40, 90)
    ax.set_xlim(10, 5000)
    ax.grid(True, linestyle="--", alpha=0.4)

    # Highlight HalDetect Pareto Superiority
    ax.axvspan(10, 50, color="#2ca02c", alpha=0.1, label="Sub-50ms Ultra-Fast Zone")

    ax.legend(loc="lower left", frameon=True, fontsize=8.5)
    plt.tight_layout()
    out_path = HERE / "fig3_latency_vs_accuracy_tradeoff.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")

# ---------------------------------------------------------------------------
# FIGURE 4: ABLATION HIERARCHY
# ---------------------------------------------------------------------------
def plot_fig4():
    configs = [
        "Full Taxonomy Router (Ours)",
        "↳ Tier 1 Only (No Fallback)",
        "↳ Semi-Routed (Symb + MiniCheck)",
        "Non-Routed MiniCheck-7B",
        "Non-Routed DeBERTa-v3",
        "Non-Routed Web-Search RAG"
    ]
    sel_acc = [77.7, 88.6, 66.6, 51.2, 51.6, 59.4]
    coverage = [39.3, 14.8, 52.7, 99.1, 79.0, 3.2]

    y = np.arange(len(configs))
    height = 0.35

    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
    b1 = ax.barh(y + height/2, sel_acc, height, label="Selective Accuracy (%)", color="#2ca02c", alpha=0.9)
    b2 = ax.barh(y - height/2, coverage, height, label="Coverage (%)", color="#1f77b4", alpha=0.85)

    ax.set_xlabel("Percentage (%)")
    ax.set_title("Architectural Ablation Decomposition (N = 1,005)", pad=15)
    ax.set_yticks(y)
    ax.set_yticklabels(configs, fontweight="bold")
    ax.invert_yaxis()
    ax.legend(loc="lower right", frameon=True)
    ax.set_xlim(0, 115)
    ax.grid(axis="x", linestyle="--", alpha=0.4)

    for b in [b1, b2]:
        for rect in b:
            width_val = rect.get_width()
            ax.annotate(f"{width_val:.1f}%",
                        xy=(width_val, rect.get_y() + rect.get_height() / 2),
                        xytext=(3, 0),
                        textcoords="offset points",
                        ha="left", va="center", fontsize=8.5)

    plt.tight_layout()
    out_path = HERE / "fig4_ablation_hierarchy.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")

if __name__ == "__main__":
    plot_fig1()
    plot_fig2()
    plot_fig3()
    plot_fig4()
    print("\nAll 4 publication plots successfully generated!")
