# stew_teeth.py
# The "version with teeth": fixed-point truncation lives INSIDE the leapfrog state,
# so rounding perturbs the trajectory itself. A float leapfrog runs alongside as the
# control. We then ask of the *mechanical* energy:
#   - is the non-conservation SECULAR (directed leak -> arrow of time) or DIFFUSIVE (noise)?
#   - how does it scale with register precision (frac_bits)?
#   - does it depend on whether the substrate rounds symmetrically or with bias?
# Yardstick: Planck power c^5/G.

import numpy as np, math

# ---- constants ----
G = 6.67430e-11
c = 299792458.0
M_sun = 1.98847e30
PLANCK_POWER = c**5 / G            # ~3.63e52 W, the natural luminosity scale

# ---- Paczynski-Wiita (dynamics only; redshift is a separate object, not used here) ----
def phi_pw(M, r):
    rs = 2*G*M/c**2
    return -G*M / (r - rs)

def accel_pw(M, r_vec):
    r = np.linalg.norm(r_vec)
    rs = 2*G*M/c**2
    a_mag = G*M / (r - rs)**2      # |dPhi/dr|
    return -a_mag * (r_vec / r)

def energy(M, pos, vel, m=1.0):
    return 0.5*m*np.dot(vel, vel) + m*phi_pw(M, np.linalg.norm(pos))

def v_circ_pw(M, r):
    rs = 2*G*M/c**2
    return math.sqrt(G*M*r/(r-rs)**2)

# ---- fixed-point grid (the substrate) ----
def quantize(x, SCALE, mode):
    # x: scalar or array. Returns value snapped to the register grid.
    s = x * SCALE
    if mode == "nearest":          # unbiased round-to-nearest (your to_reg convention)
        q = np.floor(s + 0.5)
    elif mode == "truncate":       # biased: drop low bits toward zero (real fixed-point truncation)
        q = np.trunc(s)
    else:
        raise ValueError(mode)
    return q / SCALE

# ---- one leapfrog step; if SCALE is not None the state is snapped to the grid ----
def leap_step(M, pos, vel, dt, SCALE=None, mode="nearest"):
    acc = accel_pw(M, pos)
    vel_h = vel + 0.5*dt*acc
    pos_n = pos + dt*vel_h
    acc_n = accel_pw(M, pos_n)
    vel_n = vel_h + 0.5*dt*acc_n
    if SCALE is not None:
        # truncation ENTERS the dynamics: the only state the universe keeps is on-grid
        pos_n = quantize(pos_n, SCALE, mode)
        vel_n = quantize(vel_n, SCALE, mode)
    return pos_n, vel_n

def run(M, a_factor=3.0, steps_per_orbit=200, norbits=300,
        frac_bits=None, mode="nearest", m_test=1.0):
    rs = 2*G*M/c**2
    a = a_factor*rs
    pos0 = np.array([a, 0.0, 0.0])
    vel0 = np.array([0.0, v_circ_pw(M, a), 0.0])
    P = 2*math.pi*a/np.linalg.norm(vel0)
    dt = P/steps_per_orbit
    nsteps = steps_per_orbit*norbits
    SCALE = (1 << frac_bits) if frac_bits is not None else None

    pos = quantize(pos0, SCALE, mode) if SCALE else pos0.copy()
    vel = quantize(vel0, SCALE, mode) if SCALE else vel0.copy()
    E0 = energy(M, pos, vel, m_test)

    t = np.empty(nsteps); dE = np.empty(nsteps)
    snap_events = 0; cum_abs_corr = 0.0     # honest, connected diagnostics
    for i in range(nsteps):
        if SCALE:
            pre_pos = pos + dt*(vel + 0.5*dt*accel_pw(M, pos))  # pre-snap drift, for correction size
        pos, vel = leap_step(M, pos, vel, dt, SCALE, mode)
        if SCALE:
            corr = np.linalg.norm(pos - pre_pos)
            if corr > 0: snap_events += 1
            cum_abs_corr += corr
        t[i] = (i+1)*dt
        dE[i] = energy(M, pos, vel, m_test) - E0
    return dict(t=t, dE=dE, E0=E0, dt=dt, nsteps=nsteps, P=P, rs=rs, a=a,
                snap_events=snap_events, cum_abs_corr=cum_abs_corr, frac_bits=frac_bits, mode=mode)

def split_secular_diffusive(t, dE):
    # secular = slope of linear fit (W, since dE in J and t in s); diffusive = RMS about the fit
    A = np.vstack([t, np.ones_like(t)]).T
    slope, intercept = np.linalg.lstsq(A, dE, rcond=None)[0]
    resid = dE - (slope*t + intercept)
    return slope, float(np.sqrt(np.mean(resid**2)))

