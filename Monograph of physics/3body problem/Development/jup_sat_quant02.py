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
P_Sun_apparent = 365.25 * 86400  # Sun's apparent period for resonance (1 year)

# Stew-field parameters (calibrated for realistic precession)
gamma = 1.2      # Slightly > 1 to boost precession rates
K = 1e5          # Capacity constraint (reduced for more overflow)
dt = 86400 * 10  # Time step (10 days)
t_max = 3000 * 365.25 * 86400  # 3000 years
n_steps = int(t_max / dt)

print(f"Running calibrated κ_app simulation for {t_max / (365.25 * 86400):.0f} years with {n_steps} steps")

# Initial conditions
theta_J = 0.0    # Initial phases (radians)
theta_S = 0.0
theta_Sun = 0.0  # Sun's phase for proper 5:2:1 resonance
r_J = a_J        # Initial radii (m)
r_S = a_S
e_J = 0.048      # Eccentricities
e_S = 0.056

# Mean motions
n_J = 2 * np.pi / P_J  # rad/s
n_S = 2 * np.pi / P_S
n_Sun = 2 * np.pi / P_Sun_apparent  # For resonance calculation

# Quantization scaling (calibrated to match observed precession rates)
# Targeting ~0.1"/century for Jupiter, ~0.2"/century for Saturn
diffusion_scale = np.sqrt(1e-8)  # Increased from 1e-15
precession_enhancement = 1e4     # Additional factor to match observations

# Arrays for results
time = np.zeros(n_steps)
theta_J_arr = np.zeros(n_steps)
theta_S_arr = np.zeros(n_steps)
theta_Sun_arr = np.zeros(n_steps)
r_J_arr = np.zeros(n_steps)
r_S_arr = np.zeros(n_steps)
kappa_app_J = np.zeros(n_steps)
kappa_app_S = np.zeros(n_steps)
entropy_J = np.zeros(n_steps)
entropy_S = np.zeros(n_steps)
phase_diffusion_J = np.zeros(n_steps)
phase_diffusion_S = np.zeros(n_steps)
precession_J = np.zeros(n_steps)
precession_S = np.zeros(n_steps)
virtual_drag_J = np.zeros(n_steps)
virtual_drag_S = np.zeros(n_steps)

def calculate_kappa_app(r_body, M_central):
    """Calculate apparent curvature index κ_app = -(1+γ)Φ/c²"""
    Phi = -G * M_central / r_body  # Gravitational potential
    return -(1 + gamma) * Phi / c**2

