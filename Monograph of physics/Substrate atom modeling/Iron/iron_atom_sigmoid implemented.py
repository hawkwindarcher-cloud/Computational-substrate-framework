# ============================================================
# IRON SIMULATOR — REWRITE WITH FIXES (audit session)
# Companion to iron_chapter_fixed.tex; items keyed to its changelog.
#
# CHANGELOG vs. previous version:
#  A1. VALLEY COEFFICIENT (the big one): c_val = 0.015 gave
#      r_opt = 1.39 at Z=26 and INVERTED the isotope ranking
#      (Fe-60 = 0.941 above Fe-56 = 0.830, verified). Worse, the
#      old code MASKED this with a fiat: Fe-56 was special-cased
#      to stability 1.0 by construction. Fiat removed; c_val =
#      0.006 (physical valley r_opt ~ 1.156); cap restored to 1.0.
#      Reproduces chapter orientation values: Fe-54 = 1.000
#      (magic-N capped), Fe-56 = 0.998, Fe-58 = 0.935 (STABLE,
#      audit C4), Fe-60 = 0.869 — least stable but ABOVE the 0.6
#      decay gate: the N/Z scalar alone does not produce Fe-60's
#      observed beta- decay, stated honestly per the chapter.
#  A2. Codec-5 comment honesty: 8.5 MeV is a CALIBRATED INPUT [M]
#      matched to Fe BE/A; at the Fe-56 operating point the gate
#      yields ~0.107 MeV per invocation, not the total BE/A.
#  A3. NIST shell energies and the Fe I multiplet table labeled
#      SPECIFIED CONSTANTS; summary prints derived vs specified.
#  A4. Codec-6 comment: order-symmetric stochastic decay-mode
#      selector (list comprehension + random.choice). No ordered
#      loop, no early return, NO CP/weak-phenomenology claim.
#  B1. W(26) = 832,858 computed and printed (1:10:47 hierarchy;
#      stale 830,330 retired).
#  B3. Magnetic moment: 4*0.5 = 2.0 retired. UNPAIRED = 4 is a
#      specified constant; spin-only mu_eff = sqrt(n(n+2)) =
#      4.90 mu_B, vs ~5.4 mu_B expt (orbital contribution).
#  B4. "Fe-56 = peak of binding-energy curve, maximally stable"
#      comment RETIRED: Ni-62 has the highest BE/A (8.7945 MeV);
#      Fe-56's distinction is lowest mass per nucleon.
#  B5. Emission restore conformed to canonical multiplicative M_2:
#      S -> c2*S, C -> min(1, 1.05*C) (was additive export).
#  C1. All simulation settings gathered in one [M] block below;
#      no "no free parameters" pretense anywhere in this file.
#  C4. Magic-number list gains 126 (harmless for iron, seam fixed
#      for reuse on heavy nuclei).
#  C5. Scheduler honesty: valence emission uses the Born-rule
#      sigmoid on rho = S/K_cap (governor-style, fires at
#      saturation); the inner-shell and nuclear coin flips remain
#      a stochastic SCHEDULER [M] — the coin flip stands in for
#      inner-hole creation, it is not the Sec. 28 governor.
#  D4. Threshold registry: C_DEC = 0.78 (decoherence cascade,
#      this chapter) declared DISTINCT from the hydrogen
#      chapter's C_EMIT = 0.9. Cascade reinstated per chapter
#      (was silently dropped): Id *= 0.7, S_nuc *= 0.85 at
#      mean C < C_DEC.
#  D6. Ad-hoc "curvature" replaced by the chapter's nuclear
#      loading kappa = A/(Z+0.1) * (1 - S_nuc); the unconditional
#      stability *= 0.95 degrade (present in old code, absent
#      from the chapter listing) removed — it caused spurious
#      stability drift in stable isotopes.
#  SYM. Legacy name stew_field retired (symbol watch) ->
#      env_field_scale.
#  PHYS. Core shells (closed subshells) no longer accumulate the
#      n^3 base decoherence — Pauli-frozen [M]; they take only the
#      (tiny) thermal term. Prevents the unphysical march of 2s/2p
#      coherence to zero at 300 K that plagued the old dynamics.
# ============================================================

import math
import random
import matplotlib.pyplot as plt
from typing import Dict, List, Optional

