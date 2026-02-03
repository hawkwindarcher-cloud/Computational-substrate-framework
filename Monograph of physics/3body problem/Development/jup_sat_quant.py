import numpy as np
import matplotlib.pyplot as plt

# Constants
G = 6.67430e-11  # Gravitational constant (m^3 kg^-1 s^-2)
c = 2.998e8      # Speed of light (m/s)
AU = 1.496e11    # Astronomical Unit (m)
M_Sun = 1.989e30 # Solar mass (kg)
M_J = 1.898e27   # Jupiter mass (kg)
M_S = 5.683e26   # Saturn mass (kg)
a_J = 5.2 * AU   # Jupiter semi-major axis (m)
a_S = 9.5 * AU   # Saturn semi-major axis (m)
P_J = 11.86 * 365.25 * 86400  # Jupiter period (s)
P_S = 29.46 * 365.25 * 86400  # Saturn period (s)

# Stew-field parameters
gamma = 1.0      # PPN parameter (GR value)
K = 1e6          # Capacity constraint (per paper)
dt = 86400 * 10  # Time step (10 days)
t_max = 2000 * 365.25 * 86400  # 2000 years
n_steps = int(t_max / dt)

print(f"Running κ_app quantization simulation for {t_max / (365.25 * 86400):.0f} years with {n_steps} steps")

# Initial conditions
theta_J = 0.0    # Initial phases (radians)
theta_S = 0.0
r_J = a_J        # Initial radii (m)
r_S = a_S
e_J = 0.048      # Eccentricities
e_S = 0.056

# Mean motions
n_J = 2 * np.pi / P_J  # rad/s
n_S = 2 * np.pi / P_S

# Arrays for results
time = np.zeros(n_steps)
theta_J_arr = np.zeros(n_steps)
theta_S_arr = np.zeros(n_steps)
r_J_arr = np.zeros(n_steps)
r_S_arr = np.zeros(n_steps)
kappa_app_J = np.zeros(n_steps)
kappa_app_S = np.zeros(n_steps)
phase_diffusion_J = np.zeros(n_steps)
phase_diffusion_S = np.zeros(n_steps)
precession_J = np.zeros(n_steps)
precession_S = np.zeros(n_steps)

# Quantization scaling factors (from paper's diffusion theory)
# These represent the codec complexity ratios C2/C0
codec_ratio = 1e-15  # Planck-scale diffusion factor
diffusion_scale = np.sqrt(codec_ratio)

def calculate_kappa_app(r_body, M_central):
    """Calculate apparent curvature index κ_app = -(1+γ)Φ/c²"""
    Phi = -G * M_central / r_body  # Gravitational potential
    return -(1 + gamma) * Phi / c**2

def gravitational_acceleration(r1, r2, M1, M2):
    """Calculate gravitational acceleration between two bodies"""
    dr = r2 - r1
    r_sep = np.abs(dr)
    if r_sep > 0:
        return G * M2 * np.sign(dr) / r_sep**2
    return 0

