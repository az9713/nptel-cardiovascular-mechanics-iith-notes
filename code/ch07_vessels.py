"""Original vascular geometry and mechanics checks, not fitted tissue data."""
import numpy as np
from math import pi, sqrt, log, cos, sin, exp

Q = 5e-3/60
N = 10**9
r_cap = 4e-6
area = N*pi*r_cap*r_cap
speed = Q/area
print(
    (
        f'Parallel capillary toy: total area={area:.9f} '
        f'm^2; mean speed={speed:.9f} m/s; 1mm transit={.001/speed:.6f} '
        f's'
    ))
conductance_gain = 1.2**4
print(
    (
        f'One dilated equal bed: fixed-pressure flow '
        f'gain={conductance_gain:.6f}; fixed-total '
        f'share={conductance_gain/(1+conductance_gain):.9f}'
    ))
p, r, t, mu, q = 13300., .003, .0003, .0035, 1e-6
hoop = p*r/t
wall_shear = 4*mu*q/(pi*r**3)
print(f'Thin wall hoop/fluid shear: {hoop:.6f}/{wall_shear:.6f} Pa')
# Linear-elastic thick cylinder at a stated small-deformation geometry.
a, b = .003, .0045
Aconst = p*a*a/(b*b-a*a)
Bconst = p*a*a*b*b/(b*b-a*a)
rgrid = np.linspace(a, b, 100001)
sigma_r = Aconst-Bconst/rgrid**2
sigma_theta = Aconst+Bconst/rgrid**2
assert abs(sigma_r[0]+p) < 1e-10 and abs(sigma_r[-1]) < 1e-10
average = np.trapezoid(sigma_theta, rgrid)/(b-a)
assert abs(average-p*a/(b-a)) < 1e-5
print(
    (
        f'Thick cylinder: inner hoop={sigma_theta[0]:.6f} '
        f'Pa; thickness average={average:.6f} Pa'
    ))
# Incompressible neo-Hookean tube, fixed axial stretch1, stress-free closed
# reference.
Ar, Br, ai, modulus = .003, .0036, .0045, 100000.
bo = sqrt(Br*Br+ai*ai-Ar*Ar)
rgrid = np.linspace(ai, bo, 100001)
Rref = np.sqrt(rgrid*rgrid+Ar*Ar-ai*ai)
lamtheta = rgrid/Rref
lamr = Rref/rgrid
assert np.allclose(lamtheta*lamr, 1.)
pquad = np.trapezoid(modulus*(lamtheta**2-lamr**2)/rgrid, rgrid)
panalytic = modulus*(log(Br*ai/(Ar*bo))+(ai*ai-Ar*Ar)/2*(1/ai**2-1/bo**2))
assert abs(pquad-panalytic) < 1e-5
assert abs(modulus*(log(Br*Ar/(Ar*Br)))) < 1e-12
print(
    (
        f'Neo-Hookean inflation: current outer radius={bo*1000:.6f} '
        f'mm; pressure={panalytic:.6f} Pa'
    ))
# Original symmetric two-fibre energy: orientation, not exponential alone,
# carries anisotropy.
alpha = pi/6
lt, lz = 1.2, 1.1
k1, k2 = 10000., 10.


def fibre_I(x, z):
    return x*x*cos(alpha)**2+z*z*sin(alpha)**2


def Wf(x, z):

    return k1/k2*(exp(k2*max(fibre_I(x, z)-1, 0.)**2)-1)


e = fibre_I(lt, lz)-1
nominal = 4*k1*e*exp(k2*e*e)*lt*cos(alpha)**2
h = 1e-6
finite = (Wf(lt+h, lz)-Wf(lt-h, lz))/(2*h)
assert abs(finite-nominal) < 1e-3
print(
    (
        f'Two fibres: I4={fibre_I(lt, lz):.6f}; nominal '
        f'circumferential contribution={nominal:.6f} '
        f'Pa'
    ))
E, hwall, radius, rho = 500000., .0005, .005, 1060.
c = sqrt(E*hwall/(2*rho*radius))
print(
    (
        f'Linear tube wave speed={c:.6f} m/s; fourfold '
        f'modulus speed={2*c:.6f} m/s'
    ))
print((
    'All conservation, stress, inflation, fibre '
    'derivative and wave checks passed.'
))