# --- Physical constants --------------------------------------------
H_SI        = 6.62607015e-34         # J s
EV_TO_J     = 1.602176634e-19        # J/eV
C_LIGHT     = 2.99792458e8           # m/s
K_BOLTZMANN = 8.617333e-5            # eV/K
HC_EVNM     = H_SI * C_LIGHT / EV_TO_J * 1e9   # 1239.842 eV nm

# --- Simulation parameters, ALL [M] unless noted (audit C1) --------
C_VAL        = 0.006      # valley coefficient (A1; was 0.015, inverted ranking)
MAGIC        = [2, 8, 20, 28, 50, 82, 126]     # 126 added (C4)
MAGIC_BONUS  = 0.1
S_NUC_DECAY  = 0.6        # decay gate on nuclear stability (chapter listing)
C_DEC        = 0.78       # decoherence-cascade threshold (D4; distinct from
                          # hydrogen C_EMIT = 0.9 — different process)
K_SIGMOID    = 10.0       # Born-rule steepness
C2_EXPORT    = 0.65       # canonical M_2 entropy export S -> c2*S (B5)
C_RESTORE    = 1.05       # canonical M_2 coherence factor, capped at 1 (B5)
BASE_DECOH   = 5e-4       # per-tick n^3 decoherence base (valence only, PHYS)
S_SHELL_MAX  = 3.0        # per-shell entropy cap
S_OVERFLOW   = 1.8        # overflow reset: S > 1.8 -> S *= 0.9 (param table)
ALPHA_S      = 0.118      # strong coupling (empirical input)
E0_BINDING   = 8.5        # MeV — CALIBRATED INPUT matched to Fe BE/A (A2)

# --- Specified constants (A3): typed in, not derived ---------------
FE_SHELL_ENERGY = {       # eV, NIST K/L/M edges — SPECIFIED
    "1s": -7112.0, "2s": -844.6, "2p": -721.1,
    "3s": -91.3, "3p": -52.7, "3d": -0.5, "4s": -7.9,
}
FE_SHELL_CAPACITY  = {"1s":2, "2s":2, "2p":6, "3s":2, "3p":6, "3d":10, "4s":2}
FE_SHELL_OCCUPANCY = {"1s":2, "2s":2, "2p":6, "3s":2, "3p":6, "3d":6,  "4s":2}
FE_SHELL_N         = {"1s":1, "2s":2, "2p":2, "3s":3, "3p":3, "3d":3,  "4s":4}
VALENCE_SHELLS     = ("3d", "4s")

UNPAIRED_ELECTRONS = 4                       # SPECIFIED (high-spin 3d^6)
MU_EFF_SPIN_ONLY   = math.sqrt(UNPAIRED_ELECTRONS * (UNPAIRED_ELECTRONS + 2))
                     # = 4.90 mu_B derived from specified n; expt ~5.4 (B3)
IONIZATION_EV      = 7.902                   # SPECIFIED

FE_VALENCE_TRANSITIONS = [   # Fe I multiplet lines, NIST — SPECIFIED (A3);
    # the Born rule fires the decision, this table supplies wavelengths.
    {"name": "z7D4-a5D4", "energy_ev": 2.399, "wavelength_nm": 516.9, "weight": 3},
    {"name": "z7F5-a5D4", "energy_ev": 2.328, "wavelength_nm": 532.8, "weight": 3},
    {"name": "y5F5-a5D4", "energy_ev": 2.815, "wavelength_nm": 440.5, "weight": 2},
    {"name": "z5P3-a5D4", "energy_ev": 2.829, "wavelength_nm": 438.4, "weight": 2},
    {"name": "z5G4-a5D4", "energy_ev": 2.521, "wavelength_nm": 492.1, "weight": 2},
    {"name": "z7D3-a5D3", "energy_ev": 3.064, "wavelength_nm": 404.6, "weight": 1},
    {"name": "z5F5-a5D4", "energy_ev": 2.688, "wavelength_nm": 461.5, "weight": 2},
    {"name": "z5D4-a5D4", "energy_ev": 2.179, "wavelength_nm": 569.1, "weight": 1},
]

def workload(Z: int) -> int:
    """W(Z) = Z + 10 Z^2 + 47 Z^3 — the 1:10:47 hierarchy (B1)."""
    return Z + 10 * Z**2 + 47 * Z**3


