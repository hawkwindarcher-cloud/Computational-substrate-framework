# Galilean moons demo with quantisation-delay precession
# - Planar N-body (Jupiter + Io, Europa, Ganymede)
# - Symplectic leapfrog (kick-drift-kick)
# - Diagnostics: Laplace angle and integrated precession via kappa_app = -2*Phi/c^2

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ----- Constants -----
G = 6.67430e-11           # m^3 kg^-1 s^-2
c = 299_792_458.0         # m/s

# Jupiter + moons masses (kg)
M_jup = 1.89813e27
m_io  = 8.931938e22
m_eu  = 4.799844e22
m_ga  = 1.4819e23
masses = np.array([M_jup, m_io, m_eu, m_ga])

muJ = G * M_jup

# Mean orbital radii (m) ~ semimajor axes
a_io = 421_800e3
a_eu = 671_100e3
a_ga = 1_070_400e3

# Circular speeds about Jupiter
v_io = np.sqrt(muJ / a_io)
v_eu = np.sqrt(muJ / a_eu)
v_ga = np.sqrt(muJ / a_ga)

# ----- Initial conditions (planar, nearly circular) -----
pos = np.zeros((4, 3))
vel = np.zeros((4, 3))

# Place Europa & Ganymede at theta=0; Io at pi so Laplace angle ~ 180°
pos[0] = [0.0, 0.0, 0.0]     # Jupiter provisional
pos[1] = [-a_io, 0.0, 0.0]   # Io
pos[2] = [ a_eu, 0.0, 0.0]   # Europa
pos[3] = [ a_ga, 0.0, 0.0]   # Ganymede

# Perpendicular velocities (counterclockwise positive y)
vel[1] = [0.0, -v_io, 0.0]   # choose sign to keep a clean phase choice
vel[2] = [0.0,  v_eu, 0.0]
vel[3] = [0.0,  v_ga, 0.0]

# Make total momentum zero by giving Jupiter a compensating velocity
p_tot_moons = (m_io*vel[1] + m_eu*vel[2] + m_ga*vel[3])
vel[0] = -p_tot_moons / M_jup

# ----- Integrator settings -----
dt = 300.0                 # 5 minutes
days = 40.0
T = days * 86400.0
steps = int(T / dt)

# ----- Helpers -----
def accel(positions, masses):
    n = len(masses)
    a = np.zeros_like(positions)
    for i in range(n):
        for j in range(i+1, n):
            r = positions[j] - positions[i]
            d2 = np.dot(r, r) + 1e-12
            inv_r3 = 1.0 / (d2 ** 1.5)
            f = G * masses[i] * masses[j] * inv_r3 * r
            a[i] +=  f / masses[i]
            a[j] += -f / masses[j]
    return a

def potential_at(i, positions, masses):
    Phi = 0.0
    ri = positions[i]
    for j in range(len(masses)):
        if j == i:
            continue
        r = np.linalg.norm(positions[j] - ri) + 1e-12
        Phi += -G * masses[j] / r
    return Phi

def lambda_rel(body_index, positions):
    r_rel = positions[body_index] - positions[0]  # relative to Jupiter
    return np.arctan2(r_rel[1], r_rel[0])

# ----- Storage -----
ts = np.zeros(steps+1)
XY_io = np.zeros((steps+1, 2))
XY_eu = np.zeros((steps+1, 2))
XY_ga = np.zeros((steps+1, 2))
phi_L = np.zeros(steps+1)                # Laplace angle: λ_Io - 3 λ_Eu + 2 λ_Ga
kappa_io = np.zeros(steps+1)
kappa_eu = np.zeros(steps+1)
kappa_ga = np.zeros(steps+1)
varpi_io = np.zeros(steps+1)             # integrated precession (radians)
varpi_eu = np.zeros(steps+1)
varpi_ga = np.zeros(steps+1)

# Initial logs
XY_io[0] = (pos[1]-pos[0])[:2]
XY_eu[0] = (pos[2]-pos[0])[:2]
XY_ga[0] = (pos[3]-pos[0])[:2]

lam_io = lambda_rel(1, pos)
lam_eu = lambda_rel(2, pos)
lam_ga = lambda_rel(3, pos)
phi_L[0] = (lam_io - 3*lam_eu + 2*lam_ga + np.pi) % (2*np.pi) - np.pi

for idx, arr_k in zip([1,2,3], [kappa_io, kappa_eu, kappa_ga]):
    Phi = potential_at(idx, pos, masses)
    arr_k[0] = -2.0 * Phi / (c**2)  # gamma=1  ⇒  kappa_app = -2 Phi/c^2

