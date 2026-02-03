# analyze_isco_instability.py
#
# Correct statistical analysis of ISCO-localized quantization leak
# Treats ISCO as a singular instability, not a global correlation.
#
# Tests implemented:
#   1. ISCO vs non-ISCO Z-score (sigma separation)
#   2. Contrast ratio (physical amplification factor)
#   3. Permutation test (distribution-free p-value)
#
# Optional:
#   Newtonian control baseline
#
# This script intentionally does NOT use Pearson/Spearman correlation.

import numpy as np
import numpy.random as rng
import matplotlib.pyplot as plt

# -----------------------------
# Physical constants
# -----------------------------
G = 6.67430e-11
c = 299792458.0
M_sun = 1.98847e30

M = 10.0 * M_sun
r_s = 2 * G * M / c**2

# -----------------------------
# Radii sampled
# -----------------------------
a_factors = np.array([1.2, 1.5, 2.0, 3.0, 4.0, 5.0])

# -----------------------------
# Data extraction
# -----------------------------
def load_leak_stats(fname, tail_frac=0.3):
    """
    Extract late-time mean ± std of dt-invariant leak.
    """
    data = np.load(fname, allow_pickle=True)
    L_series = data["L_per_rad"]

    n = len(L_series)
    tail = L_series[int((1 - tail_frac) * n):]

    return np.mean(tail), np.std(tail)

# -----------------------------
# Load data
# -----------------------------
L_mean = []
L_std  = []

for a in a_factors:
    mean, std = load_leak_stats(f"stew_bh_a{a}.npz")
    L_mean.append(mean)
    L_std.append(std)

L_mean = np.array(L_mean)
L_std  = np.array(L_std)

# -----------------------------
# Identify ISCO
# -----------------------------
isco_radius = 3.0
isco_idx = np.where(a_factors == isco_radius)[0][0]

L_isco = L_mean[isco_idx]
L_else = np.delete(L_mean, isco_idx)

# -----------------------------
# Test 1: Sigma separation (Z-score)
# -----------------------------
mu_else = np.mean(L_else)
sigma_else = np.std(L_else, ddof=1)

z_score = (L_isco - mu_else) / sigma_else

# -----------------------------
# Test 2: Contrast ratio
# -----------------------------
contrast = L_isco / mu_else

# -----------------------------
# Test 3: Permutation test
# -----------------------------
N_perm = 100_000
count = 0

for _ in range(N_perm):
    shuffled = rng.permutation(L_mean)
    if shuffled[isco_idx] >= L_isco:
        count += 1

p_perm = count / N_perm

# -----------------------------
# Optional Newtonian control
# -----------------------------
try:
    newt_mean, newt_std = load_leak_stats("stew_newtonian.npz")
    have_newtonian = True
except FileNotFoundError:
    have_newtonian = False

# -----------------------------
# Report results
# -----------------------------
print("\n=== ISCO INSTABILITY ANALYSIS ===\n")

print(f"ISCO radius           : r = {isco_radius} r_s")
print(f"L_ISCO                : {L_isco:.2f} Hz/rad")
print(f"Mean(non-ISCO)        : {mu_else:.2f} Hz/rad")
print(f"σ(non-ISCO)           : {sigma_else:.2f} Hz/rad")

print("\n--- Significance ---")
print(f"Z-score               : {z_score:.2f} σ")
print(f"Contrast ratio        : {contrast:.2f} ×")
print(f"Permutation p-value   : {p_perm:.3e}")

if have_newtonian:
    print("\n--- Newtonian Control ---")
    print(f"Newtonian baseline    : {newt_mean:.2f} Hz/rad")
    print(f"ISCO / Newtonian      : {L_isco / newt_mean:.2f} ×")

# -----------------------------
# Plot
# -----------------------------
fig, ax = plt.subplots(figsize=(9, 6))

ax.errorbar(
    a_factors,
    L_mean,
    yerr=L_std,
    fmt="o-",
    lw=2,
    capsize=4,
    label="Leak (dt-invariant)"
)

ax.axvline(isco_radius, color="k", ls=":", lw=1)
ax.text(isco_radius + 0.02, max(L_mean)*0.92, "ISCO", rotation=90, va="top")

if have_newtonian:
    ax.axhline(
        newt_mean,
        color="gray",
        ls="--",
        lw=2,
        label="Newtonian baseline"
    )

ax.set_xlabel(r"$r / r_s$")
ax.set_ylabel(r"$L_{\mathrm{leak}}\ \mathrm{[Hz/rad]}$")
ax.set_title("ISCO-Localized Quantization Instability")

stats_text = (
    f"Z = {z_score:.2f} σ\n"
    f"Contrast = {contrast:.2f}×\n"
    f"Permutation p = {p_perm:.2e}"
)

ax.text(
    0.02, 0.95,
    stats_text,
    transform=ax.transAxes,
    va="top",
    ha="left",
    bbox=dict(boxstyle="round", fc="white", ec="gray")
)

ax.legend()
plt.tight_layout()
plt.savefig("isco_instability_analysis.pdf", dpi=300)
plt.show()
