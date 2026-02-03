# Gravitational Theory Code Organization

This repository contains Python implementations of Jaroslav Petrina's gravitational theory framework, organized into two main categories reflecting the theoretical evolution:

## Directory Structure

### 📁 gravity-theory-development/
Early explorations and development of the computational substrate theory:

- **`gravitational_constant_analysis.py`** - Initial derivation of G from substrate efficiency using Mercury precession calibration
- **`extended_analysis.py`** - Emission-reactivity principle and architectural constants
- **`bandwidth_allocation.png`** - Visualization of computational resource distribution

Key concepts explored:
- Emission-reactivity mechanism (10^100 ops/sec emission, 10^-84 coupling)
- Codec hierarchy and computational costs
- Tensor coupling angles
- Physical impedance as computational expense

### 📁 gravity-monograph/
Refined formulation from Section 26 of the monograph:

- **`section_26_minimal.py`** - Core calculations without dependencies
- **`newton_constant_analysis.py`** - Full analysis with visualizations
- **`architectural_coupling_analysis.py`** - Complete Section 26 implementation

Key equation: **G = C_sub × ε_g**

Where:
- ε_g = 8.49×10^-84 (gravitational efficiency)
- C_sub = substrate coupling constant

### 📄 gravity_theory_bridge.py
Bridges both stages, showing the evolution from mechanistic description to fundamental architecture.

## Core Insights

1. **Gravity consumes 41% of computational budget but has only 10^-84 efficiency**
2. **Forces are unified by efficiency, not ontology**
3. **G is not fundamental but an architectural parameter**

## Running the Code

All scripts are standalone Python files requiring only standard libraries (math, numpy for calculations, matplotlib optional for visualizations).

### Minimal requirements:
```bash
python section_26_minimal.py  # No dependencies beyond standard library
```

### Full analysis:
```bash
python newton_constant_analysis.py  # matplotlib optional
```

## Key Results

- Mercury precession: 42.75 arcsec/century ✓
- Gravitational efficiency: 8.49×10^-84 ✓
- G/EM ratio: ~10^-39 ✓
- Computational efficiency: 10^45 ops/J ✓

## Physical Implications

This framework transforms gravity from a fundamental force to a computational bottleneck, explaining its weakness through substrate architecture rather than new physics.

---

*Based on Jaroslav Petrina's monograph "Emergence of finite computational substrate from Information Constraints" and earlier work "The Synthetic Engine"*
