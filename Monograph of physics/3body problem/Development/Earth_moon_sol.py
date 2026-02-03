# ThreeBodySystem model for Earth-Moon-Sun, extending the OrbitingBody logic.
# Simulates basic orbital interactions and precession-like effects in the stew-field framework.
# Focuses on Earth's orbit around Sun with Moon's perturbation, computing combined precession or stability.
# Uses Codec1 (scalar) and Codec3 (tensor) for symbolic delays/mass.
# Calibrated roughly for Earth-Moon-Sun: Earth-Sun distance ~1.5e11 m, Earth-Moon ~3.84e8 m.
# Outputs stability, precession angles, or entropy over orbits.

from stew_codecs import Codec1, Codec3
import math

class ThreeBodySystem:
    def __init__(self, sun_mass_kg=1.989e30, earth_mass_kg=5.972e24, moon_mass_kg=7.342e22,
                 earth_sun_radius_m=1.496e11, earth_moon_radius_m=3.844e8,
                 earth_orbit_period_s=3.156e7, moon_orbit_period_s=2.36e6):
        self.coherence = 1.0
        self.entropy = 0.0
        self.identity = 1.0
        self.sun_mass = sun_mass_kg
        self.earth_mass = earth_mass_kg
        self.moon_mass = moon_mass_kg
        self.earth_sun_radius = earth_sun_radius_m
        self.earth_moon_radius = earth_moon_radius_m
        self.eta = 1e-45  # Stew viscosity
        self.C2 = 1e-2  # Tensor complexity
        self.C0 = 1e6  # Scalar complexity
        self.Pe_crit = 1.24e17  # Emission crit
        self.rho_s = 1e18  # Stew density
        self.t_P = 5.39e-44  # Planck time
        self.T_earth_orbit = earth_orbit_period_s  # ~1 year
        self.T_moon_orbit = moon_orbit_period_s  # ~27.3 days
        self.earth_orbits_per_year = 1.0  # By definition
        self.moon_orbits_per_earth_orbit = self.T_earth_orbit / self.T_moon_orbit  # ~13.37
        self.G = 6.674e-11
        self.c = 3e8
        self.L_eff = 1e-7  # Coherence length
        self.codec1 = Codec1()  # Scalar mass
        self.codec3 = Codec3()  # Tensor delay
        self.precession_history = []  # Track angles or stability

    def codec3_tensor_delay(self, lambda_val, v_c=0.0, perturbation_factor=1.0):
        """Tensor delay, with moon perturbation factor."""
        delay = self.codec3.tensor_delay(lambda_val=lambda_val)['delay']
        rho_max = max(0, (self.rho_s + (self.G * self.sun_mass * self.earth_mass) / (self.earth_sun_radius ** 3) - self.Pe_crit) / self.Pe_crit)
        delay *= (1 + rho_max * perturbation_factor) / math.sqrt(1 - v_c ** 2)
        return delay

    def codec1_scalar_mass(self, sigma):
        """Scalar mass, combined for Earth-Moon."""
        mass_energy = self.codec1.scalar_mass(sigma=sigma)
        combined_mass = self.earth_mass + self.moon_mass
        return mass_energy * (combined_mass / self.earth_mass)  # Scale by Moon influence

    def precession(self, lambda_val=1e11, sigma=1e-9, v_c_earth=1e-4, v_c_moon=3e-3, num_earth_orbits=1):
        """Compute precession for Earth-Sun with Moon perturbation."""
        results = []
        moon_perturbation = (self.moon_mass / self.earth_mass) * (self.earth_sun_radius / self.earth_moon_radius) ** 2  # Tidal-like factor ~2e-7
        for _ in range(num_earth_orbits):
            # Earth-Sun base
            gravity_delay_earth = self.codec3_tensor_delay(lambda_val, v_c_earth)
            scalar_mass_earth = self.codec1_scalar_mass(sigma)
            if gravity_delay_earth > 0 and scalar_mass_earth > 0:
                rho_orbit_earth = (gravity_delay_earth / (sigma ** 2 / (self.eta * self.C0))) - (self.G * self.sun_mass) / (self.c ** 2 * self.earth_sun_radius)
                rho_max_earth = max(0, (self.rho_s + (self.G * self.sun_mass * self.earth_mass) / (self.earth_sun_radius ** 3) - self.Pe_crit) / self.Pe_crit) / (1 + (v_c_earth ** 2))
                angle_rad_per_earth_orbit = (6 * math.pi * self.G * self.sun_mass) / (self.c ** 2 * self.earth_sun_radius * (1 - rho_max_earth ** 2)) + rho_orbit_earth
                
                # Add Moon perturbation to angle
                gravity_delay_moon = self.codec3_tensor_delay(lambda_val / 100, v_c_moon, perturbation_factor=moon_perturbation)  # Scaled lambda for Moon
                rho_orbit_moon = (gravity_delay_moon / (sigma ** 2 / (self.eta * self.C0))) - (self.G * self.earth_mass) / (self.c ** 2 * self.earth_moon_radius)
                angle_rad_per_earth_orbit += rho_orbit_moon * self.moon_orbits_per_earth_orbit  # Accumulate over Moon orbits
                
                angle_arcsec_per_earth_orbit = angle_rad_per_earth_orbit * (180 * 3600 / math.pi)
                angle_arc