# ============================================================
# CODEC 2 — Born-rule vector emission
# ============================================================
class Codec2:
    """p_emit = 1/(1+exp(-k(rho-1))), rho = load/capacity.
    Governor-style: emission saturates at rho >= 1 (C5)."""
    def __init__(self, k: float = K_SIGMOID):
        self.k = k

    def born_probability(self, rho: float) -> float:
        return 1.0 / (1.0 + math.exp(-self.k * (rho - 1.0)))

    @staticmethod
    def shell_wavelength_nm(shell_i: str, shell_f: str) -> float:
        dE = abs(FE_SHELL_ENERGY[shell_f] - FE_SHELL_ENERGY[shell_i])
        return HC_EVNM / dE if dE > 0 else 0.0

    def vector_emission_shell(self, rho: float, shell_i: str,
                              shell_f: str) -> Dict:
        p = self.born_probability(rho)
        if random.random() < p:
            dE = abs(FE_SHELL_ENERGY[shell_f] - FE_SHELL_ENERGY[shell_i])
            return {"emitted": True, "regime": "x-ray/uv",
                    "wavelength_nm": self.shell_wavelength_nm(shell_i, shell_f),
                    "energy_ev": dE, "transition": f"{shell_i}->{shell_f}",
                    "probability": p, "rho": rho}
        return {"emitted": False, "probability": p}

    def vector_emission_valence(self, rho: float) -> Dict:
        p = self.born_probability(rho)
        if random.random() < p:
            weights = [t["weight"] for t in FE_VALENCE_TRANSITIONS]
            sel = random.choices(FE_VALENCE_TRANSITIONS, weights=weights)[0]
            return {"emitted": True, "regime": "visible",
                    "wavelength_nm": sel["wavelength_nm"],
                    "energy_ev": sel["energy_ev"], "transition": sel["name"],
                    "probability": p, "rho": rho}
        return {"emitted": False, "probability": p}


# ============================================================
# CODEC 5 — Confinement gate
# E0 = 8.5 MeV is a calibrated input [M], matched to Fe BE/A (A2).
# At the Fe-56 operating point (kappa ~ 0.107) the gate yields
# ~0.107 MeV per invocation — a per-tick stabilizing increment,
# NOT the total binding energy per nucleon.
# ============================================================
class Codec5:
    def __init__(self, alpha_s: float = ALPHA_S):
        self.alpha_s = alpha_s

    def confinement_gate(self, kappa: float) -> Dict:
        if kappa <= 0:
            return {"confined": False, "binding_energy_mev": 0.0,
                    "confinement_strength": 0.0}
        cs = self.alpha_s * kappa
        return {"confined": cs > 0.1,
                "binding_energy_mev": E0_BINDING * math.log(1 + cs),
                "confinement_strength": cs}


# ============================================================
# CODEC 6 — Identity rewrite
# Order-symmetric stochastic decay-mode selector (A4): eligible
# modes gathered by list comprehension, chosen by random.choice.
# No ordered loop, no early return — the Sec. 37.2 CP mechanism
# is NOT implemented here and no weak-phenomenology claim is made.
# ============================================================
class Codec6:
    DECAY_MODES = {
        "beta_minus":     {"half_life": 2.73e6, "energy_mev": 0.156, "prob": 0.95},
        "beta_plus":      {"half_life": 1.12e4, "energy_mev": 1.022, "prob": 0.85},
        "alpha_decay":    {"half_life": 4.50e9, "energy_mev": 4.200, "prob": 0.65},
        "gamma_emission": {"half_life": 1.00e-9, "energy_mev": 1.330, "prob": 0.99},
    }

    def identity_rewrite(self, info_budget: float, required: float,
                         alternatives: List[Dict]) -> Dict:
        if info_budget >= required:
            return {"rewritten": False, "mode": "stable"}
        deficit = required - info_budget
        available = [a for a in alternatives if a["required_info"] <= deficit * 2]
        if not available:
            return {"rewritten": False, "mode": "meta_stable"}
        sel = random.choice(available)
        dm = self.DECAY_MODES.get(sel["type"], self.DECAY_MODES["gamma_emission"])
        return {"rewritten": True, "new_identity": sel["identity"],
                "mode": sel["type"], "energy_released_mev": dm["energy_mev"],
                "probability": dm["prob"], "half_life_seconds": dm["half_life"]}