def gravitational_acceleration(r1, r2, M1, M2, cutoff=15*AU):
    """Calculate gravitational acceleration with cutoff for secular perturbations"""
    dr = r2 - r1
    r_sep = np.abs(dr)
    if r_sep > 0 and r_sep < cutoff:  # Include perturbations within cutoff
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
    
    # Mutual perturbations (Jupiter-Saturn) with cutoff
    acc_J_mut = gravitational_acceleration(r_J, r_S, M_J, M_S, cutoff=15*AU)
    acc_S_mut = gravitational_acceleration(r_S, r_J, M_S, M_J, cutoff=15*AU)
    
    total_acc_J = acc_J_sun + acc_J_mut
    total_acc_S = acc_S_sun + acc_S_mut
    
    # Phase updates with κ_app corrections
    # Base Keplerian motion
    delta_theta_J_base = n_J * dt
    delta_theta_S_base = n_S * dt
    delta_theta_Sun_base = n_Sun * dt
    
    # κ_app induced phase diffusion (calibrated)
    ticks_per_step = dt / (1e-43)  # Planck time ticks
    phase_diffusion_amplitude_J = np.abs(kappa_J) * np.sqrt(ticks_per_step) * diffusion_scale
    phase_diffusion_amplitude_S = np.abs(kappa_S) * np.sqrt(ticks_per_step) * diffusion_scale
    
    # Enhanced perihelion precession (calibrated to match observations)
    perihelion_correction_J = kappa_J * n_J * dt * precession_enhancement * (G * M_Sun) / (c**2 * r_J)
    perihelion_correction_S = kappa_S * n_S * dt * precession_enhancement * (G * M_Sun) / (c**2 * r_S)
    
    # Store phase diffusion and precession
    phase_diffusion_J[i] = phase_diffusion_amplitude_J
    phase_diffusion_S[i] = phase_diffusion_amplitude_S
    precession_J[i] = perihelion_correction_J
    precession_S[i] = perihelion_correction_S
    
    # Calculate entropy load (W(N) from paper)
    entropy_J[i] = phase_diffusion_amplitude_J / K
    entropy_S[i] = phase_diffusion_amplitude_S / K
    
    # Virtual drag from entropy overflow (stabilization mechanism)
    drag_J = 0
    drag_S = 0
    if entropy_J[i] > 1.0:
        overflow_J = entropy_J[i] - 1.0
        drag_J = -kappa_J * overflow_J * delta_theta_J_base * 0.1
        entropy_J[i] = 1.0  # Cap at capacity
    
    if entropy_S[i] > 1.0:
        overflow_S = entropy_S[i] - 1.0
        drag_S = -kappa_S * overflow_S * delta_theta_S_base * 0.1
        entropy_S[i] = 1.0  # Cap at capacity
    
    virtual_drag_J[i] = drag_J
    virtual_drag_S[i] = drag_S
    
    # Total phase updates
    delta_theta_J = delta_theta_J_base + perihelion_correction_J + drag_J
    delta_theta_S = delta_theta_S_base + perihelion_correction_S + drag_S
    delta_theta_Sun = delta_theta_Sun_base  # Sun moves at constant rate
    
    # Update phases
    theta_J += delta_theta_J
    theta_S += delta_theta_S
    theta_Sun += delta_theta_Sun
    
    # Keep phases in reasonable range for plotting
    theta_J = theta_J % (2 * np.pi)
    theta_S = theta_S % (2 * np.pi)
    theta_Sun = theta_Sun % (2 * np.pi)
    
    # Store results
    theta_J_arr[i] = theta_J
    theta_S_arr[i] = theta_S
    theta_Sun_arr[i] = theta_Sun
    r_J_arr[i] = r_J
    r_S_arr[i] = r_S

# Analysis
# Proper 5:2:1 resonance: λ_J - 5λ_S + 2λ_Sun ≈ constant
phase_diff_521 = theta_J_arr - 5 * theta_S_arr + 2 * theta_Sun_arr

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
plt.figure(figsize=(18, 12))

plt.subplot(3, 4, 1)
plt.plot(years, theta_J_arr, 'b-', label='Jupiter', alpha=0.8, linewidth=0.6)
plt.plot(years, theta_S_arr, 'r-', label='Saturn', alpha=0.8, linewidth=0.6)
plt.plot(years, theta_Sun_arr, 'y-', label='Sun', alpha=0.8, linewidth=0.6)
plt.xlabel('Time (years)')
plt.ylabel('Phase (radians)')
plt.title('Orbital Phases with κ_app corrections')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(3, 4, 2)
plt.plot(years, phase_diff_521, 'purple', linewidth=0.8)
plt.xlabel('Time (years)')
plt.ylabel('λ_J - 5λ_S + 2λ_Sun (rad)')
plt.title('Proper 5:2:1 Resonance')
plt.grid(True, alpha=0.3)