if __name__ == "__main__":
    M = 10.0*M_sun
    print(f"Planck power yardstick: {PLANCK_POWER:.3e} W\n")

    # --- control: pure float. We SUBTRACT this from every quantized run so the coherent
    #     leapfrog orbital ripple (shared by both) cancels, leaving only the substrate effect. ---
    ctrl = run(M, frac_bits=None)
    s_ctrl, rms_ctrl = split_secular_diffusive(ctrl['t'], ctrl['dE'])
    print(f"[float control] its own ripple rms={rms_ctrl:.2e} J, residual secular={s_ctrl:+.2e} W")
    print("  (subtracted out below; what remains is purely register-induced)\n")

    fracs = [8, 12, 16, 20, 24, 28]
    rows = {}
    for mode in ("nearest", "truncate"):
        print(f"=== mode = {mode} ===  (delta = quantized - float, paired)")
        rows[mode] = []
        for fb in fracs:
            r = run(M, frac_bits=fb, mode=mode)
            delta = r['dE'] - ctrl['dE']                     # paired difference: ripple cancels
            slope, rms = split_secular_diffusive(r['t'], delta)
            T = r['t'][-1]
            directed = abs(slope)*T
            # bound check: did quantization throw the particle off its orbit?
            lost = (abs(delta[-1]) > 0.5*abs(ctrl['E0']))
            verdict = "ORBIT LOST" if lost else ("SECULAR" if directed > 3*rms else "diffusive")
            rows[mode].append((fb, slope, rms, directed, verdict, r, delta))
            print(f"  fb={fb:2d}  secular={slope:+.3e} W  diff-rms={rms:.3e} J  "
                  f"|sec*T|={directed:.3e} J  -> {verdict}")
        print()

    # --- fit scaling laws: how do secular and diffusive amplitudes depend on LSB = 2^-fb ---
    def fit_exponent(fracs, vals):
        x = np.array(fracs, float); y = np.array(vals, float)
        good = y > 0
        if good.sum() < 2: return None
        # y ~ 2^(-k*fb) => log2(y) = -k*fb + const
        k, b = np.polyfit(x[good], np.log2(y[good]), 1)
        return -k  # exponent in units of "bits": y ∝ 2^(-exponent*fb)

    print("=== scaling with frac_bits (delta amplitude ∝ 2^(-k·fb); k≈1 linear, k≈2 quadratic) ===")
    for mode in ("nearest", "truncate"):
        # only fit where the orbit stayed bound
        good = [r for r in rows[mode] if r[4] != "ORBIT LOST"]
        fb_g = [r[0] for r in good]
        rms_vals = [r[2] for r in good]
        sec_vals = [abs(r[1]) for r in good]
        k_rms = fit_exponent(fb_g, rms_vals)
        k_sec = fit_exponent(fb_g, sec_vals)
        kr = f"{k_rms:.2f}" if k_rms is not None else "n/a"
        ks = f"{k_sec:.2f}" if k_sec is not None else "n/a"
        print(f"  {mode:8s}: diffusive k≈{kr}   |   secular k≈{ks}   (fit over fb={fb_g})")

    # --- plots ---
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(1, 3, figsize=(16, 4.6))

    # (1) paired difference in time at a representative precision
    rep_fb = 16
    for mode, col in (("nearest", "tab:blue"), ("truncate", "tab:red")):
        row = next(r for r in rows[mode] if r[0]==rep_fb)
        rr, delta = row[5], row[6]
        ax[0].plot(rr['t']/rr['P'], delta, lw=0.8, alpha=0.85, label=f'{mode} (fb={rep_fb})', color=col)
    ax[0].axhline(0, color='k', lw=0.6)
    ax[0].set_xlabel('orbits'); ax[0].set_ylabel(r'$\Delta E_{quant}-\Delta E_{float}$  [J]')
    ax[0].set_title('substrate-induced energy drift in time'); ax[0].legend(fontsize=8); ax[0].grid(alpha=0.3)

    # (2) diffusive amplitude of the paired difference vs frac_bits
    for mode, col in (("nearest","tab:blue"),("truncate","tab:red")):
        fb_g = [r[0] for r in rows[mode] if r[4]!="ORBIT LOST"]
        rv   = [r[2] for r in rows[mode] if r[4]!="ORBIT LOST"]
        ax[1].semilogy(fb_g, rv, 'o-', color=col, label=mode)
    ax[1].set_xlabel('frac_bits'); ax[1].set_ylabel('RMS of (quant - float) [J]')
    ax[1].set_title('diffusive amplitude vs precision'); ax[1].legend(fontsize=8); ax[1].grid(alpha=0.3, which='both')

    # (3) secular leak vs frac_bits as fraction of Planck power
    for mode, col in (("nearest","tab:blue"),("truncate","tab:red")):
        fb_g = [r[0] for r in rows[mode] if r[4]!="ORBIT LOST"]
        sv   = [abs(r[1])/PLANCK_POWER for r in rows[mode] if r[4]!="ORBIT LOST"]
        ax[2].semilogy(fb_g, sv, 's-', color=col, label=mode)
    ax[2].set_xlabel('frac_bits'); ax[2].set_ylabel(r'$|$secular leak$|\,/\,P_{Planck}$')
    ax[2].set_title('directed leak vs precision'); ax[2].legend(fontsize=8); ax[2].grid(alpha=0.3, which='both')

    plt.tight_layout()
    plt.savefig("/home/claude/stew_teeth.png", dpi=130)
    print("\nsaved /home/claude/stew_teeth.png")
