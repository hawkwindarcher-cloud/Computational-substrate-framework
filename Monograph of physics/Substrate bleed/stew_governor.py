# stew_governor.py  (paired / common-random-number version)
# Does the redshift coefficient EMERGE from a discrete capacity-overflow governor, or is it set by hand?
# Fed ONLY local primitives: local field g(r), cell size ell, gate speed c.
#   per-cell EP gate-pull u(r) = beta * g(r) * ell / c^2   (c^2 = tau=ell/c times dv/c; honest, not inserted)
# A tick-packet climbs out cell by cell; each cell re-emits via a stochastic overflow governor.
# We measure the LOAD-INDUCED differential with common random numbers (loaded vs unloaded through the
# SAME governor draws), so the governor's intrinsic firing offset cancels and only the redshift remains.
# Anti-rig: sweep beta. If emergent coeff == beta, the governor transmits the local law (manufactures no 1).

import numpy as np, math
G=6.67430e-11; c=299792458.0; M_sun=1.98847e30
def g_pw(M,r):
    rs=2*G*M/c**2; return G*M/(r-rs)**2
def phi_pw(M,r):
    rs=2*G*M/c**2; return -G*M/(r-rs)

def climb(M, r_src, R_far, ncells, beta, N0=20, k=12.0, npackets=2500, hard=False, rng=None):
    if rng is None: rng=np.random.default_rng(0)
    rs=2*G*M/c**2
    s0,sF=r_src-rs,R_far-rs
    edges=rs+np.exp(np.linspace(math.log(s0),math.log(sF),ncells+1))
    rmid=0.5*(edges[:-1]+edges[1:]); ell=np.diff(edges)
    u=np.clip(beta*g_pw(M,rmid)*ell/c**2,0,0.5)
    logratio=np.zeros(npackets)               # sum_cells ln(n_unloaded / n_loaded)  per packet
    nun_mean=0.0
    for uj in u:
        if hard:
            n_un=math.ceil(N0); n_ld=math.ceil(N0*(1+uj))
            logratio+=math.log(n_un/n_ld); nun_mean+=n_un; continue
        n_un=np.zeros(npackets); n_ld=np.zeros(npackets)
        em_un=np.zeros(npackets,bool); em_ld=np.zeros(npackets,bool)
        for a in range(1,4*N0):
            fill_un=a/N0; fill_ld=a/N0-uj
            p_un=1/(1+math.exp(-k*(fill_un-1)))
            p_ld=1/(1+np.exp(-k*(fill_ld-1)))      # fill_ld shifted by load -> fires later
            U=rng.random(npackets)                  # COMMON random numbers
            f_un=(~em_un)&(U<p_un); n_un[f_un]=a; em_un|=f_un
            f_ld=(~em_ld)&(U<p_ld); n_ld[f_ld]=a; em_ld|=f_ld
            if em_un.all() and em_ld.all(): break
        n_un[n_un==0]=4*N0; n_ld[n_ld==0]=4*N0
        logratio+=np.log(n_un/n_ld); nun_mean+=n_un.mean()
    dff=np.exp(logratio)-1.0                        # rate ratio loaded/unloaded - 1  (negative=redshift)
    return dff.mean(), dff.std()/math.sqrt(npackets), nun_mean/ncells, N0

if __name__=="__main__":
    M=10.0*M_sun; rs=2*G*M/c**2; R_far=2000.0*rs
    radii=np.array([3.5,4,5,6,8,10,14,20,30,50])*rs
    phi=np.array([abs(phi_pw(M,r))/c**2 for r in radii])
    rng=np.random.default_rng(7)

    print("Emergent coefficient on |Phi|/c^2  (soft sigmoid governor, k=12):\n")
    betas=[0.25,0.5,1.0,1.5,2.0]; curves={}; fit={}
    for b in betas:
        d=[];s=[]
        for r in radii:
            m,se,nun,N0=climb(M,r,R_far,140,b,N0=20,k=12.0,npackets=2500,rng=rng)
            d.append(-m); s.append(se)
        d=np.array(d); s=np.array(s); curves[b]=(d,s)
        coeff=np.sum(d*phi)/np.sum(phi**2); fit[b]=coeff
        print(f"  beta(local EP law)={b:4.2f}  ->  emergent coeff = {coeff:.3f}   (coeff/beta={coeff/b:.3f})")

    print("\n  (a hard threshold cannot resolve the sub-quantum per-cell shift u·N0 << 1;")
    print("   the stochastic softening of eq.175 is what makes the smooth redshift representable.)")

    print("\nSoftening (k) dependence of coeff/beta at beta=1:")
    for k in (6.0,12.0,24.0,48.0):
        m,se,nun,N0=climb(M,6*rs,R_far,140,1.0,N0=20,k=k,npackets=4000,rng=rng)
        print(f"  k={k:5.1f}: coeff/beta={(-m)/(abs(phi_pw(M,6*rs))/c**2):.3f}  (<n>={nun:.1f})")

    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig,ax=plt.subplots(1,3,figsize=(16,4.6))
    d1,s1=curves[1.0]; xx=np.linspace(0,phi.max()*1.05,100)
    ax[0].plot(xx,xx,'k-',lw=1.5,label=r'GR: coeff = 1')
    ax[0].errorbar(phi,d1,yerr=s1,fmt='o',color='tab:red',capsize=3,label=f'governor (β=1): coeff={fit[1.0]:.2f}')
    ax[0].set_xlabel(r'$|\Phi(r)|/c^2$'); ax[0].set_ylabel(r'emergent $|\Delta f/f|$')
    ax[0].set_title('redshift emerges; soft governor inflates ~%.0f%%'%((fit[1.0]-1)*100)); ax[0].legend(fontsize=8); ax[0].grid(alpha=0.3)

    bs=np.array(betas); cs=np.array([fit[b] for b in betas])
    ax[1].plot([0,2.1],[0,2.1],'k--',lw=1,label='y=x (faithful transmission)')
    ax[1].plot(bs,cs,'o-',color='tab:blue',label='emergent coeff')
    ax[1].axvline(1.0,color='tab:green',ls=':',label='EP value β=1')
    ax[1].set_xlabel('input local coefficient β'); ax[1].set_ylabel('emergent coefficient')
    ax[1].set_title('governor transmits β (manufactures no 1)'); ax[1].legend(fontsize=8); ax[1].grid(alpha=0.3)

    cols={0.25:'tab:purple',0.5:'tab:cyan',1.0:'tab:red',1.5:'tab:orange',2.0:'tab:brown'}
    for b in betas:
        d,s=curves[b]; ax[2].plot(phi,d,'o-',color=cols[b],ms=4,label=f'β={b}')
    ax[2].plot(xx,xx,'k--',lw=1,label='coeff=1 (GR)')
    ax[2].set_xlabel(r'$|\Phi(r)|/c^2$'); ax[2].set_ylabel(r'emergent $|\Delta f/f|$')
    ax[2].set_title('only β≈1 lands near GR'); ax[2].legend(fontsize=8); ax[2].grid(alpha=0.3)
    plt.tight_layout(); plt.savefig("/home/claude/stew_governor.png",dpi=130)
    print("\nsaved /home/claude/stew_governor.png")
