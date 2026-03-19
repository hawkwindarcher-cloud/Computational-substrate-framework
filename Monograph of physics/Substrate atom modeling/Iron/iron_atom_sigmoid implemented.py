import math
import random
import matplotlib.pyplot as plt
from typing import Dict, List, Optional

# ============================================================
# PHYSICAL CONSTANTS
# ============================================================
H_SI        = 6.62607015e-34        # J·s
EV_TO_J     = 1.602176634e-19       # J/eV
C_LIGHT     = 2.99792458e8          # m/s
K_BOLTZMANN = 8.617333e-5           # eV/K

# ============================================================
# IRON SHELL MODEL
# Binding energies (eV, from vacuum) — K/L/M edges, NIST data
# Used for deep-shell (X-ray) transition wavelengths
# ============================================================
FE_SHELL_ENERGY = {
    "1s": -7112.0,
    "2s":  -844.6,
    "2p":  -721.1,
    "3s":   -91.3,
    "3p":   -52.7,
    "3d":    -0.5,   # approximate centre of multiplet
    "4s":    -7.9,   # first ionization ~7.9024 eV
}

FE_SHELL_CAPACITY  = {"1s":2, "2s":2, "2p":6, "3s":2, "3p":6, "3d":10, "4s":2}
FE_SHELL_OCCUPANCY = {"1s":2, "2s":2, "2p":6, "3s":2, "3p":6, "3d":6,  "4s":2}
FE_SHELL_N         = {"1s":1, "2s":2, "2p":2, "3s":3, "3p":3, "3d":3,  "4s":4}

# ============================================================
# FE I VALENCE TRANSITIONS — real NIST lines, visible regime
# These live within the 3d^6 4s^2 / 3d^7 4s multiplet structure.
# Deep-shell (X-ray) transitions emerge directly from shell
# energy differences; visible lines require the multiplet table.
# ============================================================
FE_VALENCE_TRANSITIONS = [
    {"name": "z7D4→a5D4", "energy_ev": 2.399, "wavelength_nm": 516.9, "weight": 3},
    {"name": "z7F5→a5D4", "energy_ev": 2.328, "wavelength_nm": 532.8, "weight": 3},
    {"name": "y5F5→a5D4", "energy_ev": 2.815, "wavelength_nm": 440.5, "weight": 2},
    {"name": "z5P3→a5D4", "energy_ev": 2.829, "wavelength_nm": 438.4, "weight": 2},
    {"name": "z5G4→a5D4", "energy_ev": 2.521, "wavelength_nm": 492.1, "weight": 2},
    {"name": "z7D3→a5D3", "energy_ev": 3.064, "wavelength_nm": 404.6, "weight": 1},
    {"name": "z5F5→a5D4", "energy_ev": 2.688, "wavelength_nm": 461.5, "weight": 2},
    {"name": "z5D4→a5D4", "energy_ev": 2.179, "wavelength_nm": 569.1, "weight": 1},
]

