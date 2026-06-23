# stew_propertime.py
# Does a redshift profile EMERGE if the register updates are paced by PROPER time?
#
# Mechanism (not imposed-by-hand quantum dilation, but an update-cadence rule):
#   the substrate snaps the state to the grid stochastically, with per-step probability
#   p_snap(r) = alpha(r) = sqrt(1 - rs/r)   ->   update RATE tracks the local clock rate.
# Control: same grid, same dynamics, but p_snap = <alpha> (constant cadence in coordinate time).
#
# Between snaps the leapfrog runs in float with fine steps, so the ONLY error is truncation.
# We then ask:
#   (1) coordinate-time leak ratio proper/control  -> does it track alpha(r)?   (expected: yes, by rate)
#   (2) per-PROPER-time leak of the proper run      -> is it FLAT in r?          (the non-imposed claim)
#       per-proper-time leak of the control run     -> does it rise as 1/alpha?  (the foil)
#
# Dynamics: Paczynski-Wiita. Redshift factor alpha: exact Schwarzschild (separate object).

import numpy as np, math
G=6.67430e-11; c=299792458.0; M_sun=1.98847e30; PLANCK_POWER=c**5/G

def accel_pw(M,rv):
    r=np.linalg.norm(rv); rs=2*G*M/c**2
    return -(G*M/(r-rs)**2)*(rv/r)
def phi_pw(M,r):
    rs=2*G*M/c**2; return -G*M/(r-rs)
def energy(M,pos,vel,m=1.0):
    return 0.5*m*np.dot(vel,vel)+m*phi_pw(M,np.linalg.norm(pos))
def v_circ_pw(M,r):
    rs=2*G*M/c**2; return math.sqrt(G*M*r/(r-rs)**2)
def alpha_schw(M,r):
    rs=2*G*M/c**2; return math.sqrt(max(1.0-rs/r,1e-9))
def quant_trunc(x,SCALE):
    return np.trunc(x*SCALE)/SCALE
def leap(M,pos,vel,dt):
    a=accel_pw(M,pos); vh=vel+0.5*dt*a; pn=pos+dt*vh; an=accel_pw(M,pn)
    return pn, vh+0.5*dt*an

def mean_alpha(M,rp,k,steps_per_orbit,norbits):
    # quick float pass to get <alpha> along the orbit (for the control cadence)
    pos=np.array([rp,0.,0.]); vel=np.array([0.,k*v_circ_pw(M,rp),0.])
    P=2*math.pi*rp/np.linalg.norm(vel); dt=P/steps_per_orbit
    s=0.0; n=steps_per_orbit*norbits
    for _ in range(n):
        pos,vel=leap(M,pos,vel,dt); s+=alpha_schw(M,np.linalg.norm(pos))
    return s/n, dt, P

def run_cadence(M, rp_factor=3.5,k=1.10, steps_per_orbit=240, norbits=400,
                base_fb=14, mode='proper', alpha_ref=None, seed=1):
    rng=np.random.default_rng(seed)
    rs=2*G*M/c**2; rp=rp_factor*rs
    pos=np.array([rp,0.,0.]); vel=np.array([0.,k*v_circ_pw(M,rp),0.])
    P=2*math.pi*rp/np.linalg.norm(vel); dt=P/steps_per_orbit
    nsteps=steps_per_orbit*norbits
    SCALE=float(1<<base_fb)
    pos=quant_trunc(pos,SCALE); vel=quant_trunc(vel,SCALE)

    r_snap=[]; kick_snap=[]                       # at snap events
    r_all=np.empty(nsteps)                         # every step (for coord-time & proper-time budgets)
    for i in range(nsteps):
        pos,vel=leap(M,pos,vel,dt)                 # accurate float advance
        r=np.linalg.norm(pos); r_all[i]=r
        p = alpha_schw(M,r) if mode=='proper' else alpha_ref
        if rng.random()<p:                         # register update (paced by proper time if 'proper')
            E0=energy(M,pos,vel)
            pos=quant_trunc(pos,SCALE); vel=quant_trunc(vel,SCALE)
            r_snap.append(r); kick_snap.append(energy(M,pos,vel)-E0)
        if (not np.isfinite(r)) or r<1.05*rs:
            r_all=r_all[:i+1]; break
    return dict(r_snap=np.array(r_snap),kick=np.array(kick_snap),r_all=r_all,
                dt=dt,rs=rs,M=M,P=P)

