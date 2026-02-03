# Codec Library - Python Implementation

**Six-Register Computational Substrate Framework**

Complete Python implementation of the codec matrix algebra (M₁ through M₆) for the stew-field register architecture.

## Installation

No dependencies beyond NumPy:

```python
pip install numpy
```

## Quick Start

```python
from codec_library_reference import *

# Create codec instances
higgs = Codec1(coherence=0.9, entropy=0.1)
em = Codec2(coherence=0.5, entropy=0.99)

# Scalar mass calculation
E_scalar = higgs.scalar_mass(sigma=1e-10)

# Photon emission
photon = em.vector_emission(freq_thz=500)
print(photon)  # {'type': 'photon', 'energy_ev': 2.07, 'status': 'emitted'}
```

## Architecture

### Six Fundamental Registers

Every codec operates on the state vector **R = [Id, Φ, X, S, C, L]ᵀ**:

| Register | Symbol | Physical Meaning |
|----------|--------|------------------|
| Identity | Id | Particle identity checksum |
| Phase | Φ | Quantum phase (fermion) |
| Spatial | X | Position register (compressed) |
| Entropy | S | System disorder |
| Coherence | C | Quantum coherence |
| Load | L | Energy accumulator |

### Matrix Operations

Each codec implements: **R_new = M_codec(params) @ R_old**

```python
# Get explicit 6×6 matrix
M1 = get_codec_matrix(1, {'lambda_s': 0.1})
print(M1)  # 6×6 NumPy array
```

## The Six Codecs

### Codec 1: Scalar Mass (Higgs Mechanism)

**Cost: 1** (baseline)

```python
c1 = Codec1(coherence=0.9, entropy=0.1)

# Scalar mass from coherence persistence
E_q = c1.scalar_mass(sigma=1e-10, lambda_s=0.1)

# Higgs boson emission
higgs_boson = c1.higgs_emission(coherence_threshold=0.8)
```

**Matrix M₁:**
- S → (1 - λₛ)S — entropy reduction
- C → (1 + μ₁)C — coherence boost  
- L → L + η₁S — load cost

**Physics:**
- τₛ = σ²/(η·C_Q) persistence time
- E_q = h/τₛ energy quantization
- Mass emerges from coherence persistence

### Codec 2: Vector Emission (Photons)

**Cost: 10**

```python
c2 = Codec2(coherence=0.5, entropy=0.99)

# Emit photon
photon = c2.vector_emission(freq_thz=500, crit_entropy=0.98)
# Returns: {'type': 'photon', 'energy_ev': 2.07, 'wavelength_nm': 600, ...}

# Absorb photon
c2.absorb_photon(energy_ev=2.5)
```

**Matrix M₂:**
- S → c₂S (c₂ ≈ 0.90)
- C → d₂C (d₂ ≈ 1.05)
- L → L + ε₂f

**Physics:**
- Immediate emission (no storage)
- E = hν (frequency-dependent)
- Vector channel (directional)

### Codec 3: Tensor Delay (Gravitons)

**Cost: 47** (why gravity is weak)

```python
c3 = Codec3(coherence=0.8, entropy=0.2)

# Gravitational wave
gw = c3.tensor_delay(lambda_gw=1e3, g_strength=1e-8, kappa=0.01)
# Returns: {'type': 'graviton', 'delay_s': 1e53, 'energy_ev': 4.1e-68, ...}
```

**Matrix M₃:**
- Φ → (1 + α₃)Φ — phase coupling
- X → (1 + γ₃)X — spatial coupling
- S → (1 - κg)S — entropy reduction
- All coefficients ~ 10⁻⁸ (extreme weakness)

**Physics:**
- 2-boson tensor mode
- Δt_q = λ²/(η·C_Q) quantization delay
- Spacetime curvature from delayed processing

### Codec 4: Weak Force (SU(2) Identity Rewrite)

**Parity violating**

```python
c4 = Codec4(identity=0.3, coherence=0.5)

alternatives = [{
    'type': 'muon',
    'required_info': 0.2,
    'mass': 105.7e6,  # eV
    'identity': 0.8,
    'lepton': True,
    'neutrino_flavor': 'muon'
}]

rewrite = c4.identity_rewrite(required_info=0.5, alternatives=alternatives)
# Returns: {'rewritten_as': 'muon', 'residue': {'type': 'neutrino', ...}, ...}
```

**Matrix M₄:**
- Id' = cos(θ_w)Id + sin(θ_w)Φ
- Φ' = -sin(θ_w)Id + cos(θ_w)Φ  
- S → (1 - Γ_w)S
- Rotation in (Id, Φ) plane

**Physics:**
- Flavor-changing processes
- Identity budget < threshold → rewrite
- Neutrino emission as byproduct
- θ_w ≈ 28.7° (Weinberg angle)

### Codec 5: Strong Confinement (SU(3))

**Short-range only**

```python
c5 = Codec5(coherence=0.7, entropy=0.95)

gluon = c5.confinement_gate(
    curvature=1e-14,
    lambda_confine=1e-15,
    S_threshold=0.9
)
# Returns: {'type': 'gluon', 'confined': True, 'confinement_radius_m': 1e-7, ...}
```

**Matrix M₅:**
- Φ → (1 + ρ₅)Φ — phase mixing
- X → (1 + τ₅)X — spatial mixing
- S → (1 - Λₓ)S — large entropy consumption
- C → (1 + χ)C — strong coherence boost

**Physics:**
- Activation: S > S_strong AND r < r_confine
- Energy trapped internally
- Gluon emission rare
- Color force confinement