# ============================================================
# CODEC 2 — Vector emission, Born rule
# ============================================================
class Codec2:
    """
    Photon emission via Born rule sigmoid.
    p_emit = 1 / (1 + exp(-k * (rho - 1)))
    where rho = L / K_cap  (load over capacity).

    Below saturation (rho < 1): system stays coherent, emission suppressed.
    At saturation (rho >= 1): emission fires with rising probability.
    This is the quantum-to-classical transition at the register level.
    """
    def __init__(self, k_sigmoid: float = 10.0):
        self.k = k_sigmoid

    def born_probability(self, rho: float) -> float:
        return 1.0 / (1.0 + math.exp(-self.k * (rho - 1.0)))

    @staticmethod
    def shell_wavelength_nm(shell_i: str, shell_f: str) -> float:
        """Deep-shell transition wavelength from binding energy difference."""
        dE = abs(FE_SHELL_ENERGY[shell_f] - FE_SHELL_ENERGY[shell_i])
        if dE <= 0:
            return 0.0
        return (H_SI * C_LIGHT / (dE * EV_TO_J)) * 1e9

    def vector_emission_shell(self, rho: float,
                               shell_i: str, shell_f: str) -> Dict:
        """Deep-shell (X-ray / UV) emission."""
        p = self.born_probability(rho)
        if random.random() < p:
            lam = self.shell_wavelength_nm(shell_i, shell_f)
            dE  = abs(FE_SHELL_ENERGY[shell_f] - FE_SHELL_ENERGY[shell_i])
            return {
                "emitted": True, "regime": "x-ray/uv",
                "wavelength_nm": lam, "energy_ev": dE,
                "transition": f"{shell_i}→{shell_f}",
                "probability": p, "rho": rho,
            }
        return {"emitted": False, "probability": p}

    def vector_emission_valence(self, rho: float) -> Dict:
        """
        Valence (visible) emission.
        Born rule fires the decision; transition is drawn from
        FE_VALENCE_TRANSITIONS weighted by oscillator strength proxy.
        Wavelengths emerge from the multiplet table — not hardcoded
        into the trigger, only into the energy dictionary.
        """
        p = self.born_probability(rho)
        if random.random() < p:
            weights  = [t["weight"] for t in FE_VALENCE_TRANSITIONS]
            total_w  = sum(weights)
            r        = random.uniform(0, total_w)
            cumul    = 0.0
            selected = FE_VALENCE_TRANSITIONS[-1]
            for t in FE_VALENCE_TRANSITIONS:
                cumul += t["weight"]
                if r <= cumul:
                    selected = t
                    break
            return {
                "emitted": True, "regime": "visible",
                "wavelength_nm": selected["wavelength_nm"],
                "energy_ev":     selected["energy_ev"],
                "transition":    selected["name"],
                "probability":   p, "rho": rho,
            }
        return {"emitted": False, "probability": p}


# ============================================================
# CODEC 5 — Strong confinement
# ============================================================
class Codec5:
    def __init__(self, alpha_s: float = 0.118):
        self.alpha_s = alpha_s

    def confinement_gate(self, curvature: float) -> Dict:
        if curvature <= 0:
            return {"confined": False, "binding_energy_mev": 0.0,
                    "confinement_strength": 0.0}
        cs  = self.alpha_s * curvature
        be  = 8.5 * math.log(1 + cs)
        return {"confined": cs > 0.1, "binding_energy_mev": be,
                "confinement_strength": cs}


# ============================================================
# CODEC 6 — Identity rewrite (nuclear decay)
# ============================================================
class Codec6:
    DECAY_MODES = {
        "beta_minus":    {"half_life": 2.73e6, "energy_mev": 0.156, "prob": 0.95},
        "beta_plus":     {"half_life": 1.12e4, "energy_mev": 1.022, "prob": 0.85},
        "alpha_decay":   {"half_life": 4.50e9, "energy_mev": 4.200, "prob": 0.65},
        "gamma_emission":{"half_life": 1.00e-9,"energy_mev": 1.330, "prob": 0.99},
    }

    def identity_rewrite(self, info_budget: float, required: float,
                         alternatives: List[Dict]) -> Dict:
        if info_budget >= required:
            return {"rewritten": False, "mode": "stable"}
        deficit   = required - info_budget
        available = [a for a in alternatives if a["required_info"] <= deficit * 2]
        if not available:
            return {"rewritten": False, "mode": "meta_stable"}
        sel  = random.choice(available)
        dm   = self.DECAY_MODES.get(sel["type"], self.DECAY_MODES["gamma_emission"])
        return {
            "rewritten": True,
            "new_identity":       sel["identity"],
            "mode":               sel["type"],
            "energy_released_mev":dm["energy_mev"],
            "probability":        dm["prob"],
            "half_life_seconds":  dm["half_life"],
        }


