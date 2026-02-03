import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# Constants (architecture-consistent, minimal)
# ============================================================

R_H = 13.6                     # eV (Rydberg energy)
H_SI = 6.62607015e-34          # J s (Planck)
EV_TO_J = 1.602176634e-19      # J / eV
C_LIGHT = 2.99792458e8         # m/s

C_CRIT = 0.9                   # coherence threshold for Codec-2

# ============================================================
# Energy levels (gross structure only)
# ============================================================

def energy_level(n):
    """Hydrogen energy level in eV"""
    return -R_H / (n * n)

def photon_wavelength_nm(ni, nf):
    """Photon wavelength for transition ni -> nf"""
    dE_eV = abs(energy_level(nf) - energy_level(ni))
    dE_J = dE_eV * EV_TO_J
    nu = dE_J / H_SI
    lam_m = C_LIGHT / nu
    return lam_m * 1e9

# ============================================================
# Minimal Codec-2 emission model
# ============================================================

class ElectronRegister:
    def __init__(self, n):
        self.n = n          # principal quantum number
        self.C = 1.0        # coherence
        self.S = 0.0        # entropy

    def tick(self):
        """Decoherence accumulation"""
        self.S += 0.02
        self.C -= 0.02

    def codec2_emit(self, nf):
        """Codec-2 vector emission"""
        lam = photon_wavelength_nm(self.n, nf)
        self.n = nf
        self.C = min(1.0, self.C + 0.1)   # coherence recovery
        self.S = max(0.0, self.S - 0.1)   # entropy export
        return lam

# ============================================================
# Hydrogen Balmer simulation
# ============================================================

def simulate_balmer():
    """
    Demonstrator:
    excite hydrogen to multiple n
    allow Codec-2 emission when C < Ccrit
    project onto nf = 2 (Balmer series)
    """
    excited_levels = [3, 4, 5, 6]
    wavelengths = []

    for n0 in excited_levels:
        e = ElectronRegister(n0)

        # evolve until emission triggers
        while e.C > C_CRIT:
            e.tick()

        # Codec-2 emission to nf = 2
        lam = e.codec2_emit(nf=2)
        wavelengths.append(lam)

    return wavelengths

# ============================================================
# Plotting
# ============================================================

def plot_balmer(wavelengths):
    plt.figure(figsize=(8, 4))

    for lam in wavelengths:
        plt.vlines(lam, 0, 1, color="navy", linewidth=2)

    plt.xlim(380, 700)
    plt.ylim(0, 1.05)
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Intensity (arb.)")
    plt.title("Hydrogen Balmer Series (Codec-2 Emission)")
    plt.yticks([])
    plt.grid(axis="x", linestyle="--", alpha=0.4)

    plt.show()

# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    balmer_lines = simulate_balmer()
    plot_balmer(balmer_lines)
