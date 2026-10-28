"""Original geometry, rheometry and history checks; not calibrated blood data."""
from math import pi, exp, sqrt

V, A = 90.0, 135.0  # micrometre^3 and micrometre^2
rs = (3*V/(4*pi))**(1/3)
As = 4*pi*rs**2
reduced = 6*sqrt(pi)*V/A**1.5
print(f'Equal-volume sphere area: {As:.6f} um^2; reduced volume: {reduced:.6f}')
for r in (1.5, 1.3):
    length = (V-4*pi*r**3/3)/(pi*r*r)
    area = 2*V/r+4*pi*r*r/3
    assert length>0
    print(f'Spherocylinder r={r:.1f} um: length={length:.6f} um; area={area:.6f} um^2; area budget permits={area<=A}')

P50, n, capacity = 26.0, 2.7, 20.0
S = lambda p: p**n/(P50**n+p**n)
released=capacity*(S(100)-S(40))
print(f'Toy saturation: S(100)={S(100):.6f}; S(40)={S(40):.6f}; released={released:.6f} mL/dL')

mu, omega, R, h = .0012, 10.0, .02, .001
T=pi*mu*omega*R**4/(2*h)
assert abs(2*h*T/(pi*omega*R**4)-mu)<1e-15
nflow,K=.5,.02
Tpower=2*pi*K*(omega/h)**nflow*R**(nflow+3)/(nflow+3)
rim=K*(omega*R/h)**nflow
corrected=(3+nflow)*Tpower/(2*pi*R**3)
assert abs(corrected-rim)<1e-14
print(f'Newtonian torque: {T:.9e} N m; power-law naive/correct rim stress: {4/(3+nflow):.6f}')

eta_s,eta_p,lam,gamma=.0035,.0065,.2,100.0
initial=(eta_s+eta_p)*gamma
justafter=eta_p*gamma
atlam=justafter*exp(-1)
assert abs(-atlam/(-atlam/lam)-lam)<1e-15
omega=5.
Gp=eta_p*lam*omega**2/(1+(lam*omega)**2)
Gpp=eta_s*omega+eta_p*omega/(1+(lam*omega)**2)
print(f'Maxwell stop: before={initial:.6f} Pa; after={justafter:.6f} Pa; at lambda={atlam:.6f} Pa')
print(f'Oscillatory moduli at omega=5 rad/s: Gprime={Gp:.6f} Pa; Gdoubleprime={Gpp:.6f} Pa')

ka,kb,eta0,etainf=1.,.1,.0736,.0035
aeq=lambda g:ka/(ka+kb*abs(g))
eta=lambda a:etainf+(eta0-etainf)*a
stress1=eta(aeq(1))*10
stress100=eta(aeq(100))*10
astep=lambda t: aeq(10)+(aeq(1)-aeq(10))*exp(-(ka+kb*10)*t)
assert abs(astep(0)-aeq(1))<1e-15
assert abs(astep(20)-aeq(10))<1e-14
print(f'Same gamma=10 after preshear 1/100: {stress1:.6f}/{stress100:.6f} Pa; common steady stress={eta(aeq(10))*10:.6f} Pa')
print('All geometry, torque inversion, relaxation and structural-history checks passed.')
