# Click-delay vs GR perihelion precession — Mercury
# Compares click-delay integral to the GR benchmark; also scans eccentricity.

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
import math

# --- Constants ---
GMsun = 1.32712440018e20      # m^3/s^2
c = 299_792_458.0             # m/s
AU = 1.495978707e11           # m

# Mercury orbital params
a = 57.909e9                  # m
e = 0.205630
T_days = 87.969               # days
T = T_days * 86400.0          # s
n0 = np.sqrt(GMsun / a**3)    # mean motion

def delta_varpi_click_per_orbit(a, e, nsteps=200000):
    # Δϖ = ∫ κ_app(E) * n_inst(E) * dt   with κ_app = + 2 GM / (c^2 r)
    # r(E) = a (1 - e cos E),   n_inst = sqrt(GM/r^3),   dt = (1 - e cos E)/n0 dE
    n0 = np.sqrt(GMsun / a**3)
    E = np.linspace(0.0, 2*np.pi, nsteps, endpoint=False)
    r = a * (1 - e*np.cos(E))
    kappa = 2.0 * GMsun / (c**2 * r)
    n_inst = np.sqrt(GMsun / r**3)
    dE = 2*np.pi / nsteps
    dt = (1 - e*np.cos(E)) * dE / n0
    return float(np.sum(kappa * n_inst * dt))  # radians/orbit

def delta_varpi_gr_per_orbit(a, e):
    return 6.0 * math.pi * GMsun / (a * c**2 * (1.0 - e**2))

delta_click = delta_varpi_click_per_orbit(a, e)
delta_gr = delta_varpi_gr_per_orbit(a, e)

# Convert to arcsec/century
orbits_per_century = (100.0 * 365.25 * 86400.0) / T
arcsec = 206264.80624709636

click_arcsec_cent = delta_click * arcsec * orbits_per_century
gr_arcsec_cent = delta_gr * arcsec * orbits_per_century
ratio = click_arcsec_cent / gr_arcsec_cent

print(f"Click perihelion: {click_arcsec_cent:.3f} arcsec/century")
print(f"GR perihelion:    {gr_arcsec_cent:.3f} arcsec/century")
print(f"Click/GR ratio:   {ratio:.6f}")

# Time series
N_orbits = int(round(orbits_per_century))
times_years = (np.arange(N_orbits+1) * T) / (365.25*86400.0)
cum_click = np.arange(N_orbits+1) * (delta_click * arcsec)
cum_gr = np.arange(N_orbits+1) * (delta_gr * arcsec)

# Plot 1: cumulative precession
plt.figure(figsize=(7,4))
plt.plot(times_years, cum_click, linewidth=1.0, label="Click-delay")
plt.plot(times_years, cum_gr, linewidth=1.0, label="GR benchmark")
plt.xlabel("Time (years)")
plt.ylabel("Cumulative perihelion advance (arcsec)")
plt.title("Mercury perihelion: Click-delay vs GR (century)")
plt.legend()
plt.tight_layout()
plt.show()

# Plot 2: discrepancy
plt.figure(figsize=(7,4))
plt.plot(times_years, cum_gr - cum_click, linewidth=1.0)
plt.xlabel("Time (years)")
plt.ylabel("GR − Click (arcsec)")
plt.title("Discrepancy over a century")
plt.tight_layout()
plt.show()

# Plot 3: ratio vs eccentricity
e_vals = np.linspace(0.0, 0.9, 46)
ratios = []
for ee in e_vals:
    d_click = delta_varpi_click_per_orbit(a, ee, nsteps=40000)
    d_gr = delta_varpi_gr_per_orbit(a, ee)
    ratios.append(d_click / d_gr)
ratios = np.array(ratios)

plt.figure(figsize=(7,4))
plt.plot(e_vals, ratios, linewidth=1.0)
plt.xlabel("Eccentricity e")
plt.ylabel("Click / GR")
plt.title("Ratio of click-delay to GR vs eccentricity")
plt.tight_layout()
plt.show()

# Save minimal CSV
df = pd.DataFrame({
    "time_years": times_years,
    "cum_click_arcsec": cum_click,
    "cum_gr_arcsec": cum_gr
})
out = Path("mercury_click_vs_gr.csv")
df.to_csv(out, index=False)
print(f"Saved diagnostics to {out.resolve()}")
