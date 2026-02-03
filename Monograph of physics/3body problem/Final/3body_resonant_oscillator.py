"""
Three-Body Dynamics as Resonant Oscillator Networks
Based on Section 22 of Jaroslav Petrina's Monograph

This implementation demonstrates:
1. Coupled oscillator interpretation of three-body dynamics
2. Quantization delays from finite register capacity
3. Natural emergence of Laplace resonances
4. Stability through computational checksum repairs
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from dataclasses import dataclass
from typing import Tuple, List, Optional

# Physical constants
G = 6.67430e-11           # m^3 kg^-1 s^-2
c = 299_792_458.0         # m/s
t_P = 5.39e-44           # Planck time (s)

# Computational substrate parameters (from monograph)
CAP2 = 1e12              # Coherence capacity
GAMMA = 1.0              # Post-Newtonian parameter

@dataclass
class Body:
    """Represents a gravitational body with oscillator properties"""
    name: str
    mass: float          # kg
    pos: np.ndarray      # m
    vel: np.ndarray      # m/s
    
    # Oscillator clocks (Section 22.3.1)
    theta_phi: float = 0.0    # Angular phase clock
    theta_r: float = 0.0      # Radial phase clock
    varpi: float = 0.0        # Integrated apsidal advance
    
    # Register states
    load: float = 0.0         # Computational load
    coherence: float = 1.0    # Quantum/classical parameter

class ResonantOscillatorNetwork:
    """
    Three-body system as coupled oscillators with finite register constraints.
    Implements the framework from Section 22 of the monograph.
    """
    
    def __init__(self, bodies: List[Body], dt: float = 300.0):
        self.bodies = bodies
        self.n_bodies = len(bodies)
        self.dt = dt
        
        # Capacity constraint parameters (Section 22.3.2)
        self.a_coeff = 1.0    # Linear term
        self.b_coeff = 0.1    # Quadratic term  
        self.c_coeff = 0.01   # Cubic term
        
        # Time window for capacity calculation
        self.T_win = 1000 * t_P  # Window size in Planck times
        self.K_max = CAP2 * self.T_win / t_P  # Maximum capacity
        
        # Tracking arrays
        self.history = {
            'time': [],
            'laplace_angle': [],
            'energy': [],
            'capacity_usage': [],
            'resonance_strength': []
        }
        
    def compute_kappa_app(self, body_idx: int) -> float:
        """
        Calculate apparent curvature index κ_app for a body.
        From Section 22.3.1: κ_app = -(1+γ)Φ/c²
        """
        Phi = self.compute_potential_at(body_idx)
        return -(1 + GAMMA) * Phi / (c**2)
    
    def compute_potential_at(self, body_idx: int) -> float:
        """Gravitational potential at body i from all others"""
        Phi = 0.0
        pos_i = self.bodies[body_idx].pos
        
        for j, body_j in enumerate(self.bodies):
            if j == body_idx:
                continue
            r_vec = body_j.pos - pos_i
            r = np.linalg.norm(r_vec) + 1e-12  # Avoid singularity
            Phi += -G * body_j.mass / r
            
        return Phi
    
    def compute_accelerations(self) -> np.ndarray:
        """N-body gravitational accelerations"""
        accels = np.zeros((self.n_bodies, 3))
        
        for i in range(self.n_bodies):
            for j in range(i+1, self.n_bodies):
                r_vec = self.bodies[j].pos - self.bodies[i].pos
                r2 = np.dot(r_vec, r_vec) + 1e-12
                r3_inv = r2**(-1.5)
                
                F_mag = G * self.bodies[i].mass * self.bodies[j].mass * r3_inv
                F_vec = F_mag * r_vec
                
                accels[i] += F_vec / self.bodies[i].mass
                accels[j] -= F_vec / self.bodies[j].mass
                
        return accels
    
    def update_oscillator_clocks(self, body: Body, kappa: float, Omega_N: float):
        """
        Update the two-clock system per body (Section 22.3.1).
        
        Δθ_φ = Ω_N(1 + Δf/f)Δt  [angular clock]
        Δθ_r = Ω_N(1 - Δλ/λ)Δt  [radial clock]
        Δϖ = κ_app × Ω_N × Δt    [apsidal advance]
        """
        # For simplicity, approximate Δf/f ≈ κ/2 and Δλ/λ ≈ -κ/2
        delta_theta_phi = Omega_N * (1 + kappa/2) * self.dt
        delta_theta_r = Omega_N * (1 - kappa/2) * self.dt
        
        body.theta_phi += delta_theta_phi
        body.theta_r += delta_theta_r
        
        # Apsidal advance
        delta_varpi = kappa * Omega_N * self.dt
        body.varpi += delta_varpi
    
    def compute_capacity_usage(self) -> float:
        """
        Compute W(N) capacity usage (Section 22.3.2).
        W(N) = aN + bN² + cN³
        """
        N = self.n_bodies
        W = self.a_coeff * N + self.b_coeff * N**2 + self.c_coeff * N**3
        return W / self.K_max  # Normalized usage
    
    def apply_checksum_repair(self):
        """
        Implement computational checksum repairs that stabilize the system.
        This prevents runaway divergence by enforcing capacity constraints.
        """
        usage = self.compute_capacity_usage()
        
        if usage > 0.95:  # Near capacity limit
            # Apply diffusive correction to velocities
            damping = 1.0 - 0.01 * (usage - 0.95)
            for body in self.bodies:
                body.vel *= damping
                
            # Reset computational load
            for body in self.bodies:
                body.load *= 0.9
    
    def compute_laplace_angle(self) -> float:
        """
        Calculate Laplace resonant angle (Section 22.3.3).
        For Jupiter's moons: Φ_L = λ_1 - 3λ_2 + 2λ_3
        
        Assumes bodies[0] is central (Jupiter), [1,2,3] are moons
        """
        if self.n_bodies < 4:
            return 0.0
            
        # Mean longitudes relative to central body
        lambdas = []
        for i in range(1, min(4, self.n_bodies)):
            r_rel = self.bodies[i].pos - self.bodies[0].pos
            lam = np.arctan2(r_rel[1], r_rel[0])
            lambdas.append(lam)
        
        if len(lambdas) >= 3:
            # Laplace angle for 1:2:4 resonance
            phi_L = lambdas[0] - 3*lambdas[1] + 2*lambdas[2]
            # Wrap to [-π, π]
            phi_L = (phi_L + np.pi) % (2*np.pi) - np.pi
            return phi_L
        
        return 0.0
    
    def compute_resonance_strength(self) -> float:
        """
        Measure the strength of resonant phase-locking.
        Strong resonance = small amplitude oscillations in Laplace angle.
        """
        if len(self.history['laplace_angle']) < 100:
            return 0.0
            
        # Standard deviation of recent Laplace angles
        recent_angles = np.array(self.history['laplace_angle'][-100:])
        std_dev = np.std(recent_angles)
        
        # Convert to strength (0 = no resonance, 1 = perfect lock)
        max_deviation = np.pi  # Maximum possible deviation
        strength = 1.0 - min(std_dev / max_deviation, 1.0)
        
        return strength
    
    def leapfrog_step(self):
        """
        Symplectic leapfrog integrator with oscillator clock updates.
        Implements the clickwise N-body update from Section 22.3.
        """
        # Current accelerations
        accels = self.compute_accelerations()
        
        # Kick-drift-kick leapfrog
        # KICK (half)
        for i, body in enumerate(self.bodies):
            body.vel += 0.5 * self.dt * accels[i]
        
        # DRIFT
        for body in self.bodies:
            body.pos += self.dt * body.vel
        
        # New accelerations at updated positions
        accels = self.compute_accelerations()
        
        # KICK (half)
        for i, body in enumerate(self.bodies):
            body.vel += 0.5 * self.dt * accels[i]
        
        # Update oscillator clocks for each moon
        for i in range(1, self.n_bodies):  # Skip central body
            kappa = self.compute_kappa_app(i)
            
            # Instantaneous Keplerian frequency
            r_vec = self.bodies[i].pos - self.bodies[0].pos
            r = np.linalg.norm(r_vec)
            mu = G * self.bodies[0].mass
            Omega_N = np.sqrt(mu / r**3) if r > 0 else 0
            
            self.update_oscillator_clocks(self.bodies[i], kappa, Omega_N)
            
            # Update computational load
            self.bodies[i].load = abs(kappa) * Omega_N * r
        
        # Apply checksum repairs if needed
        self.apply_checksum_repair()
    
    def compute_total_energy(self) -> float:
        """Calculate total energy (kinetic + potential) for conservation check"""
        E_kin = 0.0
        E_pot = 0.0
        
        # Kinetic energy
        for body in self.bodies:
            E_kin += 0.5 * body.mass * np.dot(body.vel, body.vel)
        
        # Potential energy
        for i in range(self.n_bodies):
            for j in range(i+1, self.n_bodies):
                r = np.linalg.norm(self.bodies[j].pos - self.bodies[i].pos)
                if r > 0:
                    E_pot -= G * self.bodies[i].mass * self.bodies[j].mass / r
        
        return E_kin + E_pot
    
    def simulate(self, duration: float, record_interval: int = 10):
        """
        Run the three-body simulation.
        
        Args:
            duration: Total simulation time in seconds
            record_interval: Record data every N steps
        """
        n_steps = int(duration / self.dt)
        
        print(f"Starting resonant oscillator simulation")
        print(f"Duration: {duration/86400:.1f} days")
        print(f"Steps: {n_steps}, dt: {self.dt}s")
        print(f"Capacity limit: {self.K_max:.2e}")
        print("-" * 50)
        
        for step in range(n_steps):
            # Integrate dynamics
            self.leapfrog_step()
            
            # Record diagnostics
            if step % record_interval == 0:
                self.history['time'].append(step * self.dt)
                self.history['laplace_angle'].append(self.compute_laplace_angle())
                self.history['energy'].append(self.compute_total_energy())
                self.history['capacity_usage'].append(self.compute_capacity_usage())
                self.history['resonance_strength'].append(self.compute_resonance_strength())
                
                if step % (100 * record_interval) == 0:
                    t_days = step * self.dt / 86400
                    res_strength = self.history['resonance_strength'][-1]
                    cap_usage = self.history['capacity_usage'][-1]
                    print(f"Day {t_days:6.1f}: Resonance={res_strength:.3f}, "
                          f"Capacity={cap_usage:.3f}")
        
        print("-" * 50)
        print("Simulation complete")
        
        # Final analysis
        self.analyze_results()
    
    def analyze_results(self):
        """Analyze simulation results for resonance and stability"""
        times = np.array(self.history['time'])
        laplace = np.array(self.history['laplace_angle'])
        energy = np.array(self.history['energy'])
        
        # Check energy conservation
        E0 = energy[0]
        E_drift = (energy[-1] - E0) / abs(E0)
        print(f"\nEnergy drift: {E_drift*100:.3f}%")
        
        # Check Laplace angle stability
        if len(laplace) > 100:
            recent_std = np.std(laplace[-100:])
            print(f"Laplace angle std (last 100): {np.degrees(recent_std):.2f}°")
            
            # Detect libration vs circulation
            if recent_std < 0.5:  # radians
                print("Status: RESONANT (librating)")
            else:
                print("Status: NON-RESONANT (circulating)")
        
        # Check for emerging resonance
        res_history = self.history['resonance_strength']
        if len(res_history) > 10:
            early_res = np.mean(res_history[:10])
            late_res = np.mean(res_history[-10:])
            improvement = late_res - early_res
            print(f"Resonance improvement: {improvement:.3f}")
            
            if improvement > 0.1:
                print("→ System evolving toward resonance!")
    
    def plot_results(self, save_path: Optional[str] = None):
        """Generate diagnostic plots"""
        times_days = np.array(self.history['time']) / 86400
        
        fig, axes = plt.subplots(2, 3, figsize=(15, 8))
        
        # 1. Orbits
        ax = axes[0, 0]
        for i, body in enumerate(self.bodies[1:], 1):  # Skip central body
            trajectory = []
            # Reconstruct trajectory (simplified - would need full history)
            ax.plot([], [], 'o-', label=body.name, markersize=3)
        ax.set_xlabel('x (m)')
        ax.set_ylabel('y (m)')
        ax.set_title('Orbital Trajectories')
        ax.legend()
        ax.axis('equal')
        
        # 2. Laplace angle
        ax = axes[0, 1]
        laplace_deg = np.degrees(self.history['laplace_angle'])
        ax.plot(times_days, laplace_deg, 'b-', linewidth=0.8)
        ax.set_xlabel('Time (days)')
        ax.set_ylabel('Laplace angle (deg)')
        ax.set_title('Φ_L = λ₁ - 3λ₂ + 2λ₃')
        ax.grid(True, alpha=0.3)
        
        # 3. Energy conservation
        ax = axes[0, 2]
        energy = np.array(self.history['energy'])
        E0 = energy[0] if len(energy) > 0 else 1
        rel_energy = (energy - E0) / abs(E0) * 100
        ax.plot(times_days, rel_energy, 'r-', linewidth=0.8)
        ax.set_xlabel('Time (days)')
        ax.set_ylabel('Energy drift (%)')
        ax.set_title('Energy Conservation')
        ax.grid(True, alpha=0.3)
        
        # 4. Apsidal precession
        ax = axes[1, 0]
        for i, body in enumerate(self.bodies[1:], 1):
            precession_arcsec = np.degrees(body.varpi) * 3600
            ax.plot(times_days[-1], precession_arcsec, 'o', label=body.name)
        ax.set_xlabel('Time (days)')
        ax.set_ylabel('Precession (arcsec)')
        ax.set_title('Cumulative Apsidal Advance')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 5. Capacity usage
        ax = axes[1, 1]
        capacity = np.array(self.history['capacity_usage']) * 100
        ax.plot(times_days, capacity, 'g-', linewidth=0.8)
        ax.axhline(y=95, color='r', linestyle='--', alpha=0.5, label='Repair threshold')
        ax.set_xlabel('Time (days)')
        ax.set_ylabel('Capacity usage (%)')
        ax.set_title('Computational Load')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 6. Resonance strength
        ax = axes[1, 2]
        resonance = self.history['resonance_strength']
        ax.plot(times_days, resonance, 'purple', linewidth=1.0)
        ax.set_xlabel('Time (days)')
        ax.set_ylabel('Resonance strength')
        ax.set_title('Phase-lock Evolution')
        ax.set_ylim([0, 1])
        ax.grid(True, alpha=0.3)
        
        plt.suptitle('Three-Body Resonant Oscillator Network', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150)
            print(f"Plots saved to {save_path}")
        
        plt.show()

def setup_galilean_system() -> ResonantOscillatorNetwork:
    """Initialize the Jupiter-Io-Europa-Ganymede system"""
    
    # Masses (kg)
    M_jup = 1.89813e27
    m_io = 8.931938e22
    m_eu = 4.799844e22
    m_ga = 1.4819e23
    
    # Semi-major axes (m)
    a_io = 421_800e3
    a_eu = 671_100e3
    a_ga = 1_070_400e3
    
    # Circular velocities
    mu_J = G * M_jup
    v_io = np.sqrt(mu_J / a_io)
    v_eu = np.sqrt(mu_J / a_eu)
    v_ga = np.sqrt(mu_J / a_ga)
    
    # Create bodies
    jupiter = Body("Jupiter", M_jup, np.array([0.0, 0.0, 0.0]), np.array([0.0, 0.0, 0.0]))
    
    # Position moons to start near Laplace configuration
    io = Body("Io", m_io, 
              np.array([-a_io, 0.0, 0.0]),
              np.array([0.0, -v_io, 0.0]))
    
    europa = Body("Europa", m_eu,
                  np.array([a_eu, 0.0, 0.0]),
                  np.array([0.0, v_eu, 0.0]))
    
    ganymede = Body("Ganymede", m_ga,
                    np.array([a_ga, 0.0, 0.0]),
                    np.array([0.0, v_ga, 0.0]))
    
    # Set Jupiter velocity for zero total momentum
    p_total = m_io * io.vel + m_eu * europa.vel + m_ga * ganymede.vel
    jupiter.vel = -p_total / M_jup
    
    bodies = [jupiter, io, europa, ganymede]
    
    return ResonantOscillatorNetwork(bodies, dt=300.0)

def main():
    """Run the Galilean moons simulation"""
    
    print("=" * 60)
    print("THREE-BODY DYNAMICS AS RESONANT OSCILLATOR NETWORKS")
    print("Based on Section 22 of Jaroslav Petrina's Monograph")
    print("=" * 60)
    
    # Setup system
    system = setup_galilean_system()
    
    # Run simulation
    duration_days = 40.0
    duration_sec = duration_days * 86400
    
    system.simulate(duration_sec, record_interval=10)
    
    # Generate plots
    system.plot_results(save_path="resonant_oscillator_3body.png")
    
    # Export data
    df = pd.DataFrame({
        't_days': np.array(system.history['time']) / 86400,
        'laplace_angle_deg': np.degrees(system.history['laplace_angle']),
        'energy': system.history['energy'],
        'capacity_usage': system.history['capacity_usage'],
        'resonance_strength': system.history['resonance_strength']
    })
    
    output_path = Path("resonant_oscillator_data.csv")
    df.to_csv(output_path, index=False)
    print(f"\nData saved to {output_path.resolve()}")
    
    # Summary statistics
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    final_resonance = system.history['resonance_strength'][-1]
    print(f"Final resonance strength: {final_resonance:.3f}")
    
    if final_resonance > 0.7:
        print("→ Strong 1:2:4 resonance achieved!")
    elif final_resonance > 0.4:
        print("→ Partial resonance developing")
    else:
        print("→ System not yet resonant")
    
    # Theoretical prediction check
    print("\nMonograph prediction: Resonance emerges in ~10^4 orbits")
    io_period = 2 * np.pi * 421_800e3 / np.sqrt(G * 1.89813e27 / 421_800e3)
    orbits_simulated = duration_sec / io_period
    print(f"Orbits simulated: {orbits_simulated:.0f}")
    
    if orbits_simulated < 1e4:
        print("→ Need longer simulation to verify prediction")
    else:
        print("→ Sufficient duration for resonance capture")

if __name__ == "__main__":
    main()