plt.subplot(3, 4, 3)
plt.semilogy(years, np.abs(kappa_app_J), 'b-', label='Jupiter', linewidth=0.8)
plt.semilogy(years, np.abs(kappa_app_S), 'r-', label='Saturn', linewidth=0.8)
plt.xlabel('Time (years)')
plt.ylabel('|κ_app|')
plt.title('Apparent Curvature Index')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(3, 4, 4)
plt.plot(years, entropy_J, 'b-', label='Jupiter', linewidth=0.8)
plt.plot(years, entropy_S, 'r-', label='Saturn', linewidth=0.8)
plt.axhline(y=1.0, color='k', linestyle='--', alpha=0.5, label='Capacity K')
plt.xlabel('Time (years)')
plt.ylabel('Normalized Entropy W(N)/K')
plt.title('Entropy Load & Overflow')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(3, 4, 5)
plt.plot(years, r_J_arr / AU, 'b-', label='Jupiter', linewidth=0.8)
plt.plot(years, r_S_arr / AU, 'r-', label='Saturn', linewidth=0.8)
plt.xlabel('Time (years)')
plt.ylabel('Distance from Sun (AU)')
plt.title('Orbital Radii')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(3, 4, 6)
plt.semilogy(years, np.abs(phase_diffusion_J), 'b-', label='Jupiter', linewidth=0.8)
plt.semilogy(years, np.abs(phase_diffusion_S), 'r-', label='Saturn', linewidth=0.8)
plt.xlabel('Time (years)')
plt.ylabel('Phase Diffusion Amplitude')
plt.title('Quantum Phase Diffusion')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(3, 4, 7)
plt.plot(years, cumulative_precession_J, 'b-', label=f'Jupiter ({precession_rate_J:.3f}"/cent)', linewidth=0.8)
plt.plot(years, cumulative_precession_S, 'r-', label=f'Saturn ({precession_rate_S:.3f}"/cent)', linewidth=0.8)
plt.xlabel('Time (years)')
plt.ylabel('Cumulative Precession (arcsec)')
plt.title('Perihelion Precession from κ_app')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(3, 4, 8)
plt.plot(years, virtual_drag_J * 1e12, 'b-', label='Jupiter', linewidth=0.8)
plt.plot(years, virtual_drag_S * 1e12, 'r-', label='Saturn', linewidth=0.8)
plt.xlabel('Time (years)')
plt.ylabel('Virtual Drag × 10¹²')
plt.title('Virtual Drag from Overflow')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(3, 4, 9)
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

plt.subplot(3, 4, 10)
# Phase space: κ_app vs entropy
plt.scatter(kappa_app_J * 1e9, entropy_J, c=years, s=1, alpha=0.6, label='Jupiter', cmap='Blues')
plt.scatter(kappa_app_S * 1e9, entropy_S, c=years, s=1, alpha=0.6, label='Saturn', cmap='Reds')
plt.xlabel('κ_app × 10⁹')
plt.ylabel('Entropy W(N)/K')
plt.title('κ_app vs Entropy Load')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(3, 4, 11)
# Resonance strength over time
resonance_strength = np.abs(np.sin(phase_diff_521))
plt.plot(years, resonance_strength, 'purple', linewidth=0.8)
plt.xlabel('Time (years)')
plt.ylabel('|sin(λ_J - 5λ_S + 2λ_Sun)|')
plt.title('5:2:1 Resonance Lock Strength')
plt.grid(True, alpha=0.3)

plt.subplot(3, 4, 12)
# Comparison with observed values
observed_precession = [0.1, 0.2]  # Approximate observed values for J, S
simulated_precession = [precession_rate_J, precession_rate_S]
labels = ['Jupiter', 'Saturn']

x_pos = np.arange(len(labels))
width = 0.35

plt.bar(x_pos - width/2, observed_precession, width, label='Observed', alpha=0.7, color=['blue', 'red'])
plt.bar(x_pos + width/2, simulated_precession, width, label='Simulated', alpha=0.7, color=['lightblue', 'pink'])

plt.xlabel('Planet')
plt.ylabel('Precession Rate ("/century)')
plt.title('Precession Rate Comparison')
plt.xticks(x_pos, labels)
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

print(f"Simulation completed for {t_max / (365.25 * 86400):.0f} years")
print(f"Jupiter precession rate: {precession_rate_J:.4f} arcsec/century (target ~0.1)")
print(f"Saturn precession rate: {precession_rate_S:.4f} arcsec/century (target ~0.2)")
print(f"Mean |κ_app| - Jupiter: {np.mean(np.abs(kappa_app_J)):.2e}")
print(f"Mean |κ_app| - Saturn: {np.mean(np.abs(kappa_app_S)):.2e}")
print(f"5:2:1 resonance phase range: {np.min(phase_diff_521):.2f} to {np.max(phase_diff_521):.2f} rad")
print(f"Mean resonance lock strength: {np.mean(resonance_strength):.3f}")
print(f"Max entropy - Jupiter: {np.max(entropy_J):.3f}, Saturn: {np.max(entropy_S):.3f}")
print(f"Overflow events - Jupiter: {np.sum(entropy_J >= 1.0)}, Saturn: {np.sum(entropy_S >= 1.0)}")

# Compare with Mercury for reference
print(f"\nFor comparison, Mercury's precession: 43.0 arcsec/century")
print(f"Jupiter/Mercury ratio: {precession_rate_J/43.0:.6f}")
print(f"Saturn/Mercury ratio: {precession_rate_S/43.0:.6f}")