def profile(res, M, nbins=22):
    """Return r/rs bin centres and: leak per coord time, leak per proper time."""
    rs=res['rs']; dt=res['dt']
    r_all=res['r_all']; r_snap=res['r_snap']; kick=res['kick']
    lo,hi=r_all.min(),r_all.max()
    edges=np.linspace(lo,hi,nbins+1); ctr=0.5*(edges[:-1]+edges[1:])
    alpha_all=np.sqrt(np.clip(1-rs/r_all,1e-9,None))
    coord_leak=np.full(nbins,np.nan); proper_leak=np.full(nbins,np.nan)
    for kk in range(nbins):
        m_all=(r_all>=edges[kk])&(r_all<edges[kk+1])
        m_sn =(r_snap>=edges[kk])&(r_snap<edges[kk+1])
        if m_all.sum()>50 and m_sn.sum()>20:
            t_coord = m_all.sum()*dt
            t_proper= np.sum(alpha_all[m_all])*dt
            K = np.sum(kick[m_sn])
            coord_leak[kk]  = abs(K)/t_coord
            proper_leak[kk] = abs(K)/t_proper
    return ctr/rs, coord_leak, proper_leak

if __name__=="__main__":
    M=10.0*M_sun; rs=2*G*M/c**2
    print(f"rs={rs:.3e} m\n")

    # --- ISCO regime boundary: perturb a circular orbit with a small RADIAL nudge ---
    # above ISCO (3 rs): bounded epicycle (leakage regime). at/below: perturbation -> plunge.
    print("=== regime boundary: 2% radial nudge to a circular orbit ===")
    isco_traces={}
    for rpf in (4.0, 3.5, 3.0, 2.6):
        r0=rpf*rs; pos=np.array([r0,0.,0.]); vel=np.array([0.02*v_circ_pw(M,r0), v_circ_pw(M,r0), 0.])
        P=2*math.pi*r0/v_circ_pw(M,r0); dt=P/400; rmn=rmx=r0; plunged=False; trace=[]
        for i in range(400*12):
            pos,vel=leap(M,pos,vel,dt); r=np.linalg.norm(pos); rmn=min(rmn,r); rmx=max(rmx,r)
            if i%20==0: trace.append((i*dt/P, r/rs))
            if r<1.05*rs: plunged=True; break
            if r>60*rs: break
        isco_traces[rpf]=np.array(trace)
        print(f"  rp={rpf:.1f} rs: {'PLUNGED (curvature breaks orbit)' if plunged else 'bound epicycle (leakage regime)'}"
              f"  amp={(rmx-rmn)/r0*100:.0f}% of r0")
    print()

    # --- cadence experiment ---
    a_ref,dt,P = mean_alpha(M, 3.5*rs, 1.10, 240, 60)
    print(f"<alpha> along orbit = {a_ref:.4f}  (used as the control's constant cadence)\n")

    proper = run_cadence(M, mode='proper')
    control= run_cadence(M, mode='control', alpha_ref=a_ref)
    print(f"proper run : {len(proper['kick'])} snaps over {len(proper['r_all'])} steps")
    print(f"control run: {len(control['kick'])} snaps over {len(control['r_all'])} steps\n")

    xr_p, coord_p, prop_p = profile(proper, M)
    xr_c, coord_c, prop_c = profile(control, M)

    # (1) coordinate-time leak ratio proper/control vs alpha(r)/<alpha>
    print("=== (1) coordinate-time leak: does proper/control track alpha(r)? ===")
    good=np.isfinite(coord_p)&np.isfinite(coord_c)
    ratio=coord_p[good]/coord_c[good]
    alpha_pred=np.sqrt(1-1/xr_p[good])/a_ref
    A=np.vstack([alpha_pred,np.ones_like(alpha_pred)]).T
    sl,ic=np.linalg.lstsq(A,ratio,rcond=None)[0]
    R2=1-np.sum((ratio-(sl*alpha_pred+ic))**2)/np.sum((ratio-ratio.mean())**2)
    print(f"  ratio ≈ {sl:.3f}·(alpha/<alpha>) + {ic:.3f}   R²={R2:.3f}   "
          f"⟨ratio/pred⟩={np.mean(ratio/alpha_pred):.3f}±{np.std(ratio/alpha_pred):.3f}")

    # (2) per-proper-time leak: honest reading.
    # NOTE: the truncation kick magnitude K(r) carries its own steep dynamical profile
    # (v and force both grow inward), which DOMINATES the ~13% alpha modulation. So the
    # per-proper-time curves are NOT flat; the cadence imprints alpha only in the RATIO,
    # where K(r) cancels. Report that plainly rather than overclaiming local flatness.
    print("\n=== (2) per-proper-time leak: dominated by dynamical kick profile K(r), not flat ===")
    g=np.isfinite(prop_c)&np.isfinite(prop_p)
    span_p=np.nanmax(prop_p[g])/np.nanmin(prop_p[g]); span_c=np.nanmax(prop_c[g])/np.nanmin(prop_c[g])
    print(f"  proper  per-proper-time leak varies x{span_p:.1f} across the orbit (this is K(r), dynamics)")
    print(f"  control per-proper-time leak varies x{span_c:.1f}")
    print(f"  => the redshift factor lives in the cadence ratio (panel 2), not in local flatness.")

    # --- plots ---
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig,ax=plt.subplots(1,3,figsize=(16,4.6))

    ax[0].plot(xr_p,coord_p,'o-',color='tab:red',label='proper-paced')
    ax[0].plot(xr_c,coord_c,'s-',color='tab:green',label='uniform cadence')
    ax[0].set_xlabel('r / rs'); ax[0].set_ylabel('leak per COORDINATE time [W]')
    ax[0].set_yscale('log'); ax[0].set_title('coordinate-time leak (dominated by dynamics K(r))')
    ax[0].legend(fontsize=8); ax[0].grid(alpha=0.3,which='both')

    ax[1].plot(xr_p[good],ratio,'o',color='tab:red',label='measured proper/control')
    xx=np.linspace(np.nanmin(xr_p),np.nanmax(xr_p),200)
    ax[1].plot(xx, np.sqrt(1-1/xx)/a_ref,'k-',label=r'$\alpha(r)/\langle\alpha\rangle$')
    ax[1].set_xlabel('r / rs'); ax[1].set_ylabel('coord-time leak ratio  proper/uniform')
    ax[1].set_title(f'redshift factor emerges from cadence (R²={R2:.3f})'); ax[1].legend(fontsize=8); ax[1].grid(alpha=0.3)

    cols={4.0:'tab:blue',3.5:'tab:cyan',3.0:'tab:orange',2.6:'tab:red'}
    for rpf,tr in isco_traces.items():
        if len(tr): ax[2].plot(tr[:,0],tr[:,1],lw=1.1,color=cols.get(rpf),label=f'rp={rpf} rs')
    ax[2].axhline(3.0,color='k',ls=':',lw=1,label='ISCO = 3 rs')
    ax[2].axhline(1.0,color='gray',ls='--',lw=0.8,label='horizon')
    ax[2].set_xlabel('orbits'); ax[2].set_ylabel('r / rs'); ax[2].set_ylim(0,6)
    ax[2].set_title('regime boundary: epicycle vs plunge'); ax[2].legend(fontsize=8); ax[2].grid(alpha=0.3)

    plt.tight_layout(); plt.savefig("/home/claude/stew_propertime.png",dpi=130)
    print("\nsaved /home/claude/stew_propertime.png")
