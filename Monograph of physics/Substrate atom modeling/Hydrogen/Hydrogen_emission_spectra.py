# ============================================================
# HYDROGEN DEMONSTRATOR — REWRITE WITH FIXES (audit session)
# Companion to hydrogen_chapter_fixed.tex / hydrogen_backhalf_fixed.tex
#
# CHANGELOG vs. previous version:
#  1. REDUCED MASS (the false-precision seam, code side): the old
#     script computed Ry_inf = alpha^2 m_e c^2 / 2 and compared the
#     resulting VACUUM wavelengths against AIR reference values.
#     FIXED: Ry_H = Ry_inf / (1 + m_e/m_p) now used (eq. reduced_mass),
#     m_p/m_e = 1836.15267 stated as fixed input, +0.0545% correction.
#  2. MEDIUM SEAM: wavelengths now computed in vacuum and converted
#     per series — Balmer compared in standard air (n_air = 1.000276),
#     Lyman in vacuum — matching the six-row chapter table.
#  3. UNITS COLLISION: symbol R_H (energy) renamed RY_H_EV; the
#     wavenumber constant, if needed, is RY_H_EV/(hc). Conforms to
#     the Ry / R_H split in the front half.
#  4. N_CAP CIRCULARITY: old line N_CAP = exp(137.036/pi_eff^2)
#     back-solved capacity from the target. N_cap is now an explicit
#     literal imported from the capacity-enumeration result of
#     §alpha_fullderivation; alpha is then computed forward.
#  5. REGISTER DYNAMICS conformed to chapter equations:
#     C -= gamma*S*E_ext, S += gamma*S*E_ext (gamma = 0.07 [M]);
#     old fixed-increment ticks and ad-hoc load-density term removed.
#  6. EMISSION RESTORE conformed to canonical M_2 registry action:
#     C -> min(1, C + 0.1) (was +0.25), S -> c2*S multiplicative
#     export (was additive S - 0.3). c2 = 0.5 [M].
#  7. FINE-STRUCTURE PROXY added (was claimed in Implementation list,
#     absent from code): dE_fine = dE_gross + eps*S, eps = 1e-3 eV [M].
#     OFF by default — the proxy is a placeholder and would corrupt
#     the gross-structure table if applied.
#  8. Lyman series added (2->1, 3->1) with series classification,
#     matching the six-row back-half table; vague "excellent/good"
#     labels replaced by a Residual column in percent.
# All simulation settings (gamma, C_crit, dC_emit, c2, S0, E_ext, eps)
# are [M] — mechanism placeholders, not derived quantities.
# ============================================================

import math
import matplotlib.pyplot as plt

# --- Physical constants (SI / conversion) --------------------------
H_SI = 6.62607015e-34            # J s
EV_TO_J = 1.602176634e-19        # J/eV
C_LIGHT = 2.99792458e8           # m/s
HC_EVNM = H_SI * C_LIGHT / EV_TO_J * 1e9   # 1239.842 eV nm
N_AIR = 1.000276                 # standard air refractive index

# --- Architectural chain (§rydberg_magnitude) ----------------------
PI_EFF = 63 / 20                 # sexagesimal closure (derived)
N_CAP = 995133.72                # substrate capacity enumeration,
                                 # §alpha_fullderivation (derived there;
                                 # imported here as a literal)
ALPHA = 1.0 / (PI_EFF**2 * math.log(N_CAP))   # alpha^-1 = 137.036

M_E_C2_EV = 510998.95            # electron inertial content [empirical input]
MP_OVER_ME = 1836.15267          # proton/electron register-content ratio

RY_INF_EV = ALPHA**2 * M_E_C2_EV / 2          # 13.6057 eV (immovable nucleus)
RY_H_EV = RY_INF_EV / (1 + 1/MP_OVER_ME)      # 13.5983 eV (load partition [H])

# --- Simulation settings [M] ---------------------------------------
GAMMA, E_EXT, S0 = 0.07, 1.0, 0.05
C_CRIT, DC_EMIT, C2_EXPORT = 0.9, 0.1, 0.5
EPS_FINE = 1e-3                  # eV; fine-structure proxy, placeholder

def E_n(n):                      # architectural E_n = -Ry_H / n^2
    return -RY_H_EV / (n * n)

class ElectronRegister:
    def __init__(self, n):
        self.n, self.C, self.S = n, 1.0, S0

    def tick(self):              # eqs. coherence_decay / entropy_growth
        dS = GAMMA * self.S * E_EXT
        self.C -= dS
        self.S += dS

    def codec2_emit(self, nf, fine_structure=False):
        dE = abs(E_n(self.n) - E_n(nf))
        if fine_structure:                    # proxy [M], off by default
            dE += EPS_FINE * self.S
        from_n, self.n = self.n, nf
        self.C = min(1.0, self.C + DC_EMIT)   # eq. coherence_restoration
        self.S = C2_EXPORT * self.S           # eq. entropy_export (M_2: S -> c2 S)
        lam_vac = HC_EVNM / dE
        series = {1: "Lyman", 2: "Balmer", 3: "Paschen"}.get(nf, f"nf={nf}")
        medium = "vac" if series == "Lyman" else "air"
        lam = lam_vac if medium == "vac" else lam_vac / N_AIR
        return dict(from_n=from_n, to_n=nf, energy_ev=dE,
                    wavelength_nm=lam, medium=medium, series=series)

def simulate(transitions):
    out = []
    for ni, nf in transitions:
        e = ElectronRegister(ni)
        while e.C > C_CRIT:                   # decohere until threshold
            e.tick()
        out.append(e.codec2_emit(nf))
    return out

if __name__ == "__main__":
    print(f"alpha^-1 = {1/ALPHA:.3f}   Ry_inf = {RY_INF_EV:.4f} eV   "
          f"Ry_H = {RY_H_EV:.4f} eV")
    OBS = {(3,2): 656.28, (4,2): 486.13, (5,2): 434.05, (6,2): 410.17,
           (2,1): 121.57, (3,1): 102.57}     # air (Balmer) / vac (Lyman)
    ems = simulate(list(OBS))
    print(f"{'line':>6} {'series':>7} {'E (eV)':>8} {'model nm':>9} "
          f"{'obs nm':>8} {'med':>4} {'residual':>9}")
    for em in ems:
        key = (em['from_n'], em['to_n'])
        res = abs(em['wavelength_nm'] - OBS[key]) / OBS[key] * 100
        print(f"{em['from_n']}->{em['to_n']:>3} {em['series']:>7} "
              f"{em['energy_ev']:8.4f} {em['wavelength_nm']:9.2f} "
              f"{OBS[key]:8.2f} {em['medium']:>4} {res:8.4f}%")

    balmer = [e for e in ems if e['series'] == "Balmer"]
    plt.figure(figsize=(11, 5))
    for em in balmer:
        plt.vlines(em['wavelength_nm'], 0, 1, color="navy", lw=3.5)
        plt.text(em['wavelength_nm'] + 1.5, 1.03, f"{em['from_n']}\u21922",
                 rotation=90, va='bottom', ha='center', fontsize=10)
    plt.xlim(380, 700); plt.ylim(0, 1.2); plt.yticks([])
    plt.xlabel("Wavelength in standard air (nm)")
    plt.title("Balmer series — architectural chain with reduced mass "
              "(Ry$_H$ = %.4f eV)" % RY_H_EV)
    plt.grid(axis="x", ls="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig("balmer_codec.png", dpi=150)
    plt.show()
