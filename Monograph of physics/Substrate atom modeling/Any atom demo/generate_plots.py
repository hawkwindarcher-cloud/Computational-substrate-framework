#!/usr/bin/env python3
"""
Standalone plotting script for Universal Atom results
Reads periodic_table_scan.csv and generates publication figures
"""

import sys
import os
import pandas as pd

# =========================
# CONFIGURATION
# =========================
SHOW_PLOTS = False   # Set True if you want interactive windows
DPI = 300

# =========================
# PATH HANDLING (FIXED)
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "periodic_table_scan.csv")
OUTDIR = BASE_DIR

# =========================
# MATPLOTLIB SETUP
# =========================
try:
    import matplotlib
    if not SHOW_PLOTS:
        matplotlib.use("Agg")  # Headless / publication mode
    import matplotlib.pyplot as plt
    print("✓ Matplotlib loaded")
except ImportError as e:
    print("ERROR: matplotlib not installed")
    print("Install with: pip install matplotlib")
    sys.exit(1)

# =========================
# HELPERS
# =========================
def validate_columns(df, required):
    missing = [c for c in required if c not in df.columns]
    if missing:
        print("ERROR: CSV missing required columns:")
        for c in missing:
            print(f"  - {c}")
        print("\nFound columns:")
        print(list(df.columns))
        sys.exit(1)

# =========================
# PLOTTING FUNCTIONS
# =========================
def plot_stability_vs_Z():
    print(f"\nReading CSV: {CSV_PATH}")
    if not os.path.exists(CSV_PATH):
        print("ERROR: periodic_table_scan.csv not found")
        sys.exit(1)

    df = pd.read_csv(CSV_PATH)
    validate_columns(df, ["Z", "Stability", "N/Z"])

    Z = df["Z"].values
    stability = df["Stability"].values
    nz = df["N/Z"].values

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # --- Stability plot ---
    ax1.plot(Z, stability, linewidth=2, label="Nuclear Stability")
    for z in [2, 8, 20, 28, 50, 82]:
        if z <= Z.max():
            ax1.axvline(z, linestyle="--", alpha=0.3)
            ax1.text(z, 1.05, f"Z={z}", rotation=90, fontsize=8)

    ax1.set_xlabel("Atomic Number (Z)")
    ax1.set_ylabel("Nuclear Stability")
    ax1.set_ylim(0, 1.15)
    ax1.set_xlim(0, Z.max() + 2)
    ax1.grid(alpha=0.3)
    ax1.legend()

    # --- N/Z plot ---
    ax2.plot(Z, nz, linewidth=2, label="N/Z Ratio")
    ax2.axhline(1.0, linestyle=":", alpha=0.5, label="N=Z")
    ax2.fill_between(Z, 1.0, nz, where=(nz >= 1.0), alpha=0.2)
    ax2.set_xlabel("Atomic Number (Z)")
    ax2.set_ylabel("N/Z Ratio")
    ax2.set_xlim(0, Z.max() + 2)
    ax2.grid(alpha=0.3)
    ax2.legend()

    plt.tight_layout()

    outfile = os.path.join(OUTDIR, "stability_vs_Z.png")
    plt.savefig(outfile, dpi=DPI, bbox_inches="tight")
    print(f"✓ Saved {outfile}")

    if SHOW_PLOTS:
        plt.show()
    plt.close()

def plot_simple_summary():
    print("\nGenerating summary plot...")
    df = pd.read_csv(CSV_PATH)
    validate_columns(df, ["Z", "Stability"])

    Z = df["Z"].values
    stability = df["Stability"].values

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(Z, stability, marker="o", markersize=3, linewidth=2, alpha=0.7)

    ax.set_xlabel("Atomic Number (Z)")
    ax.set_ylabel("Nuclear Stability")
    ax.set_ylim(0, 1.1)
    ax.set_xlim(0, 95)
    ax.grid(alpha=0.3)

    outfile = os.path.join(OUTDIR, "stability_summary.png")
    plt.tight_layout()
    plt.savefig(outfile, dpi=DPI, bbox_inches="tight")
    print(f"✓ Saved {outfile}")

    if SHOW_PLOTS:
        plt.show()
    plt.close()

# =========================
# MAIN
# =========================
def main():
    print("=" * 70)
    print("UNIVERSAL ATOM — PLOT GENERATOR")
    print("=" * 70)

    plot_stability_vs_Z()
    plot_simple_summary()

    print("\nSUCCESS — plots generated")
    print(f"Output directory: {OUTDIR}")
    print("=" * 70)

if __name__ == "__main__":
    main()
