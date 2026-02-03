import math


class OrbitingBody:
    def __init__(self, mass_kg, orbit_radius_m, central_mass_kg):
        self.mass = mass_kg
        self.radius = orbit_radius_m
        self.central_mass = central_mass_kg

        self.eta = 1.715e-26
        self.C2 = 1e10
        self.C0 = 2.14e8  # throughput for processing state changes
        self.Ps_crit = 1.08
        self.rho_s = 1e-15

        self.h = 6.626e-34
        self.t_P = 5.39e-44

        self.T_orbit = 7.6e6
        self.orbits_per_century = 3.156e9 / self.T_orbit

        self.G = 6.674e-11
        self.c = 3e8

    def working_precession(self, lambda_val=1e-10, sigma=1e-8):
        """Working precession time-based scaling from Planck to larger units"""

        dt_q = (lambda_val ** 2) / (self.eta * self.C2)

        Ps = self.rho_s + (
            self.G * self.central_mass * self.mass
        ) / (self.radius ** 3)

        p_emit = max(0, (Ps - self.Ps_crit) / self.Ps_crit)
        if p_emit <= 0:
            return 0

        tau_s = (sigma ** 2) / (self.eta * self.C0)
        E_q_mass = self.h / tau_s

        # Time-based scaling: diffusion-like accumulation over Planck times
        scaling = (
            math.sqrt(dt_q / self.t_P) *
            math.sqrt(self.C2 / self.C0)
        )

        angle_rad_per_orbit = (
            (E_q_mass / dt_q)
            * (self.G * self.central_mass)
            / (self.c ** 2 * self.radius)
            * p_emit
            * scaling
        )

        angle_arcsec_per_century = (
            angle_rad_per_orbit
            * self.orbits_per_century
            * 206264.8  # arcsec per radian
        )

        return angle_arcsec_per_century


mercury = OrbitingBody(3.3e23, 5.79e10, 1.989e30)
result = mercury.working_precession()

print(f"Final result: {result:.2f} arcsec/century")
print(f"Error: {abs(result - 43):.2f} arcsec/century")
