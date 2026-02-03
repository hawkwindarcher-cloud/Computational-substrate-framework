# Complete Wavefunction class with integrated codec operations
# From "Full Quantisation" - Wavefunction as active computational agent
# All six codecs fused directly into the class for complete substrate dynamics
# Self-contained - no external dependencies except standard library

import math
import cmath

class Wavefunction:
    """
    Wavefunction as an active agent in the computational substrate.
    Maintains coherence budget through codec operations:
    - Codec1: Scalar mass (symmetry potential)
    - Codec2: Electromagnetic emission/absorption
    - Codec3: Gravitational tensor delay
    - Codec4: Decoherence field
    - Codec5: Strong confinement
    - Codec6: Weak identity rewrite
    """
    
    def __init__(self, coherence=1.0, entropy=0.0, identity=1.0, 
                 quantization_pressure=1.0, mass_ev=0.0):
        # Core state variables
        self.coherence = coherence
        self.entropy = entropy
        self.identity = identity
        self.quantization_pressure = quantization_pressure
        self.mass_ev = mass_ev  # Rest mass in eV
        
        # Physical constants
        self.h = 4.135667662e-15  # Planck's constant in eV·s
        self.c = 3e8  # Speed of light m/s
        self.t_P = 5.39e-44  # Planck time s
        self.eta = 1e-45  # Stew viscosity (substrate friction)
        
        # Codec-specific parameters
        self.C_Q_scalar = 1e6  # Codec1 quantization constant
        self.C_Q_tensor = 1e-2  # Codec3 quantization constant
        self.zeta_su5 = 1e-3  # Codec5 confinement constant
        
        # Evolution tracking
        self.time_step = 0.0
        self.history = []
        
    # ========== CODEC 1: SCALAR MASS FIELD ==========
    def codec1_scalar_mass(self, sigma, amplitude=1.0):
        """
        Scalar mass field - smooth, non-directional perturbation.
        Creates condensation-like regions in substrate.
        
        Args:
            sigma: Scalar field amplitude (dimensionless)
            amplitude: Overall field strength
            
        Returns:
            Energy contribution in eV
        """
        # Quantization delay for scalar mode
        tau_s = (sigma ** 2) / (self.eta * self.C_Q_scalar)
        
        if tau_s < self.t_P:
            return 0.0  # Below quantization threshold
            
        # Energy from coherence persistence
        E_q = self.h / tau_s
        
        # Scalar fields increase coherence (condensation effect)
        coherence_gain = 0.05 * (self.t_P / tau_s)
        self.coherence = min(1.0, self.coherence + coherence_gain)
        self.entropy = max(0.0, 1.0 - self.coherence)
        
        # Update mass contribution
        self.mass_ev += E_q * amplitude
        
        return E_q
    
    # ========== CODEC 2: ELECTROMAGNETIC VECTOR EMISSION ==========
    def codec2_emit_photon(self, energy_ev=None, freq_thz=None, crit_prob=0.98):
        """
        Emit photon if entropy exceeds critical threshold.
        Vector emission - directional radiation.
        
        Args:
            energy_ev: Photon energy in eV (or calculate from freq_thz)
            freq_thz: Frequency in THz
            crit_prob: Critical probability for emission (default 0.98)
            
        Returns:
            Dict with emission status and energy
        """
        # Determine photon energy
        if energy_ev is None and freq_thz is not None:
            energy_ev = self.h * freq_thz * 1e12
        elif energy_ev is None:
            energy_ev = self.entropy * 2.0  # Default based on entropy
            
        # Check emission threshold
        if self.entropy > crit_prob:
            # Emit photon - reduces coherence
            self.coherence *= 0.5 * self.quantization_pressure
            self.entropy *= 0.5
            
            emission = {
                "type": "photon",
                "codec": 2,
                "energy": round(energy_ev, 6),
                "frequency_thz": round(energy_ev / (self.h * 1e12), 3),
                "status": "emitted",
                "coherence_after": round(self.coherence, 4)
            }
            self.history.append(emission)
            return emission
        else:
            return {
                "type": "photon",
                "codec": 2,
                "energy": 0,
                "status": "blocked",
                "reason": f"entropy {self.entropy:.3f} < threshold {crit_prob}"
            }
    
    def codec2_absorb_photon(self, energy_ev, resonance_factor=1.0):
        """
        Absorb photon - increases coherence if energy matches.
        
        Args:
            energy_ev: Incoming photon energy in eV
            resonance_factor: Absorption efficiency (0-1)
            
        Returns:
            Absorption status string
        """
        absorption_threshold = 0.5  # Minimum energy for absorption
        
        if energy_ev > absorption_threshold:
            # Increase coherence proportional to energy
            coherence_gain = 0.15 * resonance_factor * (energy_ev / 2.0)
            self.coherence = min(1.0, self.coherence + coherence_gain)
            self.entropy = max(0.0, self.entropy - 0.1 * resonance_factor)
            self.identity = min(1.0, self.identity + 0.05)
            
            absorption = {
                "type": "absorption",
                "codec": 2,
                "energy": energy_ev,
                "coherence_gain": round(coherence_gain, 4)
            }
            self.history.append(absorption)
            return f"Photon absorbed: {energy_ev:.3f} eV"
        else:
            return f"No transition: energy {energy_ev:.3f} eV below threshold"
    
    # ========== CODEC 3: GRAVITATIONAL TENSOR DELAY ==========
    def codec3_tensor_delay(self, lambda_gw, omega=1.0, amplitude=1.0):
        """
        Gravitational wave - tensor perturbation with delayed quantization.
        2-boson mode creating spacetime curvature.
        
        Args:
            lambda_gw: Wavelength of gravitational perturbation (m)
            omega: Angular frequency
            amplitude: Wave amplitude (strain)
            
        Returns:
            Dict with gravitational packet info
        """
        # Quantization delay for tensor mode
        dt_q = (lambda_gw ** 2) / (self.eta * self.C_Q_tensor)
        
        if dt_q < self.t_P:
            return {"packet_type": "sub-quantum", "energy": 0}
            
        # Energy of gravitational quantum
        E_gw = self.h / dt_q
        
        # Tensor modes slightly decohere (spacetime distortion)
        decoherence = 0.01 * (dt_q / self.t_P)
        self.coherence = max(0.0, self.coherence - decoherence)
        self.entropy = min(1.0, 1.0 - self.coherence)
        
        packet = {
            "type": "graviton",
            "codec": 3,
            "packet_type": "2-boson tensor",
            "energy": E_gw,
            "delay": dt_q,
            "wavelength": lambda_gw,
            "amplitude": amplitude
        }
        self.history.append(packet)
        return packet
    
    # ========== CODEC 4: DECOHERENCE FIELD ==========
    def codec4_decoherence_field(self, epsilon_vals, omega_vals):
        """
        Decoherence field - phase fluctuations that destroy coherence.
        Can trigger inflation-like expansion in high-entropy regions.
        
        Args:
            epsilon_vals: List of field amplitudes
            omega_vals: List of phase angles
            
        Returns:
            Field status string
        """
        # Compute phase coherence
        phase_sum = sum(e * cmath.exp(1j * o) for e, o in zip(epsilon_vals, omega_vals))
        coherence_measure = abs(phase_sum) / len(epsilon_vals)
        
        # Low coherence triggers decoherence
        if coherence_measure < 0.5:
            self.identity *= 0.5
            self.coherence *= 0.3
            self.entropy = min(1.0, self.entropy + 0.5)
            
            event = {
                "type": "decoherence",
                "codec": 4,
                "phase_coherence": round(coherence_measure, 4),
                "identity_after": round(self.identity, 4),
                "status": "decohered"
            }
            self.history.append(event)
            return "decohered"
        else:
            return "stable field"
    
    # ========== CODEC 5: STRONG CONFINEMENT GATE ==========
    def codec5_confinement_gate(self, curvature, lambda_confine=1e-15):
        """
        Strong force confinement - high curvature traps energy.
        Prevents emission below confinement scale.
        
        Args:
            curvature: Local substrate curvature (1/m²)
            lambda_confine: Confinement wavelength (m)
            
        Returns:
            Confinement packet or None
        """
        if curvature > lambda_confine:
            # Confinement radius
            R_trap = math.sqrt(curvature)
            
            # Quantization delay in confined region
            dt_q = (R_trap ** 2) / (self.zeta_su5 * self.eta)
            
            if dt_q < self.t_P:
                return None
                
            # Confined energy
            E_confined = self.h / dt_q
            
            # Strong confinement maintains coherence locally
            self.coherence = min(1.0, self.coherence + 0.1)
            
            packet = {
                "type": "gluon",
                "codec": 5,
                "packet_type": "confined",
                "energy": E_confined,
                "confinement_radius": R_trap,
                "confined": True,
                "status": "trapped"
            }
            self.history.append(packet)
            return packet
        else:
            return None
    
    # ========== CODEC 6: WEAK IDENTITY REWRITE ==========
    def codec6_identity_rewrite(self, required_info, alternatives):
        """
        Weak force - identity rewrite when coherence budget insufficient.
        Allows wavefunction to change identity (flavor change).
        
        Args:
            required_info: Information needed to maintain current identity
            alternatives: List of alternative identity states
            
        Returns:
            Rewrite result dict
        """
        info_budget = self.identity
        
        # Check if current identity sustainable
        if info_budget < required_info:
            # Search for viable alternative
            for alt in alternatives:
                if info_budget >= alt['required_info']:
                    # Energy balance for identity change
                    mass_before = self.mass_ev
                    mass_after = alt.get('mass', 0.0)
                    delta_E = mass_after - mass_before
                    
                    # Rewrite identity
                    self.identity = alt['identity']
                    self.mass_ev = mass_after
                    
                    # Neutrino emission if lepton flavor change
                    residue = None
                    if 'lepton' in alt.get('type', ''):
                        residue = {
                            "type": "neutrino",
                            "energy": abs(delta_E),
                            "flavor": alt.get('neutrino_flavor', 'electron')
                        }
                    
                    rewrite = {
                        "codec": 6,
                        "rewritten_as": alt['type'],
                        "energy_balance": delta_E,
                        "residue": residue,
                        "identity_after": self.identity
                    }
                    self.history.append(rewrite)
                    return rewrite
            
            # No viable alternative - collapse
            return {"status": "collapse", "reason": "no viable identity"}
        else:
            return {"status": "identity preserved", "info_budget": info_budget}
    
    # ========== ENVIRONMENT INTERACTION ==========
    def environment_tick(self, external_field=0.01, dt=1e-15):
        """
        Simulate environmental interaction - builds entropy.
        
        Args:
            external_field: External field strength
            dt: Time step (seconds)
            
        Returns:
            Status string
        """
        self.time_step += dt
        
        # Entropy production from environment coupling
        entropy_rate = 0.05 * self.quantization_pressure * external_field
        self.coherence -= entropy_rate * dt / self.t_P
        self.entropy += entropy_rate * dt / self.t_P
        
        # Normalize
        self.coherence = max(0.0, min(1.0, self.coherence))
        self.entropy = max(0.0, min(1.0, self.entropy))
        
        # Check for decoherence threshold
        if self.coherence < 0.3:
            return self.full_decoherence()
        
        return "stable"
    
    def full_decoherence(self):
        """Complete wavefunction collapse with identity rewrite attempt."""
        self.identity *= 0.5
        
        # Attempt identity rewrite
        alternatives = [
            {
                'type': 'collapsed_eigenstate',
                'required_info': 0.3,
                'mass': self.mass_ev * 0.9,
                'identity': 0.5
            }
        ]
        
        rewrite = self.codec6_identity_rewrite(
            required_info=0.5,
            alternatives=alternatives
        )
        
        return f"Decoherence collapse. Identity: {self.identity:.3f}, Rewrite: {rewrite}"
    
    # ========== TIME EVOLUTION ==========
    def evolve(self, num_ticks=10, dt=1e-15, external_field=0.01, 
               photon_energy=2.0, enable_emission=True):
        """
        Complete time evolution with all codec operations.
        
        Args:
            num_ticks: Number of time steps
            dt: Time increment (seconds)
            external_field: Environmental coupling strength
            photon_energy: Energy for potential emissions (eV)
            enable_emission: Allow photon emission
            
        Returns:
            Evolution summary dict
        """
        events = []
        
        for tick in range(num_ticks):
            # Environmental decoherence
            status = self.environment_tick(external_field, dt)
            events.append({"tick": tick, "status": status})
            
            # Check for photon emission (high entropy)
            if enable_emission and self.entropy > 0.9:
                emission = self.codec2_emit_photon(energy_ev=photon_energy)
                if emission['status'] == 'emitted':
                    events.append({"tick": tick, "event": "emission", "data": emission})
            
            # Random photon absorption (simulate environment)
            if tick % 3 == 0 and self.coherence < 0.8:
                absorbed = self.codec2_absorb_photon(photon_energy * 0.7, resonance_factor=0.8)
                events.append({"tick": tick, "event": "absorption", "data": absorbed})
            
            # Check coherence state
            if self.coherence < 0.2:
                events.append({"tick": tick, "event": "critical_decoherence"})
                break
        
        return {
            "total_time": self.time_step,
            "final_coherence": round(self.coherence, 4),
            "final_entropy": round(self.entropy, 4),
            "final_identity": round(self.identity, 4),
            "num_events": len(events),
            "events": events
        }
    
    def get_state(self):
        """Return current wavefunction state."""
        return {
            "coherence": round(self.coherence, 4),
            "entropy": round(self.entropy, 4),
            "identity": round(self.identity, 4),
            "mass_ev": round(self.mass_ev, 6),
            "time": self.time_step,
            "quantization_pressure": self.quantization_pressure
        }


