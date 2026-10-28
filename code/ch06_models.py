"""Original blood-model limiting cases; not a patient or device simulation."""
import numpy as np
from math import pi, sqrt, exp

def cross(g, eta0=.0736, etainf=.0035, lam=1., m=.8):
    return etainf+(eta0-etainf)/(1+(lam*np.abs(g))**m)

def casson_ratio(a):
    return 0. if a>=1 else 1-16*sqrt(a)/7+4*a/3-a**4/21

grid=np.geomspace(1e-6,1e6,1001)
assert np.all(np.diff(cross(grid))<0)
assert np.all(np.diff(cross(grid)*grid)>0)
assert cross(0.)==.0736
print(f'Cross viscosity at gamma=100: {cross(100):.9f} Pa s')
a=.25
# Independent numerical integration of the yielded annulus.
x=np.linspace(a,1.,100001)
ratio_quad=4*np.trapezoid((np.sqrt(x)-sqrt(a))**2*x*x,x)
assert abs(ratio_quad-casson_ratio(a))<1e-10
print(f'Casson plug radius/R=.25: Q/Q_Newtonian={casson_ratio(a):.9f}')

eta_s,eta_p,lam,gamma=.0035,.0065,.2,100.
L=np.zeros((3,3));L[0,1]=gamma;D=(L+L.T)/2
S=np.array([[2*eta_p*lam*gamma**2,eta_p*gamma,0],
            [eta_p*gamma,0,0],[0,0,0]])
assert np.allclose(S-lam*(L@S+S@L.T),2*eta_p*D)
print(f'Oldroyd-B steady shear: total xy={(eta_s+eta_p)*gamma:.6f} Pa; N1={S[0,0]-S[1,1]:.6f} Pa')
theta=np.linspace(0,2*pi,100001)
rate=1+np.cos(theta)-np.sin(theta)
assert abs(rate.min()-(1-sqrt(2)))<1e-8
print(f'Nonnegative stress forcing, scalar Maxwell: minimum normalized rate={rate.min():.9f}')

A=np.diag([4.,.5,1.]);G,relax=2.,.2
W=lambda B:G/2*(np.trace(B)-np.linalg.slogdet(B)[1]-3)
diss=G/(2*relax)*np.trace(A+np.linalg.inv(A)-2*np.eye(3))
eps=1e-6;Ap=np.eye(3)+(A-np.eye(3))*exp(-eps/relax)
assert abs((W(Ap)-W(A))/eps+diss)<.001
assert np.linalg.eigvalsh(Ap).min()>0 and W(A)>=0 and diss>=0
print(f'Conformation rest: stored energy={W(A):.6f} J/m^3; initial dissipation={diss:.6f} W/m^3')
phi,rhoc,rhop,vc,vp=.4,1100.,1000.,.02,.01
u=phi*vc+(1-phi)*vp
rho=phi*rhoc+(1-phi)*rhop
v=(phi*rhoc*vc+(1-phi)*rhop*vp)/rho
beta=1e6
print(f'Volume/mass velocities: {u:.9f}/{v:.9f} m/s; drag loss={beta*(vc-vp)**2:.6f} W/m^3')

# Dimensionless conservative transport demonstration on 80 equal cells.
N=80;dx=1/N;y=(np.arange(N)+.5)*dx
phi=.45*(1-(2*y-1)**8);chi=4.;Dcoef=.02
fac=np.exp(chi*phi);mob=Dcoef*np.exp(-chi*(phi[:-1]+phi[1:])/2)
c=np.ones(N);dt=.2*dx*dx/(Dcoef*fac.max())
for _ in range(160000):
    flux=np.zeros(N+1)
    flux[1:-1]=-mob*np.diff(c*fac)/dx
    c-=dt*np.diff(flux)/dx
assert abs(c.sum()*dx-1)<1e-12 and c.min()>0
ceq=1/fac;ceq/=ceq.sum()*dx
error=np.max(np.abs(c-ceq))
assert error<.001
ratio=c[0]/c[N//2]
print(f'No-flux transport: total={c.sum()*dx:.9f}; max equilibrium error={error:.9f}; wall/center={ratio:.6f}')
print('All constitutive, conformation, drag and conservative transport checks passed.')