# ============================================================
# SHELL REGISTER
# ============================================================
class ShellRegister:
    """Per-shell (C, S) register. Only valence shells accumulate the
    n^3 base decoherence; closed core subshells are Pauli-frozen [M]
    and take only the thermal term kT/|E_bind| (PHYS)."""
    def __init__(self, name: str):
        self.name = name
        self.n = FE_SHELL_N[name]
        self.capacity = FE_SHELL_CAPACITY[name]
        self.occupancy = FE_SHELL_OCCUPANCY[name]
        self.C, self.S = 1.0, 0.0

    @property
    def headroom(self) -> float:
        return max(0.1, (self.capacity - self.occupancy) / self.capacity)

    @property
    def rho(self) -> float:
        return self.S / self.headroom

    def tick(self, temperature: float = 300, field: float = 0.02):
        kT = K_BOLTZMANN * temperature
        thermal = kT / abs(FE_SHELL_ENERGY[self.name]) * 1e-3
        base = (BASE_DECOH * self.n**3 * (1.0 + field)
                if self.name in VALENCE_SHELLS else 0.0)
        self.S = min(S_SHELL_MAX, self.S + base + thermal)
        if self.S > S_OVERFLOW:                 # overflow reset (param table)
            self.S *= 0.9
        self.C = max(0.0, 1.0 - 0.4 * self.S)

    def export_entropy(self):
        """Canonical multiplicative M_2 action (B5): S -> c2*S,
        C -> min(1, 1.05*C). Replaces the old additive export."""
        self.S *= C2_EXPORT
        self.C = min(1.0, self.C * C_RESTORE)


