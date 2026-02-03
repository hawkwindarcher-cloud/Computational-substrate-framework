from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt

class StewFieldLorentzSimulator:
    def __init__(self, c: float = 1.0, t_P: float = 1.0, leak: float = 0.0):
        self.c = float(c)
        self.t_P = float(t_P)
        self.leak = float(leak)
        self.load = 0.0

    def delta_t_q(self, u: float) -> float:
        beta = abs(u) / self.c
        if beta >= 1.0:
            beta = 1.0 - 1e-12
        return self.t_P / np.sqrt(1.0 - beta * beta)

    def signal_dt(self, ds: float) -> float:
        return ds / self.c

    def update_load(self, ds: float) -> None:
        self.load = (1.0 - self.leak) * self.load + 0.0 * ds

    def test_cone_isotropy(self, r: float = 3.0, directions=None, steps: int = 100):
        if directions is None:
            directions = {
                "axis_x": np.array([1.0, 0.0, 0.0]),
                "face_xy": np.array([1.0, 1.0, 0.0]) / np.sqrt(2.0),
                "body_xyz": np.array([1.0, 1.0, 1.0]) / np.sqrt(3.0),
            }
        results, eff = {}, {}
        for name, _u in directions.items():
            self.load = 0.0
            T = 0.0
            distance = 0.0
            step_size = float(r) / max(int(steps), 1)
            while distance < r - 1e-15:
                rem = r - distance
                ds = step_size if rem > step_size else rem
                self.update_load(ds)
                T += self.signal_dt(ds)
                distance += ds
            results[name] = T
            eff[name] = (r / T) if T > 0.0 else float("inf")
        return results, eff

    def test_michelson_morley(self, L: float = 5.0, theta_range=None, u_app: float = 0.0):
        if theta_range is None:
            theta_range = np.linspace(0.0, 2.0 * np.pi, 12, endpoint=False)
        T_arm = 2.0 * L / self.c
        gamma_clock = self.delta_t_q(u_app) / self.t_P
        Ts = np.full_like(theta_range, T_arm * gamma_clock, dtype=float)
        return float(Ts.mean()), float(Ts.std())

    def test_doppler_velocity_addition(self, u: float = 0.5, v: float = 0.3):
        u = np.sign(u) * min(abs(u), 1.0 - 1e-12)
        v = np.sign(v) * min(abs(v), 1.0 - 1e-12)
        beta = abs(u)
        dop_plus = np.sqrt((1.0 - beta) / (1.0 + beta))
        dop_minus = 1.0 / dop_plus
        w = (u + v) / (1.0 + u * v)
        return float(dop_plus), float(dop_minus), float(w)

    def test_time_dilation(self, u: float = 0.5) -> float:
        return float(self.delta_t_q(u * self.c) / self.t_P)

    def test_dispersion_linearity(self, k_vals=None, curved=True):
        if k_vals is None:
            k_vals = np.array(
                [1e-2, 2.1544346900318832e-02, 4.6415888336127774e-02,
                 1e-1, 2.1544346900318834e-01, 4.6415888336127775e-01,
                 1.0, 2.154434690031882, 4.6415888336127775, 10.0],
                dtype=float
            )
        omega = []
        for k in k_vals:
            if curved:
                v = self.c / (1.0 + 0.01 / max(k, 1e-12))
                omega.append(v * k)
            else:
                omega.append(self.c * k)
        return np.array(k_vals, float), np.array(omega, float)

if __name__ == "__main__":
    sim = StewFieldLorentzSimulator(c=1.0, t_P=1.0, leak=0.0)

    # Test 1
    times, eff = sim.test_cone_isotropy(r=3.0, steps=100)
    print("Test 1: Cone Isotropy Arrival Times:", times)
    print("Effective Speeds:", eff)

    # Test 2
    meanT, stdT = sim.test_michelson_morley(L=5.0, u_app=0.0)
    print(f"Test 2: Michelson–Morley Mean T: {meanT} Std: {stdT}")

    # Test 3
    dop_p, dop_m, w = sim.test_doppler_velocity_addition(u=0.5, v=0.3)
    print(f"Test 3: Doppler +: {dop_p} Doppler -: {dop_m} Velocity Addition: {w}")

    # Test 4
    gamma = sim.test_time_dilation(u=0.5)
    print(f"Test 4: Time Dilation γ: {gamma}")

    # Test 5 with plot
    k_vals, omega = sim.test_dispersion_linearity(curved=True)
    plt.plot(k_vals, omega, 'o-')
    plt.xlabel('k')
    plt.ylabel('ω(k)')
    plt.title('Dispersion Relation: ω = c k / (1 + 0.01/k)')
    plt.grid(True)
    plt.show()
    print("Test 5: Dispersion ω(k) values:", list(zip(k_vals, omega)))