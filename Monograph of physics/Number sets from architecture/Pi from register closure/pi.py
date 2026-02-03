# pi.py
# Register-closure π without trig: rational half-angle composition vs Chudnovsky
# Outputs a CSV and a log-error plot, and prints a summary table.

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpmath import mp

# ---------------- Rational rotation via half-angle ----------------
# Parameter t = tan(theta/2). Single-step rotation has:
#   c = (1 - t^2)/(1 + t^2),  s = 2t/(1 + t^2)
# Compose N steps by exponentiation in the (c,s) algebra (no trig).

def rot_from_t(t):
    t = mp.mpf(t)
    den = 1 + t*t
    c = (1 - t*t) / den
    s = (2 * t) / den
    return (c, s)

def rot_mul(r1, r2):
    c1, s1 = r1; c2, s2 = r2
    return (c1*c2 - s1*s2, s1*c2 + c1*s2)

def rot_pow(r, N):
    # fast exponentiation of rotation (c,s)^N
    c, s = r
    rc, rs = mp.mpf(1), mp.mpf(0)
    bc, bs = c, s
    n = int(N)
    while n > 0:
        if n & 1:
            rc, rs = rot_mul((rc, rs), (bc, bs))
        bc, bs = (bc*bc - bs*bs, 2*bc*bs)
        n >>= 1
    return (rc, rs)

def sN_of_t(t, N):
    c, s = rot_from_t(t)
    cN, sN = rot_pow((c, s), N)
    return sN  # this is sin(N*theta), computed without trig

def find_first_zero_t(N, tmax=mp.mpf('1.5'), max_iter=500000):
    """
    Find the smallest t>0 such that sN_of_t(t,N)=0 and cos(N*theta)>0 (i.e., N*theta ≈ 2π).
    Pure sign-scan + bisection; no trig is used.
    """
    # Heuristic: first zero is near t ≈ tan(pi/N) ~ π/N; step ~ const/N
    step = max(mp.mpf('1e-6'), mp.mpf('0.3')/N)
    t_prev = mp.mpf('1e-16')
    s_prev = sN_of_t(t_prev, N)
    t = t_prev + step
    it = 0
    while t <= tmax and it < max_iter:
        s = sN_of_t(t, N)
        if s_prev == 0:
            pass
        elif s_prev * s < 0:
            # bracket [t-step, t]
            lo, hi = t - step, t
            for _ in range(140):
                mid = (lo + hi)/2
                sm = sN_of_t(mid, N)
                if sm == 0:
                    lo = hi = mid
                    break
                if s_prev * sm < 0:
                    hi = mid
                else:
                    lo = mid; s_prev = sm
            cand = (lo + hi)/2
            # require cos(N*theta) > 0 (select 2π branch, not π)
            c1, s1 = rot_from_t(cand)
            cN, sN = rot_pow((c1, s1), N)
            if cN > 0:
                return cand
        t_prev, s_prev = t, s
        t += step
        it += 1
    return None

def pi_from_register_closure(N, dps=120):
    mp.dps = dps + 20
    t = find_first_zero_t(N)
    if t is None:
        return None, None
    # Inscribed polygon perimeter in unit circle: N * 2*sin(theta/2) = N * 2t/sqrt(1+t^2)
    # This gives circumference → 2π, so divide by 2 to get π
    perimeter = N * (2 * t / mp.sqrt(1 + t*t))
    pi_hat = perimeter / 2
    return +pi_hat, +t

# ---------------- Chudnovsky reference (no built-in π) ----------------
def pi_chudnovsky(dps=200):
    mp.dps = dps + 20
    def bs(a, b):
        if b - a == 1:
            k = mp.mpf(a)
            Pab = mp.mpf(1)
            Qab = mp.mpf(1)
            if a == 0:
                Pab = Qab = mp.mpf(1)
            else:
                Pab = (6*k-5)*(2*k-1)*(6*k-1)
                Qab = k*k*k*mp.mpf(10939058860032000)
            Tab = Pab * (13591409 + 545140134*k)
            if a & 1:
                Tab = -Tab
            return (Pab, Qab, Tab)
        else:
            m = (a + b) // 2
            Pam, Qam, Ram = bs(a, m)
            Pmb, Qmb, Rmb = bs(m, b)
            Pab = Pam * Pmb
            Qab = Qam * Qmb
            Rab = Qmb * Ram + Pam * Rmb
            return (Pab, Qab, Rab)
    
    terms = max(1, (dps // 14) + 10)
    P1n, Q1n, R1n = bs(0, terms)
    sqrtC = mp.sqrt(mp.mpf(10005))
    return (426880 * sqrtC * Q1n) / R1n

# ---------------- CLI & report ----------------
def main():
    ap = argparse.ArgumentParser(description="Register-closure π (no trig) vs Chudnovsky")
    ap.add_argument("--dps", type=int, default=120, help="working digits")
    ap.add_argument("--Ns", type=str, default="6,8,12,16,24,32,48,64,96,128,256,512,1024",
                    help="comma-separated N for closure")
    args = ap.parse_args()

    mp.dps = args.dps
    Ns = [int(x) for x in args.Ns.split(",")]

    # Reference π from Chudnovsky (no built-in π)
    pi_ref = pi_chudnovsky(dps=args.dps)

    rows = []
    for N in Ns:
        pi_hat, t = pi_from_register_closure(N, dps=args.dps)
        if pi_hat is None:
            rows.append((N, None, None, None, None))
        else:
            err = abs(pi_hat - pi_ref)
            digits = 0 if err == 0 else max(0, int(-mp.log10(err)))
            rows.append((N, str(pi_hat), str(t), str(err), digits))

    df = pd.DataFrame(rows, columns=["N", "pi_hat_register", "t_param", "abs_error_vs_chudnovsky", "digits_correct"])
    out_csv = Path("pi_register_closure_sweep.csv")
    df.to_csv(out_csv, index=False)

    # Plot error vs N (log scale)
    mask = df["abs_error_vs_chudnovsky"].notna()
    if mask.sum() > 0:
        Ns_plot = [int(n) for n in df.loc[mask, "N"]]
        err_plot = [float(e) for e in df.loc[mask, "abs_error_vs_chudnovsky"]]
        
        plt.figure(figsize=(6.4, 3.2))
        plt.plot(Ns_plot, np.log10(np.maximum(err_plot, 1e-999)), marker='o', linewidth=1.0)
        plt.xlabel("closure order N")
        plt.ylabel("log10 |π̂ − π_ref|")
        plt.title("Register-closure π (rational half-angle) vs Chudnovsky")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        out_png = Path("pi_register_closure_error.png")
        plt.savefig(out_png, dpi=150)
        print(f"Saved plot    : {out_png.resolve()}")
    else:
        print("No valid data points for plotting")

    print("Chudnovsky π  :", pi_ref)
    print(f"Saved table   : {out_csv.resolve()}")
    print("\nRegister-closure sweep:")
    print(df.to_string(index=False))

if __name__ == "__main__":
    main()
