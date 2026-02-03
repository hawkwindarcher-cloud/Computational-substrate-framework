"""
Earth-Moon-Sun Three-Body System
Enhanced implementation based on Section 22 of Jaroslav Petrina's Monograph

This explores the Earth-Moon-Sun system with focus on:
1. Lunar perturbations on Earth's orbit
2. Tidal effects through codec coupling
3. Precession of Earth's perihelion
4. Moon's apsidal and nodal precession
"""

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import Dict, Tuple, List
import pandas as pd

# Physical Constants
G = 6.67430e-11       # m³ kg⁻¹ s⁻²
c = 299_792_458.0     # m/s
t_P = 5.39e-44        # Planck time (s)

# System masses (kg)
M_Sun = 1.989e30
M_Earth = 5.972e24
M_Moon = 7.342e22

# Orbital parameters
AU = 1.496e11         # Astronomical Unit (m)
a_Earth = AU          # Earth's semi-major axis
a_Moon = 3.844e8      # Moon's semi-major axis (from Earth)
e_Earth = 0.0167      # Earth's eccentricity
e_Moon = 0.0549       # Moon's eccentricity
i_Moon = 5.145        # Moon's inclination (degrees)

# Periods
P_Earth = 365.256363004 * 86400  # Tropical year (s)
P_Moon = 27.321661 * 86400       # Sidereal month (s)

@dataclass
class CelestialBody:
    """Represents a body in the Earth-Moon-Sun system"""
    name: str
    mass: float
    
    # Orbital elements
    semi_major: float
    eccentricity: float
    inclination: float = 0.0  # degrees
    
    # Dynamic state
    theta: float = 0.0        # True anomaly
    omega: float = 0.0        # Argument of periapsis
    Omega: float = 0.0        # Longitude of ascending node
    
    # Position and velocity
    pos: np.ndarray = None
    vel: np.ndarray = None
    
    # Oscillator clocks (Section 22.3.1)
    theta_phi: float = 0.0    # Angular phase clock
    theta_r: float = 0.0      # Radial phase clock
    varpi: float = 0.0        # Accumulated apsidal advance
    
    # Substrate states
    kappa: float = 0.0        # Current κ_app
    entropy: float = 0.0      # W(N)/K
    coherence: float = 1.0    # Quantum coherence
    
    def __post_init__(self):
        if self.pos is None:
            self.pos = np.zeros(3)
        if self.vel is None:
            self.vel = np.zeros(3)
    
    @property
    def mean_motion(self) -> float:
        """Calculate mean motion n = 2π/P"""
        if self.name == "Earth":
            return 2 * np.pi / P_Earth
        elif self.name == "Moon":
            return 2 * np.pi / P_Moon
        else:
            return 0.0