# Simulation loop
for i in range(n_steps):
    time[i] = i * dt
    
    # Update elliptical orbits (Kepler's equation approximation)
    r_J = a_J * (1 + e_J * np.cos(theta_J))
    r_S = a_S * (1 + e_S * np.cos(theta_S))
    
    # Calculate κ_app for each body (from Sun's potential)
    kappa_J = calculate_kappa_app(r_J, M_Sun)
    kappa_S = calculate_kappa_app(r_S, M_Sun)
    
    # Store κ_app values
    kappa_app_J[i] = kappa_J
    kappa_app_S[i] = kappa_S
    
    # Calculate mutual gravitational perturbations
    acc_J_sun = -G * M_Sun / r_J**2  # From Sun
    acc_S_sun = -G * M_Sun / r_S**2
    
    # Mutual perturbations (Jupiter-Saturn)
    acc_J_mut = gravitational_acceleration(r_J, r_S, M_J, M_S)
    acc_S_mut = gravitational_acceleration(r_S, r_J, M_S, M_J)
    
    total_acc_J = acc_J_sun + acc_J_mut
    total_acc_S = acc_S_sun + acc_S_mut
    
    # Phase updates with κ_app corrections
    # Base Keplerian motion
    delta_theta_J_base = n_J * dt
    delta_theta_S_base = n_S * dt
    
    # κ_app induced phase diffusion (from paper's quantum diffusion theory)
    # Phase mismatch accumulates as sqrt(N) random walk over N ticks
    ticks_per_step = dt / (1e-43)  # Approximate Planck time ticks
    phase_diffusion_amplitude_J = np.abs(kappa_J) * np.sqrt(ticks_per_step) * diffusion_scale
    phase_diffusion_amplitude_S = np.abs(kappa_S) * np.sqrt(ticks_per_step) * diffusion_scale
    
    # Add small deterministic drift (simplified from paper's eq. 3)
    perihelion_correction_J = kappa_J * n_J * dt * (G * M_Sun) / (c**2 * r_J)
    perihelion_correction_S = kappa_S * n_S * dt * (G * M_Sun) / (c**2 * r_S)
    
    # Store phase diffusion and precession
    phase_diffusion_J[i] = phase_diffusion_amplitude_J
    phase_diffusion_S[i] = phase_diffusion_amplitude_S
    precession_J[i] = perihelion_correction_J
    precession_S[i] = perihelion_correction_S
    
    # Total phase updates
    delta_theta_J = delta_theta_J_base + perihelion_correction_J
    delta_theta_S = delta_theta_S_base + perihelion_correction_S
    
    # Apply quantization delays (simplified virtual drag)
    # When |κ_app| is large, add extra drag
    if np.abs(kappa_J) > 1e-8:
        drag_J = -kappa_J * delta_theta_J_base * 0.01
        delta_theta_J += drag_J
    
    if np.abs(kappa_S) > 1e-8:
        drag_S = -kappa_S * delta_theta_S_base * 0.01
        delta_theta_S += drag_S
    
    # Update phases
    theta_J += delta_theta_J
    theta_S += delta_theta_S
    
    # Keep phases in reasonable range
    theta_J = theta_J % (2 * np.pi)
    theta_S = theta_S % (2 * np.pi)
    
    # Store results
    theta_J_arr[i] = theta_J
    theta_S_arr[i] = theta_S
    r_J_arr[i] = r_J
    r_S_arr[i] = r_S

# Analysis
# 5:2 resonance phase difference
phase_diff_52 = 5 * theta_S_arr - 2 * theta_J_arr

# Calculate cumulative precession (integrate the corrections)
cumulative_precession_J = np.cumsum(precession_J) * 180/np.pi * 3600  # arcseconds
cumulative_precession_S = np.cumsum(precession_S) * 180/np.pi * 3600

# Convert to per-century rates
years = time / (365.25 * 86400)
if years[-1] > 0:
    precession_rate_J = cumulative_precession_J[-1] / years[-1] * 100  # "/century
    precession_rate_S = cumulative_precession_S[-1] / years[-1] * 100
else:
    precession_rate_J = 0
    precession_rate_S = 0

# Plotting
plt.figure(figsize=(16, 12))

plt.subplot(3, 3, 1)
plt.plot(years, theta_J_arr, 'b-', label='Jupiter', alpha=0.8, linewidth=0.8)
plt.plot(years, theta_S_arr, 'r-', label='Saturn', alpha=0.8, linewidth=0.8)
plt.xlabel('Time (years)')
plt.ylabel('Phase (radians)')
plt.title('Orbital Phases with κ_app corrections')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(3, 3, 2)
plt.plot(years, phase_diff_52, 'g-', linewidth=0.8)
plt.xlabel('Time (years)')
plt.ylabel('5θ_S - 2θ_J (radians)')
plt.title('5:2 Resonance Phase Difference')
plt.grid(True, alpha=0.3)