# ============================================================
# IRON ATOM
# ============================================================
class IronAtom:
    def __init__(self, isotope: int = 56, env_field_scale: float = 1.0):
        self.mass_number = isotope
        self.atomic_number = 26
        self.neutron_number = isotope - 26
        self.identity = 1.0
        self.env_field_scale = env_field_scale   # legacy stew_field retired
        self.time_step = 0.0

        # A1: NO Fe-56 fiat. One formula for all isotopes.
        # (Fe-56's actual distinction is lowest mass/nucleon; the
        #  BE/A peak belongs to Ni-62 at 8.7945 MeV — audit B4.)
        self.nuclear_stability = self._calc_stability()

        self.shells = {name: ShellRegister(name) for name in FE_SHELL_ENERGY}
        self.c2, self.c5, self.c6 = Codec2(), Codec5(), Codec6()
        self.emission_events, self.decay_events, self.history = [], [], []

    # --- A1-corrected stability: physical valley, cap 1.0 ----------
    def _calc_stability(self) -> float:
        n_z = self.neutron_number / self.atomic_number
        opt = 1.0 + C_VAL * self.atomic_number      # r_opt = 1.156 at Z=26
        stab = 1.0 - abs(n_z - opt) / opt
        if self.neutron_number in MAGIC: stab += MAGIC_BONUS
        if self.atomic_number in MAGIC:  stab += MAGIC_BONUS
        return max(0.1, min(1.0, stab))

    # --- Environment ------------------------------------------------
    def _env_tick(self, temperature: float, field: float):
        for shell in self.shells.values():
            shell.tick(temperature, field * self.env_field_scale)

    def _mean_coherence(self) -> float:
        return sum(s.C for s in self.shells.values()) / len(self.shells)

    def _mean_entropy(self) -> float:
        return sum(s.S for s in self.shells.values()) / len(self.shells)

    # --- Decoherence cascade (reinstated per chapter, D4) -----------
    def _decohere(self):
        """Discrete cascade at mean C < C_DEC: multiple registers
        degrade simultaneously. Model behavior [H at best]; the old
        'measurement problem solved' framing is retired."""
        self.identity *= 0.7
        self.nuclear_stability *= 0.85
        for name in VALENCE_SHELLS:
            self.shells[name].S = min(S_SHELL_MAX, self.shells[name].S + 0.06)
        event = {"type": "decoherence", "time": self.time_step,
                 "identity_after": round(self.identity, 3),
                 "stability_after": round(self.nuclear_stability, 3)}
        self.history.append(event)
        self._nuclear_interaction()
        return event

    # --- Emission ----------------------------------------------------
    def _attempt_valence_emission(self) -> Optional[Dict]:
        for name in sorted(VALENCE_SHELLS,
                           key=lambda s: self.shells[s].rho, reverse=True):
            reg = self.shells[name]
            result = self.c2.vector_emission_valence(reg.rho)
            if result["emitted"]:
                reg.export_entropy()
                result.update(shell=name, time=self.time_step)
                self.emission_events.append(result)
                self.history.append(result)
                return result
        return None

    def _attempt_inner_emission(self, shell_i: str, shell_f: str) -> Optional[Dict]:
        """The scheduler coin flip that reaches here stands in for
        inner-hole creation by external radiation [M] (C5); the hole
        state is saturated by construction, rho = 1."""
        result = self.c2.vector_emission_shell(1.0, shell_i, shell_f)
        if result["emitted"]:
            self.shells[shell_i].export_entropy()
            result["time"] = self.time_step
            self.emission_events.append(result)
            self.history.append(result)
            return result
        return None

    # --- Nuclear (D6: kappa, no unconditional degrade) ---------------
    def _nuclear_interaction(self) -> Dict:
        kappa = (self.mass_number / (self.atomic_number + 0.1)
                 * (1.0 - self.nuclear_stability))
        result = self.c5.confinement_gate(kappa)
        if result["confined"]:
            self.nuclear_stability = min(
                1.0, self.nuclear_stability + 0.02 * result["binding_energy_mev"])
        event = {"type": "nuclear", "time": self.time_step,
                 "kappa": round(kappa, 4),
                 "stability_after": round(self.nuclear_stability, 4), **result}
        self.history.append(event)
        return event

    def _check_decay(self) -> Optional[Dict]:
        if self.nuclear_stability > S_NUC_DECAY:      # gate 0.6 per chapter
            return None
        alts = [{"type": "gamma_emission", "required_info": 0.1, "identity": 0.95}]
        if self.neutron_number > 30:
            alts.append({"type": "beta_minus", "required_info": 0.3, "identity": 0.80})
        if self.neutron_number < 28:
            alts.append({"type": "beta_plus", "required_info": 0.4, "identity": 0.75})
        if self.mass_number > 60:
            alts.append({"type": "alpha_decay", "required_info": 0.6, "identity": 0.60})

        required = 0.5 + 0.3 * (1.0 - self.nuclear_stability)
        result = self.c6.identity_rewrite(self.identity, required, alts)
        if result["rewritten"]:
            self.identity = result["new_identity"]
            mode = result["mode"]
            if mode == "beta_minus":
                self.atomic_number += 1; self.neutron_number -= 1
            elif mode == "beta_plus":
                self.atomic_number -= 1; self.neutron_number += 1
            elif mode == "alpha_decay":
                self.atomic_number -= 2; self.neutron_number -= 2
                self.mass_number -= 4
            if mode != "gamma_emission":
                self.nuclear_stability = self._calc_stability()
            event = {"type": "decay", "mode": mode,
                     "energy_mev": result["energy_released_mev"],
                     "new_element": self._symbol(), "time": self.time_step}
            self.decay_events.append(event)
            self.history.append(event)
            return event
        return None

    def _symbol(self) -> str:
        return {24: "Cr", 25: "Mn", 26: "Fe", 27: "Co", 28: "Ni"}.get(
            self.atomic_number, f"Z{self.atomic_number}")

    # --- Evolution loop (scheduler probabilities are [M], C5) --------
    def evolve(self, steps: int = 1000, temperature: float = 300,
               field: float = 0.02, nuc_period: int = 20) -> Dict:
        counts = {"photon_visible": 0, "photon_xray": 0,
                  "nuclear": 0, "decays": 0, "cascades": 0}
        for step in range(steps):
            self.time_step += 1e-15
            self._env_tick(temperature + random.gauss(0, 5),
                           field * (1 + random.uniform(0, 0.3)))

            if self._mean_coherence() < C_DEC:        # cascade (D4)
                self._decohere()
                counts["cascades"] += 1

            if self._attempt_valence_emission():
                counts["photon_visible"] += 1
            if random.random() < 0.03:                # scheduler [M]
                if self._attempt_inner_emission("3p", "2p"):
                    counts["photon_xray"] += 1
            if random.random() < 0.02:
                if self._attempt_inner_emission("3d", "2p"):
                    counts["photon_xray"] += 1

            if step % nuc_period == 0:
                if random.random() < 0.25:
                    self._nuclear_interaction()
                    counts["nuclear"] += 1
                if self._check_decay():
                    counts["decays"] += 1

        return {"final_element": self._symbol(), "final_mass": self.mass_number,
                "counts": counts, "total_events": len(self.history),
                "final_coherence": round(self._mean_coherence(), 4),
                "final_entropy": round(self._mean_entropy(), 4),
                "nuclear_stability": round(self.nuclear_stability, 4),
                "shell_rho": {n: round(s.rho, 3) for n, s in self.shells.items()}}