# ============================================================
# SHELL REGISTER
# ============================================================
class ShellRegister:
    """
    Per-shell coherence / entropy register.
    Decoherence rate scales as n^3 (outer shells couple more strongly
    to environment — same physical argument as Rydberg atom lifetime).
    rho = S / K_cap drives the Born rule in Codec2.
    """
    def __init__(self, name: str):
        self.name     = name
        self.n        = FE_SHELL_N[name]
        self.capacity = FE_SHELL_CAPACITY[name]
        self.occupancy= FE_SHELL_OCCUPANCY[name]
        self.C        = 1.0   # coherence
        self.S        = 0.0   # accumulated load / entropy

    @property
    def headroom(self) -> float:
        """Normalised available capacity — K_cap in the Born rule."""
        return max(0.1, (self.capacity - self.occupancy) / self.capacity)

    @property
    def rho(self) -> float:
        """Load / capacity ratio."""
        return self.S / self.headroom

    def tick(self, temperature: float = 300, field: float = 0.02):
        """
        Accumulate entropy.  Rate = base_n3 + thermal coupling.
        Thermal coupling is proportional to kT / |binding energy|:
        loosely-bound outer shells couple more to thermal bath.
        """
        base       = 5e-4 * (self.n ** 3)
        kT         = K_BOLTZMANN * temperature
        thermal    = kT / abs(FE_SHELL_ENERGY[self.name])  # dimensionless
        dS         = base * (1.0 + field) + thermal * 1e-3
        self.S     = min(3.0, self.S + dS)
        self.C     = max(0.0, 1.0 - self.S * 0.4)

    def export_entropy(self, fraction: float = 0.35):
        """Restore register after emission — photon carries entropy out."""
        exported  = min(self.S, fraction * self.S + 0.05)
        self.S   -= exported
        self.C    = min(1.0, self.C + exported * 0.5)
        return exported


