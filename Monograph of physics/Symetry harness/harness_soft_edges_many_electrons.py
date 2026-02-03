import numpy as np
import pandas as pd

class EmissionGovernor:
    def __init__(self, B=[1,1,1], sigma=[1,1,1], Kcap=10, gamma=0.1, lambda_=1, epsilon=1,
                 delta_C=0.1, delta_S=0.1, k=1000, soft_edge=False, f=1.0, lambda_gate=1.0, c=1.0, N=1, scheme='DR'):
        """Initialize the emission governor with register states and parameters."""
        self.R = np.zeros(3)  # Spatial registers for tracking deltas
        self.B = np.array(B)  # Budgets for each axis
        self.sigma = np.array(sigma)  # Symmetry gate flags
        self.L = 0.0  # Load accumulator
        self.Kcap = Kcap * N if scheme == 'DR' else Kcap  # Capacity, scaled for DR
        self.C = 0.5  # Coherence level
        self.S = 0.0  # Entropy level
        self.gamma = gamma  # Damping factor
        self.lambda_ = lambda_  # Emission drain factor
        self.epsilon = epsilon  # Energy per emission
        self.delta_C = delta_C  # Coherence boost per emission
        self.delta_S = delta_S  # Entropy reduction per emission
        self.k = k  # Steepness for soft-edge (high for sharp threshold)
        self.soft_edge = soft_edge  # Default to False for deterministic emissions
        self.emits = 0  # Total emission count
        self.f = f  # Gate frequency
        self.lambda_gate = lambda_gate  # Gate width
        self.vg = f * lambda_gate  # Gate-speed invariant
        self.c = c  # Speed limit
        self.N = N  # Number of electrons
        self.scheme = scheme  # Allocation scheme: 'DR', 'PE', 'HR'
        self.emit_history = []  # Track emissions per tick

    def kick(self, delta_R):
        """Apply a kick to the registers, handle emissions, and enforce gate cone."""
        if self.vg > self.c:
            delta_R *= self.c / self.vg  # Scale if beyond speed limit
        delta_R = self.sigma * delta_R  # Apply symmetry
        delta_L = np.sum(np.abs(self.B * delta_R))  # Base load increase
        if self.scheme == 'DR':
            delta_L *= self.N  # Linear cost for Distributed Registers
        elif self.scheme == 'PE':
            W_N = self.N + 10 * self.N**2 + 47 * self.N**3  # Cost hierarchy
            delta_L *= W_N / self.N  # Average cost per electron
        if self.N > 1:
            collision_prob = min(1, self.N**2 / (2 * 1e6))  # Rough Pauli penalty
            if np.random.rand() < collision_prob:
                delta_L += 5  # Simplified penalty
        self.L = (1 - self.gamma) * self.L + delta_L  # Update load with damping
        self.R += delta_R  # Accumulate register changes
        rho = self.L / self.Kcap  # Fill ratio
        emits_this_tick = 0
        while rho >= 1:
            if self.soft_edge:
                p_emit = 1 / (1 + np.exp(-self.k * (rho - 1)))  # Soft-edge probability
                if np.random.rand() > p_emit:
                    break
            self.L = max(0, self.L - self.lambda_ * self.epsilon)  # Emit energy
            self.C = min(1, self.C + self.delta_C)  # Boost coherence
            self.S = max(0, self.S - self.delta_S)  # Reduce entropy
            self.emits += 1
            emits_this_tick += 1
            rho = self.L / self.Kcap
        self.emit_history.append(emits_this_tick)

    def reset(self):
        """Reset all dynamic state variables."""
        self.R = np.zeros(3)
        self.L = 0.0
        self.C = 0.5
        self.S = 0.0
        self.emits = 0
        self.emit_history = []

def normalize(u):
    """Normalize a direction vector."""
    return u / np.linalg.norm(u)

# Define normalized direction sets
axes = [normalize(np.array(d)) for d in [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]]
faces = [normalize(np.array(d)) for d in [(1,1,0), (1,-1,0), (-1,1,0), (-1,-1,0),
                                          (1,0,1), (1,0,-1), (-1,0,1), (-1,0,-1),
                                          (0,1,1), (0,1,-1), (0,-1,1), (0,-1,-1)]]
bodies = [normalize(np.array(d)) for d in [(1,1,1), (1,1,-1), (1,-1,1), (1,-1,-1),
                                           (-1,1,1), (-1,1,-1), (-1,-1,1), (-1,-1,-1)]]

direction_classes = {'axes': axes, 'faces': faces, 'bodies': bodies}

def simulate_direction(gov, u, step=10.0, N_ticks=1000):
    """Simulate movement in a given direction and return statistics."""
    gov.reset()
    for t in range(N_ticks):
        delta_R = step * u
        gov.kick(delta_R)
    total_distance = N_ticks * step
    emit_rate = np.mean(gov.emit_history)  # Average emissions per tick
    slowness = emit_rate / step  # Emissions per unit distance
    v = 1 / slowness if slowness > 0 else np.inf
    avg_C = gov.C
    avg_S = gov.S
    return {'slowness': slowness, 'v': v, 'emit_rate': emit_rate,
            'peak_L': max(gov.emit_history) * gov.epsilon * gov.lambda_, 'avg_C': avg_C, 'avg_S': avg_S, 'vg': gov.vg}

def test_symmetry(B=[1,1,1], epsilon_tol=0.05, N=1, scheme='DR'):
    """Test symmetry properties across all direction classes."""
    gov = EmissionGovernor(B=B, N=N, scheme=scheme)
    results = []
    for class_name, directions in direction_classes.items():
        for i, u in enumerate(directions):
            stats = simulate_direction(gov, u)
            results.append({'class': class_name, 'dir_idx': i, 'u': tuple(u), **stats})
    
    df = pd.DataFrame(results)
    print(df[['class', 'dir_idx', 'slowness', 'v', 'emit_rate', 'avg_C', 'avg_S']])
    
    # Check parity symmetry
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
    
    # Check cubic symmetry
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
    
    # L1 predictions with offset correction
    axis_slownesses = df[df['class'] == 'axes']['slowness'].values[:3]
    s_x, s_y, s_z = axis_slownesses
    offset = 1 - np.mean(axis_slownesses)  # Offset from bare axis cost
    pred_s_face = np.sqrt(2) - offset
    pred_v_face = 1 / pred_s_face if pred_s_face > 0 else np.inf
    pred_s_body = np.sqrt(3) - offset
    pred_v_body = 1 / pred_s_body if pred_s_body > 0 else np.inf
    print(f"L1 Prediction (with offset correction) - Face diagonal slowness: {pred_s_face:.3f}, v: {pred_v_face:.3f}")
    print(f"L1 Prediction (with offset correction) - Body diagonal slowness: {pred_s_body:.3f}, v: {pred_v_body:.3f}")

# Run the test
test_symmetry(B=[1,1,1], N=1, scheme='DR')  # Single electron test
# Test with many electrons: test_symmetry(N=2, scheme='PE')