### Codec 6: Pauli Exclusion

**Conditional: S > S_thr**

```python
c6 = Codec6(coherence=0.5, entropy=0.98)

# Check collision with another fermion
collision = c6.pauli_check(other_fermion)

# Apply rewrite if collision detected
if collision:
    result = c6.apply_pauli_rewrite()
    # Returns: {'identity_flipped': True, 'entropy_dumped': 0.98, ...}
```

**Matrix M₆:**
- Id → -Id — identity flip
- S → 0 — entropy consumed
- C → ρ₆C (ρ₆ ≈ 0.70)
- L → L + S — entropy dumped

**Physics:**
- Hash collision in (Φ, X, C) space
- Two fermions same state → one rewrites
- Enforces exclusion principle
- Triggered at S > 0.95

## State Vector Operations

All codecs inherit from `CodecBase`:

```python
# Get current state as 6D vector
state = codec.get_state_vector()
# Returns: [Id, Φ, X, S, C, L]

# Set state from vector
codec.set_state_vector(np.array([1.0, 0.0, 0.0, 0.5, 0.8, 0.0]))

# Update coherence (maintains S = 1 - C)
codec.update_coherence(delta=0.1)
```

## Matrix Algebra

Get explicit 6×6 matrices:

```python
# Scalar mass matrix
M1 = get_codec_matrix(1, {'lambda_s': 0.1, 'mu_1': 0.05})

# Photon emission matrix  
M2 = get_codec_matrix(2, {'c_2': 0.90, 'd_2': 1.05, 'f': 500})

# Weak interaction matrix
M4 = get_codec_matrix(4, {'theta_w': 0.5, 'Gamma_w': 0.3})

# Apply matrix transformation
R_new = M1 @ codec.get_state_vector()
codec.set_state_vector(R_new)
```

## Constants

Architectural constants (NOT tunable):

```python
H_EV = 4.135667662e-15      # Planck's constant (eV·s)
C_LIGHT = 3e8                # Speed of light (m/s)
T_PLANCK = 5.39e-44          # Planck time (s)
ETA_STEW = 1e-45             # Stew viscosity (kg·s⁻²)

C0_SCALAR = 2.14e8           # Scalar quantization
C2_TENSOR = 1e10             # Tensor quantization
CAPACITY_PER_TICK = 1e6      # Packets per tick

# Cost hierarchy
COST_SCALAR = 1
COST_VECTOR = 10
COST_TENSOR = 47
```

## Complete Example

```python
from codec_library_reference import *
import numpy as np

# Initialize electron state
electron = Codec2(coherence=0.95, entropy=0.05, identity=1.0)
electron.spatial = 0.0  # Position
electron.phase = 0.0    # Quantum phase

# Time evolution over 10 ticks
for tick in range(10):
    # Build entropy from environment
    electron.entropy += 0.1
    
    # Check for photon emission
    if electron.entropy > 0.98:
        photon = electron.vector_emission(freq_thz=500)
        if photon['status'] == 'emitted':
            print(f"Tick {tick}: Photon emitted at {photon['energy_ev']:.2f} eV")
    
    # Check Pauli collision (if multiple electrons)
    # if electron.pauli_check(other_electron):
    #     electron.apply_pauli_rewrite()

print(f"Final state: {electron.get_state_vector()}")
```

## Advanced: Composite Operations

Chain multiple codecs:

```python
# Weak decay: electron → muon + neutrino
electron = Codec4(identity=0.3, coherence=0.5)

muon_alternative = {
    'type': 'muon',
    'required_info': 0.2,
    'mass': 105.7e6,
    'identity': 0.8,
    'lepton': True,
    'neutrino_flavor': 'electron'
}

decay = electron.identity_rewrite(
    required_info=0.5,
    alternatives=[muon_alternative]
)

if decay['status'] != 'identity preserved':
    print(f"Decay: {decay['rewritten_as']}")
    print(f"Neutrino: {decay['residue']}")
```

## Framework Correspondence

| Python Class | Matrix | Assembly Codec | Physical Force |
|--------------|--------|----------------|----------------|
| `Codec1` | M₁(λₛ) | `CODEC1_SCALAR` | Higgs/Mass |
| `Codec2` | M₂(f) | `CODEC2_VECTOR` | Electromagnetic |
| `Codec3` | M₃(g,κ) | `CODEC3_TENSOR` | Gravity |
| `Codec4` | M₄(θ_w,Γ_w) | `CODEC6_REWRITE` | Weak (SU(2)) |
| `Codec5` | M₅(Λₛ,χ) | `CODEC5_CONFINE` | Strong (SU(3)) |
| `Codec6` | M₆(S) | `PAULI_CHECK` | Exclusion |

## Testing

Run built-in demonstration:

```bash
python codec_library_reference.py
```

Output shows all six codecs in action with realistic parameters.

## Theory References

- **Matrix Algebra**: See `codec_algebra.pdf`
- **Assembly Code**: See `universe_asm_opcodes.pdf`
- **Full Quantisation**: Complete monograph (forthcoming)

## License

MIT License - Part of the Computational Substrate framework

## Citation

```bibtex
@software{codec_library_python,
  author = {Jaroslav Petrina},
  title = {Codec Library: Python Implementation of Six-Register Substrate},
  year = {2024},
  note = {Part of Full Quantisation framework}
}
```

---

**Note**: This is a working implementation of a speculative physics framework. All parameters are architectural constraints derived from first principles (h, α, capacity) rather than fitted values. Deviations from predictions would falsify the framework and not require parameter adjustment.