# ============================================================
# IRON ATOM
# ============================================================
class IronAtom:
    """
    Fe isotope simulation.

    Architecture:
      - Seven ShellRegisters carry (C, S, rho) state.
      - Codec2 Born rule triggers emission when rho >= 1.
        * Valence shells (3d, 4s) → visible multiplet lines.
        * Inner shells        → X-ray / UV transitions.
      - Codec5 handles nuclear confinement (strong force proxy).
      - Codec6 handles nuclear decay (identity rewrite).
      - Two timescales:
          electronic  : every step  (dt ~ 1e-15 s)
          nuclear     : every N_nuc electronic steps
    """

    def __init__(self, isotope: int = 56, stew_field: float = 1.0):
        self.mass_number    = isotope
        self.atomic_number  = 26
        self.neutron_number = isotope - 26
        self.identity       = 1.0
        self.stew_field     = stew_field
        self.time_step      = 0.0

        # Fe-56 = peak of binding-energy curve, maximally stable.
        # All other isotopes use the N/Z formula.
        self.nuclear_stability = (1.0 if (self.atomic_number == 26
                                          and isotope == 56)
                                  else self._calc_stability())

        # Shell registers
        self.shells = {name: ShellRegister(name)
                       for name in FE_SHELL_ENERGY}

        # Codecs
        self.c2 = Codec2(k_sigmoid=10.0)
        self.c5 = Codec5()
        self.c6 = Codec6()

        # Observables
        self.emission_events = []
        self.decay_events    = []
        self.history         = []

        print(f"Fe-{isotope}  nuclear_stability={self.nuclear_stability:.3f}  "
              f"stew={stew_field}")

    # ----------------------------------------------------------
    def _calc_stability(self) -> float:
        n_z      = self.neutron_number / self.atomic_number
        opt      = 1.0 + 0.015 * self.atomic_number
        stab     = 1.0 - abs(n_z - opt) / opt
        for magic in [2, 8, 20, 28, 50, 82]:
            if self.neutron_number == magic: stab += 0.1
            if self.atomic_number  == magic: stab += 0.1
        return max(0.1, min(0.95, stab))   # Fe-56 only reaches 1.0

    # ----------------------------------------------------------
    def _env_tick(self, temperature: float, field: float):
        for shell in self.shells.values():
            shell.tick(temperature, field)

    # ----------------------------------------------------------
    def _attempt_valence_emission(self) -> Optional[Dict]:
        """
        Try emission from whichever valence shell (3d or 4s)
        has the higher rho first.
        Born rule decides; multiplet table supplies wavelength.
        """
        valence = ["3d", "4s"]
        valence.sort(key=lambda s: self.shells[s].rho, reverse=True)

        for shell_name in valence:
            reg    = self.shells[shell_name]
            result = self.c2.vector_emission_valence(reg.rho)
            if result["emitted"]:
                reg.export_entropy()
                result["shell"]    = shell_name
                result["time"]     = self.time_step
                self.emission_events.append(result)
                self.history.append(result)
                return result
        return None

    # ----------------------------------------------------------
    def _attempt_inner_emission(self, shell_i: str, shell_f: str) -> Optional[Dict]:
        """X-ray / UV emission between inner shells."""
        reg    = self.shells[shell_i]
        result = self.c2.vector_emission_shell(reg.rho, shell_i, shell_f)
        if result["emitted"]:
            reg.export_entropy(fraction=0.5)
            result["time"] = self.time_step
            self.emission_events.append(result)
            self.history.append(result)
            return result
        return None

    # ----------------------------------------------------------
    def _nuclear_interaction(self) -> Dict:
        curvature = (1.5 * (1.0 - self.nuclear_stability)
                     + 0.5 * self._mean_entropy())
        result    = self.c5.confinement_gate(curvature)
        if result["confined"]:
            self.nuclear_stability = min(
                1.0, self.nuclear_stability
                     + 0.1 * result["confinement_strength"])
        else:
            self.nuclear_stability *= 0.95

        event = {"type": "nuclear", "time": self.time_step,
                 "stability_after": self.nuclear_stability, **result}
        self.history.append(event)
        return event

    # ----------------------------------------------------------
    def _check_decay(self) -> Optional[Dict]:
        if self.nuclear_stability > 0.85:
            return None

        alts = [{"type": "gamma_emission",
                 "required_info": 0.1, "identity": 0.95}]
        if self.neutron_number > 30:
            alts.append({"type": "beta_minus",
                         "required_info": 0.3, "identity": 0.80})
        if self.neutron_number < 28:
            alts.append({"type": "beta_plus",
                         "required_info": 0.4, "identity": 0.75})
        if self.mass_number > 60:
            alts.append({"type": "alpha_decay",
                         "required_info": 0.6, "identity": 0.60})

        required = 0.5 + 0.3 * (1.0 - self.nuclear_stability)
        result   = self.c6.identity_rewrite(self.identity, required, alts)

        if result["rewritten"]:
            self.identity = result["new_identity"]
            mode = result["mode"]
            if mode == "beta_minus":
                self.atomic_number  += 1; self.neutron_number -= 1
            elif mode == "beta_plus":
                self.atomic_number  -= 1; self.neutron_number += 1
            elif mode == "alpha_decay":
                self.atomic_number  -= 2; self.neutron_number -= 2
                self.mass_number    -= 4
            if mode != "gamma_emission":
                self.nuclear_stability = self._calc_stability()

            event = {"type": "decay", "mode": mode,
                     "energy_mev": result["energy_released_mev"],
                     "new_element": self._symbol(),
                     "time": self.time_step}
            self.decay_events.append(event)
            self.history.append(event)
            return event
        return None

    # ----------------------------------------------------------
    def _mean_entropy(self) -> float:
        return sum(s.S for s in self.shells.values()) / len(self.shells)

    def _mean_coherence(self) -> float:
        return sum(s.C for s in self.shells.values()) / len(self.shells)

    def _symbol(self) -> str:
        return {25:"Mn", 26:"Fe", 27:"Co", 28:"Ni"}.get(
            self.atomic_number, f"Z{self.atomic_number}")

    # ----------------------------------------------------------
    def evolve(self, steps: int = 1000,
               temperature: float = 300,
               field: float = 0.02,
               nuc_period: int = 20) -> Dict:
        """
        Two-timescale loop.
        Electronic : every step  (femtosecond)
        Nuclear    : every nuc_period steps
        """
        counts = {"photon_visible":0, "photon_xray":0,
                  "nuclear":0, "decays":0}

        for step in range(steps):
            self.time_step += 1e-15

            # --- Environmental decoherence ---
            self._env_tick(
                temperature=temperature + random.gauss(0, 5),
                field=field * (1 + random.uniform(0, 0.3))
            )

            # --- Valence emission (visible, always attempted) ---
            ev = self._attempt_valence_emission()
            if ev:
                counts["photon_visible"] += 1

            # --- Inner-shell emission (X-ray, lower probability) ---
            # 3p → 2p  (Fe Lα analog, UV/soft X-ray)
            if random.random() < 0.03:
                ev = self._attempt_inner_emission("3p", "2p")
                if ev:
                    counts["photon_xray"] += 1

            # 3d → 2p  (valence to L-shell, EUV)
            if random.random() < 0.02:
                ev = self._attempt_inner_emission("3d", "2p")
                if ev:
                    counts["photon_xray"] += 1

            # --- Nuclear timescale ---
            if step % nuc_period == 0:
                if random.random() < 0.25:
                    self._nuclear_interaction()
                    counts["nuclear"] += 1
                decay = self._check_decay()
                if decay:
                    counts["decays"] += 1

        return {
            "initial_element": "Fe",
            "final_element":   self._symbol(),
            "final_mass":      self.mass_number,
            "counts":          counts,
            "total_events":    len(self.history),
            "final_coherence": round(self._mean_coherence(), 4),
            "final_entropy":   round(self._mean_entropy(),   4),
            "nuclear_stability": round(self.nuclear_stability, 4),
            "shell_rho": {n: round(s.rho, 3)
                          for n, s in self.shells.items()},
        }

    # ----------------------------------------------------------
    def state(self) -> Dict:
        return {
            "element":           self._symbol(),
            "mass_number":       self.mass_number,
            "atomic_number":     self.atomic_number,
            "nuclear_stability": round(self.nuclear_stability, 4),
            "identity":          round(self.identity, 4),
            "mean_coherence":    round(self._mean_coherence(), 4),
            "mean_entropy":      round(self._mean_entropy(),   4),
            "shell_rho": {n: round(s.rho, 3)
                          for n, s in self.shells.items()},
        }