# ----- Leapfrog integration -----
a_now = accel(pos, masses)
for k in range(1, steps+1):
    # KICK half
    vel += 0.5 * dt * a_now
    # DRIFT
    pos += dt * vel
    # Force at new positions
    a_now = accel(pos, masses)
    # KICK half
    vel += 0.5 * dt * a_now

    # Logs
    ts[k] = k*dt
    XY_io[k] = (pos[1]-pos[0])[:2]
    XY_eu[k] = (pos[2]-pos[0])[:2]
    XY_ga[k] = (pos[3]-pos[0])[:2]

    lam_io = lambda_rel(1, pos)
    lam_eu = lambda_rel(2, pos)
    lam_ga = lambda_rel(3, pos)
    phi_L[k] = (lam_io - 3*lam_eu + 2*lam_ga + np.pi) % (2*np.pi) - np.pi

    Phi_io = potential_at(1, pos, masses)
    Phi_eu = potential_at(2, pos, masses)
    Phi_ga = potential_at(3, pos, masses)
    kappa_io[k] = -2.0 * Phi_io / (c**2)
    kappa_eu[k] = -2.0 * Phi_eu / (c**2)
    kappa_ga[k] = -2.0 * Phi_ga / (c**2)

    # Instantaneous Kepler frequencies around Jupiter (for the click rule)
    r_io = np.linalg.norm(pos[1]-pos[0])
    r_eu = np.linalg.norm(pos[2]-pos[0])
    r_ga = np.linalg.norm(pos[3]-pos[0])
    n_io = np.sqrt(muJ / (r_io**3))
    n_eu = np.sqrt(muJ / (r_eu**3))
    n_ga = np.sqrt(muJ / (r_ga**3))

    # Integrate Δϖ = κ_app * n * Δt
    varpi_io[k] = varpi_io[k-1] + kappa_io[k] * n_io * dt
    varpi_eu[k] = varpi_eu[k-1] + kappa_eu[k] * n_eu * dt
    varpi_ga[k] = varpi_ga[k-1] + kappa_ga[k] * n_ga * dt

# ----- Plots -----
# 1) XY orbits relative to Jupiter
plt.figure(figsize=(6,6))
plt.plot(XY_io[:,0], XY_io[:,1], linewidth=1.0, label="Io")
plt.plot(XY_eu[:,0], XY_eu[:,1], linewidth=1.0, label="Europa")
plt.plot(XY_ga[:,0], XY_ga[:,1], linewidth=1.0, label="Ganymede")
plt.scatter([0],[0], s=20, label="Jupiter")
plt.axis('equal')
plt.xlabel("x (m)")
plt.ylabel("y (m)")
plt.title("Galilean moons — planar N-body (leapfrog)")
plt.legend()
plt.tight_layout()
plt.show()

# 2) Laplace resonant angle
plt.figure(figsize=(7,4))
plt.plot(ts/86400.0, np.degrees(phi_L), linewidth=1.0)
plt.xlabel("time (days)")
plt.ylabel("Laplace angle φ_L (deg)")
plt.title("Laplace 1:2:4 resonant angle")
plt.tight_layout()
plt.show()

# 3) Integrated precession from quantisation delays (arcsec)
plt.figure(figsize=(7,4))
plt.plot(ts/86400.0, np.degrees(varpi_io)*3600.0, linewidth=1.0, label="Io")
plt.plot(ts/86400.0, np.degrees(varpi_eu)*3600.0, linewidth=1.0, label="Europa")
plt.plot(ts/86400.0, np.degrees(varpi_ga)*3600.0, linewidth=1.0, label="Ganymede")
plt.xlabel("time (days)")
plt.ylabel("Integrated precession (arcsec)")
plt.title("Quantisation-delay precession integral (Δϖ)")
plt.legend()
plt.tight_layout()
plt.show()

# ----- Export CSV -----
df = pd.DataFrame({
    "t_s": ts,
    "t_days": ts/86400.0,
    "phi_L_rad": phi_L,
    "phi_L_deg": np.degrees(phi_L),
    "varpi_io_rad": varpi_io,
    "varpi_eu_rad": varpi_eu,
    "varpi_ga_rad": varpi_ga,
    "kappa_io": kappa_io,
    "kappa_eu": kappa_eu,
    "kappa_ga": kappa_ga,
    "x_io": XY_io[:,0], "y_io": XY_io[:,1],
    "x_eu": XY_eu[:,0], "y_eu": XY_eu[:,1],
    "x_ga": XY_ga[:,0], "y_ga": XY_ga[:,1],
})
out = Path("galilean_quant_delay_demo.csv")
df.to_csv(out, index=False)
print(f"Saved diagnostics to {out.resolve()}")
