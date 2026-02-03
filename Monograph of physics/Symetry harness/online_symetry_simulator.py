import numpy as np
import pandas as pd

class EmissionGovernor:
    def __init__(self, B=[1,1,1], sigma=[1,1,1], Kcap=10, gamma=0.1, lambda_=1, epsilon=1,
                 delta_C=0.1, delta_S=0.1, k=10, soft_edge=False):
        self.R = np.zeros(3)  # Spatial registers (accumulate deltas)
        self.B = np.array(B)  # Budgets
        self.sigma = np.array(sigma)  # Symmetry gate
        self.L = 0.0  # Load
        self.Kcap = Kcap  # Capacity
        self.C = 0.5  # Coherence
        self.S = 0.0  # Entropy
        self.gamma = gamma  # Damping
        self.lambda_ = lambda_  # Drain factor
        self.epsilon = epsilon  # Emit energy
        self.delta_C = delta_C  # Coherence boost
        self.delta_S = delta_S  # Entropy reduction
        self.k = k  # Soft-edge steepness
        self.soft_edge = soft_edge
        self.emits = 0  # Total emits

    def kick(self, delta_R):
        # Apply symmetry
        delta_R = self.sigma * delta_R
        # Compute delta_L
        delta_L = np.sum(np.abs(self.B * delta_R))
        # Update L with damping
        self.L = (1 - self.gamma) * self.L + delta_L
        # Accumulate R
        self.R += delta_R
        # Check emission
        rho = self.L / self.Kcap
        emitted_this_tick = False
        while rho >= 1 and not emitted_this_tick:
            if self.soft_edge:
                p_emit = 1 / (1 + np.exp(-self.k * (rho - 1)))
                if np.random.rand() > p_emit:
                    break
            # Emit
            self.L = max(0, self.L - self.lambda_ * self.epsilon)
            self.C = min(1, self.C + self.delta_C)
            self.S = max(0, self.S - self.delta_S)
            self.emits += 1
            rho = self.L / self.Kcap
            emitted_this_tick = True if self.soft_edge else False  # Soft: at most once

    def reset(self):
        self.R = np.zeros(3)
        self.L = 0.0
        self.C = 0.5
        self.S = 0.0
        self.emits = 0

def normalize(u):
    return u / np.linalg.norm(u)

# Directions (normalized)
axes = [normalize(np.array(d)) for d in [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]]
faces = [normalize(np.array(d)) for d in [(1,1,0), (1,-1,0), (-1,1,0), (-1,-1,0),
                                          (1,0,1), (1,0,-1), (-1,0,1), (-1,0,-1),
                                          (0,1,1), (0,1,-1), (0,-1,1), (0,-1,-1)]]
bodies = [normalize(np.array(d)) for d in [(1,1,1), (1,1,-1), (1,-1,1), (1,-1,-1),
                                           (-1,1,1), (-1,1,-1), (-1,-1,1), (-1,-1,-1)]]

direction_classes = {'axes': axes, 'faces': faces, 'bodies': bodies}

def simulate_direction(gov, u, step=10.0, N_ticks=1000):
    gov.reset()
    max_L = 0.0
    for t in range(N_ticks):
        delta_R = step * u
        gov.kick(delta_R)
        max_L = max(max_L, gov.L)  # Track peak after update but before potential emit
    total_distance = N_ticks * step
    emit_rate = gov.emits / N_ticks
    slowness = emit_rate / step  # Normalized to emits per unit distance
    v = 1 / slowness if slowness > 0 else np.inf
    avg_C = gov.C  # Final C (approaches 1 after emissions)
    avg_S = gov.S  # Final S (approaches 0 after emissions)
    return {'slowness': slowness, 'v': v, 'emit_rate': emit_rate,
            'peak_L': max_L, 'avg_C': avg_C, 'avg_S': avg_S}

def test_symmetry(B=[1,1,1], epsilon_tol=0.05):
    gov = EmissionGovernor(B=B)
    results = []
    for class_name, directions in direction_classes.items():
        for i, u in enumerate(directions):
            stats = simulate_direction(gov, u)
            results.append({'class': class_name, 'dir_idx': i, 'u': tuple(u), **stats})  # Use tuple for comparison
    
    df = pd.DataFrame(results)
    print(df[['class', 'dir_idx', 'slowness', 'v', 'emit_rate', 'avg_C', 'avg_S']])
    
    # Parity check: for each u, find -u, check rel diff < tol
    parity_pass = True
    for i in range(len(df)):
        u = np.array(df.loc[i, 'u'])
        neg_u = tuple(-u)
        neg_u_idx = df.index[df['u'] == neg_u].tolist()
        if neg_u_idx:
            for key in ['slowness', 'emit_rate', 'avg_C', 'avg_S']:
                val = df.loc[i, key]
                neg_val = df.loc[neg_u_idx[0], key]
                rel_diff = abs(val - neg_val) / (0.5 * (val + neg_val + 1e-10))
                if rel_diff > epsilon_tol:
                    parity_pass = False
                    print(f"Parity fail: {key} for u={u}, rel_diff={rel_diff:.3f}")
    
    # Permutation symmetry: std within class < tol * mean
    cubic_pass = True
    for class_name in direction_classes:
        class_df = df[df['class'] == class_name]
        for key in ['slowness', 'emit_rate']:
            mean = class_df[key].mean()
            std = class_df[key].std()
            if std > epsilon_tol * mean:
                cubic_pass = False
                print(f"Cubic fail: {class_name} {key}, std/mean={std/mean:.3f}")
    
    print(f"Parity symmetry: {'PASS' if parity_pass else 'FAIL'}")
    print(f"Cubic symmetry: {'PASS' if cubic_pass else 'FAIL'}")
    
    # L1 predictions (from axis measurements)
    axis_slownesses = df[df['class'] == 'axes']['slowness'].values[:3]  # Positive axes
    s_x, s_y, s_z = axis_slownesses
    pred_s_face = (s_x + s_y) / np.sqrt(2)
    pred_v_face = np.sqrt(2) / (s_x + s_y) if (s_x + s_y) > 0 else np.inf
    pred_s_body = (s_x + s_y + s_z) / np.sqrt(3)
    pred_v_body = np.sqrt(3) / (s_x + s_y + s_z) if (s_x + s_y + s_z) > 0 else np.inf
    print(f"L1 Prediction - Face diagonal slowness: {pred_s_face:.3f}, v: {pred_v_face:.3f}")
    print(f"L1 Prediction - Body diagonal slowness: {pred_s_body:.3f}, v: {pred_v_body:.3f}")

# Run the test
test_symmetry(B=[1,1,1])  # Symmetric case
# test_symmetry(B=[1,1.5,2])  # Uncomment to break symmetry and test failures