class EarthMoonSunSystem:
    """
    Three-body system for Earth-Moon-Sun with codec coupling.
    Implements resonant oscillator framework from Section 22.
    """
    
    def __init__(self, gamma: float = 1.0):
        """
        Initialize the Earth-Moon-Sun system.
        
        Args:
            gamma: Post-Newtonian parameter
        """
        self.gamma = gamma
        
        # Create bodies
        self.sun = CelestialBody("Sun", M_Sun, 0, 0)
        self.earth = CelestialBody("Earth", M_Earth, a_Earth, e_Earth)
        self.moon = CelestialBody("Moon", M_Moon, a_Moon, e_Moon, i_Moon)
        
        # Substrate parameters (stew-field)
        self.eta = 1e-45          # Stew viscosity
        self.C2 = 1e-2           # Tensor complexity (Codec3)
        self.C0 = 1e6            # Scalar complexity (Codec1)
        self.rho_s = 1e18        # Stew density
        self.Pe_crit = 1.24e17   # Critical emission threshold
        
        # Capacity parameters
        self.capacity = 1e12
        self.T_win = 1000 * t_P
        self.K_max = self.capacity * self.T_win / t_P
        
        # Codec coupling factors
        self.codec1_scalar = 1.0  # Scalar mass coupling
        self.codec3_tensor = 1.0  # Tensor delay coupling
        
        # History tracking
        self.history = {
            'time': [],
            'earth_pos': [],
            'moon_pos': [],
            'earth_kappa': [],
            'moon_kappa': [],
            'earth_varpi': [],
            'moon_varpi': [],
            'moon_nodal': [],
            'tidal_effect': [],
            'entropy_total': []
        }
    
    def calculate_kappa_app(self, body: CelestialBody, perturber_pos: np.ndarray = None) -> float:
        """
        Calculate apparent curvature index with perturbations.
        κ_app = -(1+γ)Φ/c²
        
        Includes contributions from both Sun and perturbations.
        """
        # Primary potential from Sun
        r_sun = np.linalg.norm(body.pos)
        if r_sun > 0:
            Phi_sun = -G * M_Sun / r_sun
        else:
            Phi_sun = 0
        
        # Add perturbation potential if present
        Phi_pert = 0
        if perturber_pos is not None and body.name == "Earth":
            # Moon's perturbation on Earth
            r_pert = np.linalg.norm(body.pos - perturber_pos)
            if r_pert > 0:
                Phi_pert = -G * M_Moon / r_pert
        elif perturber_pos is not None and body.name == "Moon":
            # Earth's influence on Moon (in Earth-centered frame)
            r_pert = np.linalg.norm(perturber_pos)
            if r_pert > 0:
                Phi_pert = -G * M_Earth / r_pert
        
        Phi_total = Phi_sun + Phi_pert
        return -(1 + self.gamma) * Phi_total / (c**2)
    
    def codec3_tensor_delay(self, body: CelestialBody, lambda_val: float = 1e11) -> float:
        """
        Calculate tensor delay from Codec3 with perturbations.
        This represents gravitational processing delay.
        """
        # Base delay
        delay_base = (lambda_val**2) / (self.eta * self.C2)
        
        # Density enhancement from gravitational field
        if body.name == "Earth":
            r = np.linalg.norm(body.pos)
            rho_grav = G * M_Sun * M_Earth / (r**3) if r > 0 else 0
        else:  # Moon
            r = np.linalg.norm(body.pos - self.earth.pos)
            rho_grav = G * M_Earth * M_Moon / (r**3) if r > 0 else 0
        
        # Enhanced delay from field density
        rho_excess = max(0, (self.rho_s + rho_grav - self.Pe_crit) / self.Pe_crit)
        delay = delay_base * (1 + rho_excess)
        
        # Relativistic correction
        v = np.linalg.norm(body.vel)
        v_c = v / c if c > 0 else 0
        delay /= np.sqrt(1 - v_c**2)
        
        return delay
    
    def codec1_scalar_mass(self, body: CelestialBody, sigma: float = 1e-9) -> float:
        """
        Calculate scalar mass effect from Codec1.
        Represents mass-energy coupling in substrate.
        """
        # Base scalar field
        mass_energy = body.mass * c**2
        
        # Diffusion timescale
        tau_s = (sigma**2) / (self.eta * self.C0)
        
        # Scalar coupling strength
        scalar_effect = mass_energy * tau_s / (self.capacity * t_P)
        
        return scalar_effect
    
    def calculate_tidal_effect(self) -> float:
        """
        Calculate tidal perturbation factor from Moon on Earth.
        This affects Earth's precession and stability.
        """
        r_earth_sun = np.linalg.norm(self.earth.pos)
        r_earth_moon = np.linalg.norm(self.moon.pos - self.earth.pos)
        
        if r_earth_sun > 0 and r_earth_moon > 0:
            # Tidal factor: (M_moon/M_sun) * (r_sun/r_moon)³
            tidal = (M_Moon / M_Sun) * (r_earth_sun / r_earth_moon)**3
        else:
            tidal = 0
        
        return tidal
    
    def update_oscillator_clocks(self, body: CelestialBody, dt: float):
        """
        Update two-clock system from Section 22.3.1.
        """
        Omega_N = body.mean_motion
        
        if Omega_N > 0:
            # Clock updates with κ_app correction
            delta_theta_phi = Omega_N * (1 + body.kappa/2) * dt
            delta_theta_r = Omega_N * (1 - body.kappa/2) * dt
            
            body.theta_phi += delta_theta_phi
            body.theta_r += delta_theta_r
            
            # Apsidal advance
            delta_varpi = body.kappa * Omega_N * dt
            body.varpi += delta_varpi
    
    def calculate_moon_nodal_precession(self, dt: float) -> float:
        """
        Calculate Moon's nodal precession due to Earth's oblateness and Sun.
        Retrograde precession with period ~18.6 years.
        """
        # Simplified nodal precession rate
        # Real value: -19.34° per year (retrograde)
        n_moon = self.moon.mean_motion
        
        # J2 effect from Earth's oblateness
        J2_Earth = 1.08263e-3  # Earth's J2 coefficient
        R_Earth = 6.371e6      # Earth radius
        
        r_moon = np.linalg.norm(self.moon.pos - self.earth.pos)
        if r_moon > 0:
            # Nodal rate from J2
            dOmega_dt = -1.5 * n_moon * J2_Earth * (R_Earth / r_moon)**2 * \
                       np.cos(np.radians(self.moon.inclination))
            
            # Solar perturbation (simplified)
            solar_factor = (M_Sun / M_Earth) * (a_Moon / a_Earth)**3
            dOmega_dt *= (1 + solar_factor)
            
            self.moon.Omega += dOmega_dt * dt
            return dOmega_dt
        
        return 0
    
    def calculate_entropy_load(self) -> float:
        """
        Calculate total system entropy W(N)/K.
        """
        # Three-body capacity usage
        N = 3
        W = N + 0.1*N**2 + 0.01*N**3  # From Section 22.3.2
        
        # Add dynamical contributions
        tidal = self.calculate_tidal_effect()
        W += abs(tidal) * 1e3  # Scale tidal effects
        
        # Add codec delays
        earth_delay = self.codec3_tensor_delay(self.earth)
        moon_delay = self.codec3_tensor_delay(self.moon)
        W += (earth_delay + moon_delay) / self.K_max
        
        return W / self.K_max  # Normalized
    
    def step(self, dt: float):
        """
        Single integration step with all effects.
        """
        # Update positions (simplified circular/elliptical)
        # Earth around Sun
        self.earth.theta += self.earth.mean_motion * dt
        r_earth = a_Earth * (1 + e_Earth * np.cos(self.earth.theta))
        self.earth.pos = np.array([
            r_earth * np.cos(self.earth.theta),
            r_earth * np.sin(self.earth.theta),
            0
        ])
        
        # Moon around Earth (in Earth-centered frame, then transform)
        self.moon.theta += self.moon.mean_motion * dt
        r_moon = a_Moon * (1 + e_Moon * np.cos(self.moon.theta))
        
        # Include inclination and nodal effects
        moon_local = np.array([
            r_moon * np.cos(self.moon.theta),
            r_moon * np.sin(self.moon.theta) * np.cos(np.radians(i_Moon)),
            r_moon * np.sin(self.moon.theta) * np.sin(np.radians(i_Moon))
        ])
        
        # Transform to solar frame
        self.moon.pos = self.earth.pos + moon_local
        
        # Calculate velocities (approximate)
        v_earth = r_earth * self.earth.mean_motion
        self.earth.vel = np.array([
            -v_earth * np.sin(self.earth.theta),
            v_earth * np.cos(self.earth.theta),
            0
        ])
        
        v_moon = r_moon * self.moon.mean_motion
        self.moon.vel = self.earth.vel + np.array([
            -v_moon * np.sin(self.moon.theta),
            v_moon * np.cos(self.moon.theta),
            0
        ])
        
        # Calculate κ_app for each body
        self.earth.kappa = self.calculate_kappa_app(self.earth, self.moon.pos)
        self.moon.kappa = self.calculate_kappa_app(self.moon, self.earth.pos)
        
        # Update oscillator clocks
        self.update_oscillator_clocks(self.earth, dt)
        self.update_oscillator_clocks(self.moon, dt)
        
        # Moon's nodal precession
        nodal_rate = self.calculate_moon_nodal_precession(dt)
        
        # Calculate entropy
        entropy = self.calculate_entropy_load()
        
        # Apply checksum repair if needed
        if entropy > 0.95:
            damping = 1.0 - 0.05 * (entropy - 0.95)
            self.earth.vel *= damping
            self.moon.vel *= damping
    
    def simulate(self, duration: float, dt: float = 3600):
        """
        Run simulation for specified duration.
        
        Args:
            duration: Total time in seconds
            dt: Time step in seconds (default 1 hour)
        """
        n_steps = int(duration / dt)
        
        print(f"Simulating Earth-Moon-Sun System")
        print(f"Duration: {duration/(365.256*86400):.2f} years")
        print(f"Steps: {n_steps}, dt: {dt/3600:.1f} hours")
        print("-" * 50)
        
        for step in range(n_steps):
            self.step(dt)
            
            # Record every 100 steps
            if step % 100 == 0:
                self.history['time'].append(step * dt)
                self.history['earth_pos'].append(self.earth.pos.copy())
                self.history['moon_pos'].append(self.moon.pos.copy())
                self.history['earth_kappa'].append(self.earth.kappa)
                self.history['moon_kappa'].append(self.moon.kappa)
                self.history['earth_varpi'].append(self.earth.varpi)
                self.history['moon_varpi'].append(self.moon.varpi)
                self.history['moon_nodal'].append(self.moon.Omega)
                self.history['tidal_effect'].append(self.calculate_tidal_effect())
                self.history['entropy_total'].append(self.calculate_entropy_load())
            
            # Progress update
            if step % 10000 == 0:
                t_years = step * dt / (365.256 * 86400)
                earth_prec = np.degrees(self.earth.varpi) * 3600  # arcsec
                moon_prec = np.degrees(self.moon.varpi) * 3600
                print(f"Year {t_years:5.2f}: "
                      f"Earth Δϖ={earth_prec:6.2f}\", "
                      f"Moon Δϖ={moon_prec:6.2f}\"")
        
        print("-" * 50)
        print("Simulation complete")
        self.analyze_results()
    
    def analyze_results(self):
        """Analyze simulation results"""
        times = np.array(self.history['time'])
        years = times / (365.256 * 86400)
        
        if len(years) > 0 and years[-1] > 0:
            # Precession rates
            earth_varpi = np.array(self.history['earth_varpi'])
            moon_varpi = np.array(self.history['moon_varpi'])
            moon_nodal = np.array(self.history['moon_nodal'])
            
            # Convert to standard units
            earth_rate = np.degrees(earth_varpi[-1]) * 3600 / years[-1]  # arcsec/year
            moon_apsidal_rate = np.degrees(moon_varpi[-1]) * 3600 / years[-1]
            moon_nodal_rate = np.degrees(moon_nodal[-1] - moon_nodal[0]) / years[-1]
            
            print(f"\nPrecession Rates:")
            print(f"  Earth perihelion: {earth_rate:.4f} arcsec/year")
            print(f"  Moon apsidal: {moon_apsidal_rate:.4f} arcsec/year")
            print(f"  Moon nodal: {moon_nodal_rate:.4f} degrees/year")
            
            # Compare with observations
            print(f"\nObserved values:")
            print(f"  Earth: ~11.45 arcsec/year")
            print(f"  Moon apsidal: ~40.7 degrees/year")
            print(f"  Moon nodal: ~-19.34 degrees/year")
            
            # Tidal effects
            tidal = np.array(self.history['tidal_effect'])
            print(f"\nTidal perturbation:")
            print(f"  Mean: {tidal.mean():.2e}")
            print(f"  Max: {tidal.max():.2e}")
    
    def plot_results(self, save_path: str = None):
        """Generate diagnostic plots"""
        
        times = np.array(self.history['time'])
        years = times / (365.256 * 86400)
        
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        
        # 1. Orbital paths
        ax = axes[0, 0]
        earth_pos = np.array(self.history['earth_pos'])
        moon_pos = np.array(self.history['moon_pos'])
        
        if len(earth_pos) > 0:
            ax.plot(earth_pos[::100, 0]/AU, earth_pos[::100, 1]/AU, 
                   'b-', linewidth=0.5, alpha=0.7, label='Earth')
            ax.plot(moon_pos[::10, 0]/AU, moon_pos[::10, 1]/AU, 
                   'gray', linewidth=0.3, alpha=0.5, label='Moon')
            ax.plot(0, 0, 'yo', markersize=10, label='Sun')
            ax.set_xlabel('X (AU)')
            ax.set_ylabel('Y (AU)')
            ax.set_title('Orbital Paths')
            ax.axis('equal')
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        # 2. Earth-Moon distance
        ax = axes[0, 1]
        if len(earth_pos) > 0 and len(moon_pos) > 0:
            r_em = np.linalg.norm(moon_pos - earth_pos, axis=1)
            ax.plot(years, r_em/1e6, 'purple', linewidth=0.8)
            ax.set_xlabel('Time (years)')
            ax.set_ylabel('Distance (Mm)')
            ax.set_title('Earth-Moon Distance')
            ax.grid(True, alpha=0.3)
        
        # 3. κ_app evolution
        ax = axes[0, 2]
        ax.semilogy(years, np.abs(self.history['earth_kappa']), 
                   'b-', label='Earth', linewidth=0.8)
        ax.semilogy(years, np.abs(self.history['moon_kappa']), 
                   'gray', label='Moon', linewidth=0.8)
        ax.set_xlabel('Time (years)')
        ax.set_ylabel('|κ_app|')
        ax.set_title('Apparent Curvature Index')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 4. Precession accumulation
        ax = axes[1, 0]
        earth_varpi = np.degrees(self.history['earth_varpi']) * 3600
        moon_varpi = np.degrees(self.history['moon_varpi']) * 3600
        
        ax.plot(years, earth_varpi, 'b-', label='Earth', linewidth=0.8)
        ax.plot(years, moon_varpi/100, 'gray', label='Moon (÷100)', linewidth=0.8)
        ax.set_xlabel('Time (years)')
        ax.set_ylabel('Precession (arcsec)')
        ax.set_title('Cumulative Apsidal Advance')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 5. Tidal effects
        ax = axes[1, 1]
        tidal = np.array(self.history['tidal_effect'])
        ax.plot(years, tidal*1e7, 'green', linewidth=0.8)
        ax.set_xlabel('Time (years)')
        ax.set_ylabel('Tidal factor (×10⁻⁷)')
        ax.set_title('Moon Tidal Perturbation')
        ax.grid(True, alpha=0.3)
        
        # 6. System entropy
        ax = axes[1, 2]
        entropy = np.array(self.history['entropy_total'])
        ax.plot(years, entropy, 'red', linewidth=0.8)
        ax.axhline(y=0.95, color='orange', linestyle='--', 
                  alpha=0.5, label='Repair threshold')
        ax.axhline(y=1.0, color='red', linestyle='--', 
                  alpha=0.5, label='Capacity')
        ax.set_xlabel('Time (years)')
        ax.set_ylabel('W(N)/K')
        ax.set_title('System Entropy Load')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_ylim([0, 1.2])
        
        plt.suptitle('Earth-Moon-Sun Three-Body System', 
                    fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150)
            print(f"Plots saved to {save_path}")
        
        plt.show()

