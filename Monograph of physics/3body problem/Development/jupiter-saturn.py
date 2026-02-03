# jup_sat_quant02.py
# Jupiter–Saturn stew-field resonance simulation

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# =====================================================
# Parameters
# =====================================================
G = 1.0
c = 1.0
gamma = 1.0
dt = 0.01
steps = 20000

# stew-field parameters
eta = 1e-8
C0 = 1.0
C2 = 1.0
dt_q = (eta * C2) / 2.0
tau_s = (eta * C0) / 2.0

entropy_capacity = 1.0
drag_scale = 0.01

# =====================================================
# Helper functions
# =====================================================
def gravitational_potential(masses, positions, i):
    phi = 0.0
    pos_i = positions[i]
    for j, m_j in enumerate(masses):
        if i != j:
            r_ij = np.linalg.norm(pos_i - positions[j])
            if r_ij > 1e-10:
                phi -= G * m_j / r_ij
    return phi

def apparent_curvature(phi):
    return -(1 + gamma) * phi / (c ** 2)

def newtonian_acceleration(masses, positions, i):
    acc = np.zeros(2)
    for j, m_j in enumerate(masses):
        if i != j:
            r_vec = positions[j] - positions[i]
            r = np.linalg.norm(r_vec)
            if r > 1e-10:
                acc += G * m_j * r_vec / r ** 3
    return acc

# =====================================================
# Initial conditions
# =====================================================
names = ["Sun", "Jupiter", "Saturn"]
masses = np.array([1000.0, 1.0, 0.3])

positions = np.array([
    [0.0, 0.0],
    [5.2, 0.0],
    [9.5, 0.0]
], dtype=float)

velocities = np.array([
    [0.0, 0.0],
    [0.0, np.sqrt(G * masses[0] / np.linalg.norm(positions[1]))],
    [0.0, np.sqrt(G * masses[0] / np.linalg.norm(positions[2]))]
], dtype=float)

# =====================================================
# Storage
# =====================================================
kappa_history = []
entropy_history = []
precession_history = []
phase_diff_history = []
positions_history = []

entropy_load = 0.0
total_precession = 0.0

# =====================================================
# Main loop
# =====================================================
for step in range(steps):
    phi = np.array([gravitational_potential(masses, positions, i) for i in range(3)])
    kappa = np.array([apparent_curvature(p) for p in phi])
    kappa_history.append(kappa[1:])

    acc = np.array([newtonian_acceleration(masses, positions, i) for i in range(3)])

    diffusion_scale = np.sqrt(dt_q / dt)
    phase_noise = np.random.normal(0, diffusion_scale * 0.001, acc.shape)
    acc += phase_noise

    if entropy_load > entropy_capacity:
        acc *= (1.0 - drag_scale * (entropy_load - entropy_capacity))

    velocities += acc * dt
    positions += velocities * dt

    entropy_load = np.var(phi)
    entropy_history.append(entropy_load)

    total_precession += np.mean(kappa[1:]) * dt
    precession_history.append(total_precession)

    phase_j = np.arctan2(positions[1,1], positions[1,0])
    phase_s = np.arctan2(positions[2,1], positions[2,0])
    phase_diff = 5 * phase_s - 2 * phase_j
    phase_diff_history.append(np.sin(phase_diff))

    positions_history.append(positions.copy())

positions_history = np.array(positions_history)
entropy_history = np.array(entropy_history)
precession_history = np.array(precession_history)
phase_diff_history = np.array(phase_diff_history)

# =====================================================
# Plotting
# =====================================================
fig, axs = plt.subplots(3, 3, figsize=(14, 10))
fig.suptitle("Stew-Field Jupiter–Saturn Resonance Model", fontsize=14)

# 1) Orbits
axs[0,0].plot(positions_history[:,1,0], positions_history[:,1,1], label="Jupiter", color='orange')
axs[0,0].plot(positions_history[:,2,0], positions_history[:,2,1], label="Saturn", color='brown')
axs[0,0].plot(positions_history[:,0,0], positions_history[:,0,1], 'yo', label="Sun")
axs[0,0].set_title("Orbital Trajectories")
axs[0,0].legend()

# 2) κ_app
axs[0,1].plot(kappa_history)
axs[0,1].set_title("Apparent Curvature κ_app (Jupiter, Saturn)")
axs[0,1].set_ylabel("κ_app")

# 3) Entropy load
axs[0,2].plot(entropy_history, color='purple')
axs[0,2].set_title("Normalized Entropy Load W(N)/K")

# 4) Virtual drag
axs[1,0].plot(np.maximum(0, entropy_history - entropy_capacity), color='red')
axs[1,0].set_title("Virtual Drag (Overflow)")

# 5) Resonance phase
axs[1,1].plot(phase_diff_history, color='green')
axs[1,1].set_title("5:2 Resonance Phase Combination")

# 6) Precession
axs[1,2].plot(precession_history, color='blue')
axs[1,2].set_title("Cumulative Precession (κ_app-driven)")

# 7–9 diagnostics
axs[2,0].plot(np.gradient(precession_history), color='gray')
axs[2,0].set_title("Precession Rate Derivative")

axs[2,1].hist(entropy_history, bins=30, color='gray', alpha=0.7)
axs[2,1].set_title("Entropy Distribution")

axs[2,2].axis("off")
axs[2,2].text(0.1, 0.5, "Stew-field Quantization\nJupiter–Saturn Simulation\nv0.2", fontsize=12)

plt.tight_layout()
plt.show()

# Export data
df = pd.DataFrame({
    'time': np.arange(len(precession_history)) * dt,
    'entropy': entropy_history,
    'precession': precession_history,
    'phase_diff': phase_diff_history
})
df.to_csv("jup_sat_quant02_output.csv", index=False)
print("Simulation complete. Data saved to jup_sat_quant02_output.csv")
