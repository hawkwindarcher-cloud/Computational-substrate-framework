import numpy as np
import matplotlib.pyplot as plt

# Constants
G = 6.67430e-11  # Gravitational constant (m^3 kg^-1 s^-2)
AU = 1.496e11    # Astronomical Unit (m)
M_Sun = 1.989e30 # Solar mass (kg)
M_J = 1.898e27   # Jupiter mass (kg)
M_S = 5.683e26   # Saturn mass (kg)
a_J = 5.2 * AU   # Jupiter semi-major axis (m)
a_S = 9.5 * AU   # Saturn semi-major axis (m)
P_J = 11.86 * 365.25 * 86400  # Jupiter period (s)
P_S = 29.46 * 365.25 * 86400  # Saturn period (s)
K = 1e6          # Capacity constraint (arbitrary, per paper)
dt = 86400 * 30  # Time step (30 days in s) - larger for stability
t_max = 1000 * 365.25 * 86400  # 1000 years (s) - shorter for testing
n_steps = int(t_max / dt)     # Number of steps

print(f"Running simulation for {t_max / (365.25 * 86400):.0f} years with {n_steps} steps")

# Initial conditions (approximate, from JPL Horizons)
theta_J = 0.0    # Initial phase (radians)
theta_S = 0.0    # Initial phase (radians)
r_J = a_J        # Initial radius (m)
r_S = a_S        # Initial radius (m)
e_J = 0.048      # Eccentricity
e_S = 0.056      # Eccentricity

# Angular velocities (mean motion)
n_J = 2 * np.pi / P_J  # Jupiter mean motion
n_S = 2 * np.pi / P_S  # Saturn mean motion

# Arrays to store data
time = np.zeros(n_steps)
theta_J_arr = np.zeros(n_steps)
theta_S_arr = np.zeros(n_steps)
r_J_arr = np.zeros(n_steps)
r_S_arr = np.zeros(n_steps)
entropy_J = np.zeros(n_steps)
entropy_S = np.zeros(n_steps)

# Quantization delay factors (approximate, per paper eq. 5)
kappa_app_J = 1e-12  # Reduced delay gradient for Jupiter
kappa_app_S = 1.2e-12 # Reduced delay gradient for Saturn
Omega_N_J = n_J  # Newtonian angular frequency
Omega_N_S = n_S  # Newtonian angular frequency

# Simulation loop
for i in range(n_steps):
    time[i] = i * dt
    
    # Calculate separation
    separation = abs(r_S - r_J)
    
    # Newtonian gravitational acceleration (simplified)
    # Sun's gravitational acceleration
    acc_J_sun = -G * M_Sun / r_J**2
    acc_S_sun = -G * M_Sun / r_S**2
    
    # Mutual gravitational acceleration (when close enough to matter)
    if separation > 0 and separation < 10 * AU:  # Only when reasonably close
        acc_J_mut = G * M_S / separation**2 * np.sign(r_S - r_J)
        acc_S_mut = G * M_J / separation**2 * np.sign(r_J - r_S)
    else:
        acc_J_mut = 0
        acc_S_mut = 0
    
    # Total accelerations
    acc_J = acc_J_sun + acc_J_mut
    acc_S = acc_S_sun + acc_S_mut
    
    # Phase updates with Keplerian motion plus delay corrections
    delta_theta_J = n_J * dt + kappa_app_J * abs(acc_J) * dt
    delta_theta_S = n_S * dt + kappa_app_S * abs(acc_S) * dt
    
    # Radius updates (small perturbations around semi-major axis)
    r_J = a_J * (1 + e_J * np.cos(theta_J))
    r_S = a_S * (1 + e_S * np.cos(theta_S))
    
    # Update phases
    theta_J += delta_theta_J
    theta_S += delta_theta_S
    
    # Keep angles in [0, 2π] for cleaner plots
    theta_J = theta_J % (2 * np.pi)
    theta_S = theta_S % (2 * np.pi)
    
    # Entropy load (simplified as function of acceleration magnitude)
    entropy_J[i] = abs(acc_J) * dt / K
    entropy_S[i] = abs(acc_S) * dt / K
    
    # Virtual drag from overflow (simplified)
    if entropy_J[i] > 1.0:
        theta_J -= kappa_app_J * (entropy_J[i] - 1.0) * dt * 0.1
    if entropy_S[i] > 1.0:
        theta_S -= kappa_app_S * (entropy_S[i] - 1.0) * dt * 0.1
    
    # Store values
    theta_J_arr[i] = theta_J
    theta_S_arr[i] = theta_S
    r_J_arr[i] = r_J
    r_S_arr[i] = r_S
    entropy_J[i] = min(entropy_J[i], 2.0)  # Cap entropy
    entropy_S[i] = min(entropy_S[i], 2.0)