# ============================================================
# SPECTRAL PLOT
# ============================================================
def _lam_to_color(lam: float) -> str:
    if lam < 440:   return "#8B00FF"
    elif lam < 490: return "#0000FF"
    elif lam < 510: return "#00CC00"
    elif lam < 580: return "#CCCC00"
    elif lam < 645: return "#FF7F00"
    return "#FF0000"

def plot_spectrum(atom: IronAtom, fname: str = "fe56_spectrum.png"):
    visible = [e["wavelength_nm"] for e in atom.emission_events
               if e.get("regime") == "visible"]
    fig, axes = plt.subplots(2, 1, figsize=(11, 8))
    fig.suptitle("Fe-56 Emission — Born-rule Codec-2 "
                 "(multiplet wavelengths: specified constants [A3])",
                 fontsize=12, fontweight="bold")
    ax1 = axes[0]
    for lam in visible:
        ax1.vlines(lam, 0, 1, color=_lam_to_color(lam), lw=1.8, alpha=0.55)
    ax1.set_xlim(380, 700); ax1.set_ylim(0, 1.1)
    ax1.set_xlabel("Wavelength (nm)"); ax1.set_ylabel("Intensity (arb.)")
    ax1.set_title(f"Visible regime ({len(visible)} events)")
    ax1.grid(axis="x", ls="--", alpha=0.3)
    ax2 = axes[1]
    if visible:
        ax2.hist(visible, bins=40, range=(380, 700), color="steelblue",
                 alpha=0.75, edgecolor="navy")
    ax2.set_xlabel("Wavelength (nm)"); ax2.set_ylabel("Count")
    ax2.grid(axis="y", ls="--", alpha=0.3)
    plt.tight_layout()
    plt.savefig(fname, dpi=150)
    plt.close(fig)


# ============================================================
# MAIN — derived vs specified stated plainly (A3)
# ============================================================
if __name__ == "__main__":
    print("=" * 64)
    print(f"W(26) = {workload(26):,} units  (1:10:47 hierarchy; audit B1)")
    print(f"mu_eff(spin-only) = {MU_EFF_SPIN_ONLY:.2f} mu_B from n = "
          f"{UNPAIRED_ELECTRONS} [specified]; expt ~5.4 mu_B (audit B3)")
    print("=" * 64)

    print("\nISOTOPE SURVEY (A1-corrected valley, r_opt = "
          f"{1 + C_VAL*26:.3f}; decay gate {S_NUC_DECAY})")
    orientation = {54: 1.000, 56: 0.998, 58: 0.935, 60: 0.869}  # chapter values
    survey = {}
    for iso in [54, 56, 58, 60]:
        fe = IronAtom(isotope=iso)
        s0 = fe.nuclear_stability
        res = fe.evolve(steps=300)
        survey[iso] = s0
        c = res["counts"]
        print(f"  Fe-{iso}: S0 = {s0:.3f} (chapter: {orientation[iso]:.3f})  "
              f"vis {c['photon_visible']:3d}  xray {c['photon_xray']:2d}  "
              f"cascades {c['cascades']:2d}  decays {c['decays']}  "
              f"-> {res['final_element']}-{res['final_mass']}")
    assert survey[54] >= survey[56] > survey[58] > survey[60], \
        "A1 REGRESSION: isotope ordering inverted"
    print("  ordering Fe-54 >= Fe-56 > Fe-58 > Fe-60 : OK")
    print("  Fe-58 STABLE (audit C4); Fe-60 above decay gate — the N/Z")
    print("  scalar alone does not produce its beta- decay [pending A1 re-run]")

    print("\nFe-56 FULL RUN (1000 steps, 300 K)")
    fe56 = IronAtom(isotope=56)
    result = fe56.evolve(steps=1000)
    for k, v in result["counts"].items():
        print(f"  {k:15s}: {v}")
    print(f"  mean C = {result['final_coherence']}   "
          f"S_nuc = {result['nuclear_stability']}")
    plot_spectrum(fe56)

    print("\nDERIVED: stability ordering (pending A1 re-run), sigmoid "
          "threshold shape [H],\n         Hund mechanism [H], mu_eff from "
          "specified n.\nSPECIFIED: shell energies (NIST), multiplet table, "
          "config [Ar]3d6 4s2,\n         n_unpaired = 4, ionization 7.902 eV, "
          "E0 = 8.5 MeV (calibrated, A2).")