# ========== DEMONSTRATION ==========
if __name__ == "__main__":
    print("="*60)
    print("WAVEFUNCTION WITH INTEGRATED CODECS")
    print("Computational Substrate Model")
    print("="*60)
    
    # Create wavefunction
    wf = Wavefunction(coherence=0.95, entropy=0.05, identity=1.0, 
                      quantization_pressure=1.0, mass_ev=0.511e6)  # Electron mass
    
    print("\n1. INITIAL STATE:")
    print(wf.get_state())
    
    # Codec 1: Scalar mass contribution
    print("\n2. CODEC 1 - Scalar Mass Field:")
    E_scalar = wf.codec1_scalar_mass(sigma=0.5, amplitude=1.0)
    print(f"Scalar energy: {E_scalar:.6e} eV")
    print(wf.get_state())
    
    # Codec 2: Photon emission
    print("\n3. CODEC 2 - Photon Emission:")
    wf.entropy = 0.99  # Force high entropy
    emission = wf.codec2_emit_photon(energy_ev=2.5)
    print(emission)
    
    # Codec 2: Photon absorption
    print("\n4. CODEC 2 - Photon Absorption:")
    absorption = wf.codec2_absorb_photon(energy_ev=3.0, resonance_factor=0.9)
    print(absorption)
    
    # Codec 3: Gravitational wave
    print("\n5. CODEC 3 - Gravitational Tensor:")
    gw = wf.codec3_tensor_delay(lambda_gw=1e3, omega=1e-3, amplitude=1e-21)
    print(gw)
    
    # Codec 4: Decoherence field
    print("\n6. CODEC 4 - Decoherence Field:")
    epsilons = [0.1, 0.2, 0.15, 0.18]
    omegas = [0, math.pi/2, math.pi, 3*math.pi/2]
    field_status = wf.codec4_decoherence_field(epsilons, omegas)
    print(f"Field status: {field_status}")
    
    # Codec 5: Strong confinement
    print("\n7. CODEC 5 - Strong Confinement:")
    confinement = wf.codec5_confinement_gate(curvature=1e-14, lambda_confine=1e-15)
    print(confinement)
    
    # Codec 6: Weak identity rewrite
    print("\n8. CODEC 6 - Identity Rewrite:")
    wf.identity = 0.4  # Low identity budget
    alternatives = [
        {
            'type': 'muon',
            'required_info': 0.3,
            'mass': 105.7e6,  # Muon mass in eV
            'identity': 0.8,
            'lepton': True,
            'neutrino_flavor': 'muon'
        }
    ]
    rewrite = wf.codec6_identity_rewrite(required_info=0.5, alternatives=alternatives)
    print(rewrite)
    
    # Time evolution
    print("\n9. TIME EVOLUTION:")
    wf2 = Wavefunction(coherence=0.9, entropy=0.1)
    evolution = wf2.evolve(num_ticks=8, dt=1e-15, photon_energy=2.5)
    print(f"Evolution over {evolution['num_events']} events")
    print(f"Final state: coherence={evolution['final_coherence']}, "
          f"entropy={evolution['final_entropy']}")
    
    print("\n" + "="*60)
    print("All six codecs integrated and operational")
    print("="*60)