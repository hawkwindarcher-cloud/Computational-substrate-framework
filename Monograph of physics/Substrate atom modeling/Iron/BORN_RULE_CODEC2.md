# Born Rule as Register Overflow Sigmoid — Codec-2 Implementation Note

**Jaroslav Petřina** · Computational Substrate Framework · March 2025

---

## The Problem with Linear Emission Probability

Early demonstrators (Fe atom v1, Chlorophyll) used a linear proxy for photon emission probability:

```python
emission_prob = min(1.0, freq_thz / (crit_prob * 1000))
```

This captures the qualitative behaviour but has no grounding in the framework's own
architecture. It imports an assumption (probability proportional to frequency) rather than
deriving it from register dynamics. The Balmer demonstrator exposed the correct path:
emission should trigger when accumulated load exceeds shell capacity — not when frequency
crosses a threshold.

---

## The Register Load Ratio

Each shell register carries two state variables:

| Variable | Symbol | Meaning |
|----------|--------|---------|
| Entropy  | `S`    | Accumulated environmental coupling, decoherence load |
| Headroom | `h`    | Normalised available capacity: `(capacity − occupancy) / capacity` |

Their ratio defines the **load factor**:

```
ρ = S / h
```

- `ρ < 1` : register below saturation — system evolves coherently, emission suppressed  
- `ρ ≥ 1` : register at or above capacity — classical collapse, emission permitted  

This is the same decision boundary stated in the monograph:

```
ρ < 1  →  QM regime   (coherent evolution)
ρ ≥ 1  →  Collapse    (emission / identity rewrite)
```

---

## The Sigmoid

A hard threshold at `ρ = 1` would produce discontinuous, unphysical behaviour.
The correct implementation is a logistic function centred on the transition point:

```
p_emit = 1 / (1 + exp(−k · (ρ − 1)))
```

| Parameter | Role |
|-----------|------|
| `k`       | Sharpness of the quantum-to-classical transition. `k → ∞` recovers a hard threshold; `k ~ 10` gives a physically smooth crossover. |
| `ρ − 1`   | Signed distance from the saturation boundary. |

### Behaviour

```
ρ = 0.5  →  p ≈ 0.007   (strongly coherent, emission rare)
ρ = 0.8  →  p ≈ 0.119   (approaching threshold)
ρ = 1.0  →  p = 0.500   (at capacity, coin-flip)
ρ = 1.2  →  p ≈ 0.881   (over capacity, emission likely)
ρ = 1.5  →  p ≈ 0.993   (saturated, emission near-certain)
```

The sigmoid is formally identical to the Born rule emission probability derived in the
monograph from the six-register architecture:

```
p_emit = 1 / (1 + exp(−k · (L/K_cap − 1)))
```

where `L` is the Load register and `K_cap` is the architectural capacity constant.
`S/h` is the per-shell realisation of the same ratio.

---

## Python Implementation

```python
class Codec2:
    def __init__(self, k_sigmoid: float = 10.0):
        self.k = k_sigmoid

    def born_probability(self, rho: float) -> float:
        return 1.0 / (1.0 + math.exp(-self.k * (rho - 1.0)))

    def vector_emission_valence(self, rho: float) -> dict:
        p = self.born_probability(rho)
        if random.random() < p:
            # select transition from multiplet table — wavelength emerges,
            # it is not an input to the probability calculation
            ...
```

The critical design point: **wavelength is not an argument to the probability function**.
Emission probability is set entirely by register state `ρ`. Which transition fires is
determined afterwards by the multiplet table weighted by oscillator strength proxies.
This means spectral lines are emergent from the energy architecture, not assumed.

---

## n³ Decoherence Rate

The rate at which `S` accumulates (and therefore how quickly `ρ` approaches 1) scales
with principal quantum number:

```python
dS = base_rate * (n ** 3) * (1 + field) + thermal_coupling
```

Physical motivation: outer shells have larger orbital radii, couple more strongly to the
environmental field, and lose coherence faster. This matches the known scaling of Rydberg
atom lifetimes (~n³) and produces the correct qualitative intensity envelope — inner
shells saturate to classical behaviour (`ρ ≫ 1`), outer valence shells sit near the
transition region and respond to environmental perturbation.

In the Fe-56 simulation this gives:

```
Shell   ρ (typical, 300 K)
─────────────────────────
1s      ~5        fully classical (filled, no headroom)
2s/2p   ~30       saturated core
3p      ~2–8      intermediate
3d      ~0.7–1.2  at transition boundary  ← optical emission here
4s      ~0–0.3    loosely coupled, low load
```

The 3d shell sitting at `ρ ~ 1` is not tuned — it is a consequence of the n³ rate,
the partial occupancy (6 of 10 electrons, giving real headroom), and iron's first
ionisation energy of 7.9 eV setting the thermal coupling scale.

---

## Relationship to Prior Demonstrators

| Code | Emission trigger | Wavelength source |
|------|-----------------|-------------------|
| Fe v1 | `random.random() < linear(freq)` | sampled from uniform range |
| Balmer | `while C > C_crit` (implicit ρ) | Rydberg formula — emergent |
| Chlorophyll | `random.random() < absorption_cross_section` | absorption peak table |
| **Fe v2** | **Born sigmoid on ρ = S/h** | **NIST multiplet table — emergent** |

The Balmer code was the conceptual bridge: it already used a threshold on coherence
accumulation to gate emission, and derived wavelengths from energy level differences
rather than assuming them. Fe v2 replaces the hard threshold with the sigmoid,
generalises the coherence variable to per-shell `ρ`, and replaces the Rydberg formula
with the multiplet table for the many-electron case.

---

## Open: Oscillator Strength Normalisation

Transition *selection* currently uses integer weight proxies in the multiplet table.
Quantitative intensity ratios matching NIST data require replacement with Einstein
A-coefficients. This is a calibration step, not a structural change — the sigmoid
machinery is independent of which weights populate the table.

```python
FE_VALENCE_TRANSITIONS = [
    {"name": "z7D4→a5D4", "wavelength_nm": 516.9,
     "weight": 3},          # ← replace with A_ki / sum(A_ki)
    ...
]
```

When A-coefficients are in place, the simulation becomes quantitatively predictive
rather than qualitatively demonstrative.

---

*Part of the Computational Substrate Framework validation series.*  
*Repository: [github.com/hawkwindarcher-cloud/Computational-substrate-framework](https://github.com/hawkwindarcher-cloud/Computational-substrate-framework)*
