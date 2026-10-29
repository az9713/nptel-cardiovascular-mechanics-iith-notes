"""Original geometry, deformation and experiment-identifiability checks."""
from math import pi, exp, isclose
import numpy as np

outer, inner = (50., 30.), (45., 25.)  # long/short semiaxes in mm
wall_ml = 4*pi/3*(outer[0]*outer[1]**2-inner[0]*inner[1]**2)/1000
print(f"Illustrative full ellipsoidal wall: {wall_ml:.6f} mL")
print(f"Mass at 1.05 g/mL: {1.05*wall_ml:.6f} g")
f = np.array([[1.2, .3, 0.], [.2, 1.1, 0.], [0., 0., 1/(1.2*1.1-.3*.2)]])
assert isclose(np.linalg.det(f), 1.)
print(
    (
        f"Sheared biaxial thickness ratio: {f[2, 2]:.6f}; "
        f"J: {np.linalg.det(f):.6f}"
    ))


def energy(deformation, coupling):
    c = deformation.T @ deformation
    return (1000*(np.trace(c)-3)/2+2000*(c[0, 0]-1)**2/2
            + 1500*(c[1, 1]-1)**2/2+coupling*c[0, 1]**2/2)


for l1, l2 in [(1., 1.), (1.1, 1.2), (1.2, 1.1), (1.3, 1.05)]:
    diagonal = np.diag([l1, l2, 1/(l1*l2)])
    assert isclose(energy(diagonal, 0.), energy(diagonal, 2000.))


def shear(g):
    return np.array([[1., g, 0.], [0., 1., 0.], [0., 0., 1.]])


def gap(g):
    return energy(shear(g), 2000.)-energy(shear(g), 0.)


gamma, delta = .2, 1e-6
shear_stress = (gap(gamma+delta)-gap(gamma-delta))/(2*delta)
assert isclose(gap(gamma), 2000*gamma**2/2)
assert isclose(shear_stress, 2000*gamma, rel_tol=1e-8)
print(f"Biaxially invisible parameter: shear energy gap {gap(gamma):.6f} J/m3")
print(f"Shear traction gap: {shear_stress:.6f} Pa")


def membrane(lam):
    e = (lam**2-1)/2
    return 2*(exp(10*e**2/2)-1)  # energy/reference area, N/m


lam = 1.5
e = (lam**2-1)/2
resultant = 2*exp(10*e**2/2)*10*e*lam
fd = (membrane(lam+delta)-membrane(lam-delta))/(2*delta)
assert isclose(resultant, fd, rel_tol=1e-8)
print(f"Illustrative membrane nominal resultant: {resultant:.6f} N/m")
active_tension, area = 5000., 10e-6
print(f"Constrained active bar reaction: {active_tension*area:.6f} N")
print((
    "Geometry, incompressibility, energy-derivative "
    "and identifiability checks passed"
))