plt.subplot(3, 3, 3)
plt.semilogy(years, np.abs(kappa_app_J), 'b-', label='Jupiter', linewidth=0.8)
plt.semilogy(years, np.abs(kappa_app_S), 'r-', label='Saturn', linewidth=0.8)
plt.xlabel('Time (years)')
plt.ylabel('|κ_app|')
plt.title('Apparent Curvature Index')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(3, 3, 4)
plt.plot(years, r_J_arr / AU, 'b-', label='Jupiter', linewidth=0.8)
plt.plot(years, r_S_arr / AU, 'r-', label='Saturn', linewidth=0.8)
plt.xlabel('Time (years)')
plt.ylabel('Distance from Sun (AU)')
plt.title('Orbital Radii')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(3, 3, 5)
plt.semilogy(years, phase_diffusion_J, 'b-', label='Jupiter', linewidth=0.8)
plt.semilogy(years, phase_diffusion_S, 'r-', label='Saturn', linewidth=0.8)
plt.xlabel('Time (years)')
plt.ylabel('Phase Diffusion Amplitude')
plt.title('Quantum Phase Diffusion')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(3, 3, 6)
plt.plot(years, cumulative_precession_J, 'b-', label=f'Jupiter ({precession_rate_J:.3f}"/cent)', linewidth=0.8)
plt.plot(years, cumulative_precession_S, 'r-', label=f'Saturn ({precession_rate_S:.3f}"/cent)', linewidth=0.8)
plt.xlabel('Time (years)')
plt.ylabel('Cumulative Precession (arcsec)')
plt.title('Perihelion Precession from κ_app')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(3, 3, 7)
# Orbital trajectories
x_J = r_J_arr * np.cos(theta_J_arr)
y_J = r_J_arr * np.sin(theta_J_arr)
x_S = r_S_arr * np.cos(theta_S_arr)
y_S = r_S_arr * np.sin(theta_S_arr)

plt.plot(x_J / AU, y_J / AU, 'b-', alpha=0.6, linewidth=0.5, label='Jupiter')
plt.plot(x_S / AU, y_S / AU, 'r-', alpha=0.6, linewidth=0.5, label='Saturn')
plt.plot(0, 0, 'yo', markersize=8, label='Sun')
plt.xlabel('X (AU)')
plt.ylabel('Y (AU)')
plt.title('Orbital Paths')
plt.axis('equal')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(3, 3, 8)
# Phase space plot: κ_app vs phase diffusion
plt.scatter(kappa_app_J * 1e8, phase_diffusion_J * 1e15, c=years, s=1, alpha=0.6, label='Jupiter')
plt.scatter(kappa_app_S * 1e8, phase_diffusion_S * 1e15, c=years, s=1, alpha=0.6, label='Saturn')
plt.xlabel('κ_app × 10⁸')
plt.ylabel('Phase Diffusion × 10¹⁵')
plt.title('κ_app vs Quantum Diffusion')
plt.colorbar(label='Time (years)')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(3, 3, 9)
# Resonance strength over time
resonance_strength = np.abs(np.sin(phase_diff_52))
plt.plot(years, resonance_strength, 'purple', linewidth=0.8)
plt.xlabel('Time (years)')
plt.ylabel('|sin(5θ_S - 2θ_J)|')
plt.title('Resonance Lock Strength')
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

print(f"Simulation completed for {t_max / (365.25 * 86400):.0f} years")
print(f"Jupiter precession rate: {precession_rate_J:.4f} arcsec/century")
print(f"Saturn precession rate: {precession_rate_S:.4f} arcsec/century")
print(f"Mean |κ_app| - Jupiter: {np.mean(np.abs(kappa_app_J)):.2e}")
print(f"Mean |κ_app| - Saturn: {np.mean(np.abs(kappa_app_S)):.2e}")
print(f"Phase difference range: {np.min(phase_diff_52):.2f} to {np.max(phase_diff_52):.2f} rad")
print(f"Mean resonance lock strength: {np.mean(resonance_strength):.3f}")

# Compare with Mercury's 43"/century for reference
print(f"\nFor comparison, Mercury's precession: 43.0 arcsec/century")
print(f"Jupiter/Mercury ratio: {precession_rate_J/43.0:.4f}")
print(f"Saturn/Mercury ratio: {precession_rate_S/43.0:.4f}")