# Calculate resonance phase difference
# For 5:2 resonance: 5*n_S ≈ 2*n_J, so we look at 5*theta_S - 2*theta_J
phase_diff = 5 * theta_S_arr - 2 * theta_J_arr

# Plotting
plt.figure(figsize=(15, 10))

plt.subplot(3, 2, 1)
plt.plot(time / (365.25 * 86400), theta_J_arr, 'b-', label='Jupiter', linewidth=0.8)
plt.plot(time / (365.25 * 86400), theta_S_arr, 'r-', label='Saturn', linewidth=0.8)
plt.xlabel('Time (years)')
plt.ylabel('Phase (radians)')
plt.title('Orbital Phases')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(3, 2, 2)
plt.plot(time / (365.25 * 86400), phase_diff, 'g-', linewidth=0.8)
plt.xlabel('Time (years)')
plt.ylabel('5θ_S - 2θ_J (radians)')
plt.title('5:2 Resonance Phase Difference')
plt.grid(True, alpha=0.3)

plt.subplot(3, 2, 3)
plt.plot(time / (365.25 * 86400), r_J_arr / AU, 'b-', label='Jupiter', linewidth=0.8)
plt.plot(time / (365.25 * 86400), r_S_arr / AU, 'r-', label='Saturn', linewidth=0.8)
plt.xlabel('Time (years)')
plt.ylabel('Distance from Sun (AU)')
plt.title('Orbital Radii')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(3, 2, 4)
plt.plot(time / (365.25 * 86400), entropy_J, 'b-', label='Jupiter', linewidth=0.8)
plt.plot(time / (365.25 * 86400), entropy_S, 'r-', label='Saturn', linewidth=0.8)
plt.xlabel('Time (years)')
plt.ylabel('Normalized Entropy')
plt.title('Entropy Load')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(3, 2, 5)
# Orbital plot (x-y coordinates)
x_J = r_J_arr * np.cos(theta_J_arr)
y_J = r_J_arr * np.sin(theta_J_arr)
x_S = r_S_arr * np.cos(theta_S_arr)
y_S = r_S_arr * np.sin(theta_S_arr)

plt.plot(x_J / AU, y_J / AU, 'b-', alpha=0.7, linewidth=0.5, label='Jupiter')
plt.plot(x_S / AU, y_S / AU, 'r-', alpha=0.7, linewidth=0.5, label='Saturn')
plt.plot(0, 0, 'yo', markersize=8, label='Sun')
plt.xlabel('X (AU)')
plt.ylabel('Y (AU)')
plt.title('Orbital Paths')
plt.axis('equal')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(3, 2, 6)
# Frequency analysis - approximate periods
if n_steps > 100:
    # Calculate approximate current periods from phase derivatives
    period_J_apparent = 2 * np.pi / np.mean(np.diff(theta_J_arr[-100:]) / dt) / (365.25 * 86400)
    period_S_apparent = 2 * np.pi / np.mean(np.diff(theta_S_arr[-100:]) / dt) / (365.25 * 86400)
    
    plt.bar(['Jupiter (actual)', 'Jupiter (sim)', 'Saturn (actual)', 'Saturn (sim)'], 
            [P_J/(365.25 * 86400), period_J_apparent, P_S/(365.25 * 86400), period_S_apparent],
            color=['blue', 'lightblue', 'red', 'pink'])
    plt.ylabel('Period (years)')
    plt.title('Orbital Periods Comparison')
    plt.xticks(rotation=45)

plt.tight_layout()
plt.show()

print(f"Simulation completed for {t_max / (365.25 * 86400):.0f} years.")
print(f"Final Jupiter phase: {theta_J_arr[-1]:.3f} rad")
print(f"Final Saturn phase: {theta_S_arr[-1]:.3f} rad")
print(f"Mean entropy - Jupiter: {np.mean(entropy_J):.2e}, Saturn: {np.mean(entropy_S):.2e}")
print(f"Phase difference range: {np.min(phase_diff):.3f} to {np.max(phase_diff):.3f} rad")