# ============================================================
# SPECTRAL PLOT
# ============================================================
def _lam_to_color(lam: float) -> str:
    if   lam < 380: return "#9400D3"
    elif lam < 440: return "#8B00FF"
    elif lam < 490: return "#0000FF"
    elif lam < 510: return "#00CC00"
    elif lam < 580: return "#CCCC00"
    elif lam < 645: return "#FF7F00"
    else:           return "#FF0000"


def plot_spectrum(atom: IronAtom, title: str = "Fe Emission Spectrum"):
    visible = [e["wavelength_nm"] for e in atom.emission_events
               if e.get("regime") == "visible"]
    xray    = [e["wavelength_nm"] for e in atom.emission_events
               if e.get("regime") == "x-ray/uv" and
               0 < e["wavelength_nm"] < 2000]

    fig, axes = plt.subplots(2, 1, figsize=(11, 8))
    fig.suptitle(title, fontsize=13, fontweight="bold")

    # --- Visible spectral lines ---
    ax1 = axes[0]
    for lam in visible:
        ax1.vlines(lam, 0, 1, color=_lam_to_color(lam),
                   linewidth=1.8, alpha=0.55)
    ax1.set_xlim(380, 700)
    ax1.set_ylim(0, 1.1)
    ax1.set_xlabel("Wavelength (nm)")
    ax1.set_ylabel("Intensity (arb.)")
    ax1.set_title(f"Visible regime  ({len(visible)} events)  "
                  f"— Born-rule Codec-2, Fe I multiplet table")
    ax1.grid(axis="x", linestyle="--", alpha=0.3)

    # Mark known strong lines for reference
    known = {"Hα(656)":656, "Hβ(486)":486,
             "Fe 517":516.9, "Fe 533":532.8,
             "Fe 441":440.5, "Fe 438":438.4}
    for label, lam in known.items():
        ax1.axvline(lam, color="gray", linewidth=0.6, linestyle=":",
                    alpha=0.6)
        ax1.text(lam + 1, 1.02, label, fontsize=6, color="gray",
                 rotation=90, va="bottom")

    # --- Emission histogram ---
    ax2 = axes[1]
    if visible:
        ax2.hist(visible, bins=40, range=(380, 700),
                 color="steelblue", alpha=0.75, edgecolor="navy",
                 label="visible")
    ax2.set_xlabel("Wavelength (nm)")
    ax2.set_ylabel("Count")
    ax2.set_title("Emission density — visible regime")
    ax2.grid(axis="y", linestyle="--", alpha=0.3)
    ax2.legend()

    plt.tight_layout()
    plt.show()

    # Summary
    print(f"\nVisible emissions : {len(visible)}")
    if xray:
        print(f"X-ray/UV events  : {len(xray)}")
    if visible:
        print(f"Wavelength range : "
              f"{min(visible):.1f} – {max(visible):.1f} nm")

    transitions: Dict[str, int] = {}
    for e in atom.emission_events:
        t = e.get("transition", "?")
        transitions[t] = transitions.get(t, 0) + 1
    print("\nTransition counts:")
    for t, c in sorted(transitions.items(), key=lambda x: -x[1]):
        print(f"  {t:30s}  {c:5d}")


