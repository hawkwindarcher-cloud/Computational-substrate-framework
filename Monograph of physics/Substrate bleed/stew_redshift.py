# stew_redshift.py
# Does the register bleed carry a GRAVITATIONAL fingerprint?
# Make the register quantum dilate with depth:  q_eff(r) = q0 / alpha(r),  alpha = sqrt(1 - rs/r)
# (proper-time dilation of the substrate: deeper in the well, the register resolves fewer bits).
# Eccentric orbit so the particle samples a range of r. Measure per-step substrate energy kick,
# bin by r, and compare the GRAV-dilated run against a UNIFORM-quantum control on the same orbit.
# Dynamics: Paczynski-Wiita. Redshift factor: exact Schwarzschild (separate object).

import numpy as np, math
G=6.67430e-11; c=299792458.0; M_sun=1.98847e30; PLANCK_POWER=c**5/G

def phi_pw(M,r):
    rs=2*G*M/c**2;  return -G*M/(r-rs)
def accel_pw(M,rv):
    r=np.linalg.norm(rv); rs=2*G*M/c**2
    return -(G*M/(r-rs)**2)*(rv/r)
def energy(M,pos,vel,m=1.0):
    return 0.5*m*np.dot(vel,vel)+m*phi_pw(M,np.linalg.norm(pos))
def v_circ_pw(M,r):
    rs=2*G*M/c**2; return math.sqrt(G*M*r/(r-rs)**2)
def alpha_schw(M,r):                       # exact Schwarzschild redshift factor
    rs=2*G*M/c**2; return math.sqrt(max(1.0-rs/r, 1e-9))

def quant_trunc(x,SCALE):                  # biased truncation toward zero onto grid of size 1/SCALE
    return np.trunc(x*SCALE)/SCALE

def leap(M,pos,vel,dt):                    # one float leapfrog step (no snap)
    a=accel_pw(M,pos); vh=vel+0.5*dt*a; pn=pos+dt*vh; an=accel_pw(M,pn)
    return pn, vh+0.5*dt*an

def run_eccentric(M, rp_factor=3.5, k=1.10, steps_per_orbit=300, norbits=400,
                  base_fb=14, dilate=None):
    """
    Launch at PERIAPSIS r_p = rp_factor*rs with tangential v = k*v_circ(r_p), k>1,
    giving a bound strong-field ellipse so alpha(r) varies appreciably along the orbit.
    dilate=None      -> uniform quantum (control)
    dilate='inv_alpha'-> q_eff = q0/alpha(r)        (linear proper-time dilation)
    dilate='inv_a2'  -> q_eff = q0/alpha(r)^2       (dilation squared)
    Returns per-step (r, local substrate energy kick) plus orbit info.
    """
    rs=2*G*M/c**2; rp=rp_factor*rs
    pos=np.array([rp,0.0,0.0]); vel=np.array([0.0, k*v_circ_pw(M,rp), 0.0])
    P=2*math.pi*rp/np.linalg.norm(vel); dt=P/steps_per_orbit
    nsteps=steps_per_orbit*norbits
    SCALE0=float(1<<base_fb)
    pos=quant_trunc(pos,SCALE0); vel=quant_trunc(vel,SCALE0)

    r_rec=np.empty(nsteps); dE_rec=np.empty(nsteps)
    rmin=1e99; rmax=0.0
    for i in range(nsteps):
        r=np.linalg.norm(pos); rmin=min(rmin,r); rmax=max(rmax,r)
        # local register scale
        if dilate is None:                 SCALE=SCALE0
        elif dilate=='inv_alpha':          SCALE=SCALE0*alpha_schw(M,r)      # coarser deeper
        elif dilate=='inv_a2':             SCALE=SCALE0*alpha_schw(M,r)**2
        # paired local kick: float step vs grid-snapped step from the SAME pre-state
        pf,vf=leap(M,pos,vel,dt); E_f=energy(M,pf,vf)
        pq,vq=leap(M,pos,vel,dt); pq=quant_trunc(pq,SCALE); vq=quant_trunc(vq,SCALE)
        E_q=energy(M,pq,vq)
        r_rec[i]=r; dE_rec[i]=E_q-E_f      # substrate energy injected/removed this step
        pos,vel=pq,vq                      # advance on the grid
        if (not np.isfinite(r)) or r<1.05*rs:   # plunged
            r_rec=r_rec[:i+1]; dE_rec=dE_rec[:i+1]; break
    return dict(r=r_rec,dE=dE_rec,rs=rs,dt=dt,rmin=rmin,rmax=rmax,rp=rp,M=M,base_fb=base_fb)

def bin_by_r(res, nbins=24):
    r=res['r']; dE=res['dE']; rs=res['rs']
    lo,hi=r.min(),r.max()
    edges=np.linspace(lo,hi,nbins+1); ctr=0.5*(edges[:-1]+edges[1:])
    mean=np.full(nbins,np.nan)
    for k in range(nbins):
        m=(r>=edges[k])&(r<edges[k+1])
        if m.sum()>20: mean[k]=dE[m].mean()
    return ctr/rs, mean      # x in units of r/rs