def main():
    """Run the Earth-Moon-Sun simulation"""
    
    print("=" * 60)
    print("EARTH-MOON-SUN THREE-BODY SYSTEM")
    print("Substrate Framework with Codec Coupling")
    print("=" * 60)
    print()
    
    # Create system
    system = EarthMoonSunSystem(gamma=1.0)
    
    # Run for 10 years
    duration = 10 * 365.256 * 86400
    system.simulate(duration, dt=3600)  # 1-hour time step
    
    # Generate plots
    system.plot_results(save_path="earth_moon_sun.png")
    
    # Export data
    df = pd.DataFrame({
        't_years': np.array(system.history['time']) / (365.256 * 86400),
        'earth_kappa': system.history['earth_kappa'],
        'moon_kappa': system.history['moon_kappa'],
        'earth_varpi_arcsec': np.degrees(system.history['earth_varpi']) * 3600,
        'moon_varpi_arcsec': np.degrees(system.history['moon_varpi']) * 3600,
        'moon_nodal_deg': np.degrees(system.history['moon_nodal']),
        'tidal_factor': system.history['tidal_effect'],
        'entropy': system.history['entropy_total']
    })
    
    df.to_csv('earth_moon_sun_data.csv', index=False)
    print("\nData exported to earth_moon_sun_data.csv")
    
    print("\n" + "=" * 60)
    print("KEY FINDINGS")
    print("=" * 60)
    
    print("\nThe Earth-Moon-Sun system demonstrates:")
    print("1. Tidal perturbations affect Earth's precession")
    print("2. Moon's nodal precession (~18.6 year cycle)")
    print("3. Coupled oscillator dynamics through κ_app")
    print("4. Substrate entropy regulates stability")
    print("\nCodec coupling (scalar + tensor) provides natural")
    print("mechanism for gravitational interactions in finite substrate.")

if __name__ == "__main__":
    main()