# ============================================================
# ISOTOPE COMPARISON DEMO
# ============================================================
def demo_isotopes():
    print("\n" + "=" * 60)
    print("ISOTOPE SURVEY  Fe-54 / Fe-56 / Fe-58 / Fe-60")
    print("=" * 60)
    isotopes = [54, 56, 58, 60]
    for iso in isotopes:
        print(f"\n--- Fe-{iso} ---")
        fe    = IronAtom(isotope=iso, stew_field=1.0)
        res   = fe.evolve(steps=300, temperature=300)
        c     = res["counts"]
        print(f"  visible photons : {c['photon_visible']}")
        print(f"  X-ray/UV photons: {c['photon_xray']}")
        print(f"  nuclear events  : {c['nuclear']}")
        print(f"  decays          : {c['decays']}")
        print(f"  final element   : {res['final_element']}-{res['final_mass']}")
        print(f"  stability       : {res['nuclear_stability']}")
        print(f"  shell ρ         : {res['shell_rho']}")


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Fe-56  Born-Rule Codec-2  |  n³ decoherence  |  two-timescale")
    print("=" * 60 + "\n")

    fe56 = IronAtom(isotope=56, stew_field=1.0)
    result = fe56.evolve(steps=1000, temperature=300, field=0.02)

    print(f"\n--- Evolution complete ---")
    print(f"  Visible photons  : {result['counts']['photon_visible']}")
    print(f"  X-ray/UV photons : {result['counts']['photon_xray']}")
    print(f"  Nuclear events   : {result['counts']['nuclear']}")
    print(f"  Decays           : {result['counts']['decays']}")
    print(f"  Total events     : {result['total_events']}")
    print(f"  Final coherence  : {result['final_coherence']}")
    print(f"  Final entropy    : {result['final_entropy']}")
    print(f"  Nuclear stability: {result['nuclear_stability']}")
    print(f"\n  Shell ρ values:")
    for shell, rho in result["shell_rho"].items():
        bar = "█" * int(min(rho, 3.0) * 10)
        print(f"    {shell:4s}  ρ={rho:.3f}  {bar}")

    plot_spectrum(fe56, "Fe-56 Emission Spectrum — Born-Rule Codec-2")

    demo_isotopes()