if __name__=="__main__":
    M=10.0*M_sun; rs=2*G*M/c**2
    print(f"rs={rs:.3e} m,  Planck power={PLANCK_POWER:.3e} W\n")

    runs={}
    for tag,dil in (("uniform",None),("grav 1/alpha","inv_alpha"),("grav 1/alpha^2","inv_a2")):
        res=run_eccentric(M,dilate=dil)
        runs[tag]=res
        print(f"{tag:14s}: steps={len(res['r'])}  r range = [{res['rmin']/rs:.2f}, {res['rmax']/rs:.2f}] rs  "
              f"mean|dE|={np.mean(np.abs(res['dE'])):.3e} J")
    print()

    # bin each by r
    x_u,m_u  = bin_by_r(runs["uniform"])
    x_g,m_g  = bin_by_r(runs["grav 1/alpha"])
    x_g2,m_g2= bin_by_r(runs["grav 1/alpha^2"])

    def alpha_of(xr): return math.sqrt(max(1.0-1.0/xr,1e-9))

    # Strong test: each imposed law should recover ITSELF in the leak ratio vs the uniform control.
    def fingerprint(mg, label, power):
        xs=[]; meas=[]; pred=[]
        for xr,mu,mgi in zip(x_u,m_u,mg):
            if np.isfinite(mu) and np.isfinite(mgi) and abs(mu)>0:
                xs.append(xr); meas.append(mgi/mu); pred.append(1.0/alpha_of(xr)**power)
        meas=np.array(meas); pred=np.array(pred)
        A=np.vstack([pred,np.ones_like(pred)]).T
        slope,icpt=np.linalg.lstsq(A,meas,rcond=None)[0]
        R2=1-np.sum((meas-(slope*pred+icpt))**2)/np.sum((meas-meas.mean())**2)
        print(f"  {label:16s}: ratio ≈ {slope:.3f}·(1/α^{power}) + {icpt:.3f}   R²={R2:.3f}   "
              f"⟨meas/pred⟩={np.mean(meas/pred):.3f}±{np.std(meas/pred):.3f}")
        return np.array(xs),meas,pred

    print("=== fingerprint test: does each run's leak/uniform recover its OWN imposed law? ===")
    xg,meas_g,pred_g   = fingerprint(m_g,  "grav 1/alpha",   1)
    xg2,meas_g2,pred_g2= fingerprint(m_g2, "grav 1/alpha^2", 2)

    # cross-check: does the 1/alpha run accidentally look like 1/alpha^2 instead?
    print("\n=== cross-check (1/alpha run scored against the WRONG law 1/alpha^2) ===")
    _=fingerprint(m_g, "grav 1/alpha", 2)

    # plots
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig,ax=plt.subplots(1,3,figsize=(16,4.6))
    ax[0].plot(x_u,-m_u,'o-',label='uniform q',color='tab:green')
    ax[0].plot(x_g,-m_g,'s-',label=r'grav $q_0/\alpha$',color='tab:red')
    ax[0].plot(x_g2,-m_g2,'^-',label=r'grav $q_0/\alpha^2$',color='tab:purple')
    ax[0].set_xlabel('r / rs'); ax[0].set_ylabel('mean energy LOSS per step [J]')
    ax[0].set_title('local leak vs depth'); ax[0].set_yscale('log'); ax[0].legend(fontsize=8); ax[0].grid(alpha=0.3,which='both')

    ax[1].plot(xg,meas_g,'o',color='tab:red',label=r'measured ($1/\alpha$ run)/uniform')
    ax[1].plot(xg2,meas_g2,'^',color='tab:purple',label=r'measured ($1/\alpha^2$ run)/uniform')
    xx=np.linspace(min(xg),max(xg),200)
    ax[1].plot(xx,1/np.sqrt(1-1/xx),'-',color='k',label=r'$1/\alpha$')
    ax[1].plot(xx,1/(1-1/xx),'--',color='tab:gray',label=r'$1/\alpha^2$')
    ax[1].set_xlabel('r / rs'); ax[1].set_ylabel('leak ratio  grav / uniform')
    ax[1].set_title('gravitational fingerprint'); ax[1].legend(fontsize=8); ax[1].grid(alpha=0.3)

    # residual: measured/predicted should sit flat at 1 if passthrough is linear
    ax[2].axhline(1.0,color='k',lw=0.8)
    ax[2].plot(xg,meas_g/pred_g,'o-',color='tab:red',label=r'$1/\alpha$ run')
    ax[2].plot(xg2,meas_g2/pred_g2,'^-',color='tab:purple',label=r'$1/\alpha^2$ run')
    ax[2].set_xlabel('r / rs'); ax[2].set_ylabel('measured ratio / imposed law')
    ax[2].set_title('passthrough fidelity'); ax[2].legend(fontsize=8); ax[2].grid(alpha=0.3)
    ax[2].set_ylim(0,2)

    plt.tight_layout(); plt.savefig("/home/claude/stew_redshift.png",dpi=130)
    print("\nsaved /home/claude/stew_redshift.png")
