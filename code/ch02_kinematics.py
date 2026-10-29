"""Original finite-kinematics and constitutive consistency checks."""
from math import sqrt
import numpy as np

f = np.array([[1., .4, 0.], [0., 1., 0.], [0., 0., 1.]])
q = np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]])
c = f.T @ f
e = (c - np.eye(3)) / 2
assert np.allclose((q @ f).T @ (q @ f), c)
stretches = np.sqrt(np.linalg.eigvalsh(c))
assert np.allclose(stretches, [sqrt(1.04)-.2, 1., sqrt(1.04)+.2])
print(f"Shear J: {np.linalg.det(f):.6f}")
print(f"Green E12, E22: {e[0, 1]:.6f}, {e[1, 1]:.6f}")
print("Principal stretches: " + ", ".join(f"{s:.6f}" for s in stretches))
rigid_green = (q.T @ q - np.eye(3)) / 2
rigid_linear = (q + q.T) / 2 - np.eye(3)
print(
    (
        f"Rigid rotation Green/linear xx: {rigid_green[0, 0]:.6f}, "
        f"{rigid_linear[0, 0]:.6f}"
    ))
velocity_gradient = np.array([[0., 10., 0.], [0., 0., 0.], [0., 0., 0.]])
d = (velocity_gradient + velocity_gradient.T) / 2
omega = np.array([[0., -3., 0.], [3., 0., 0.], [0., 0., 0.]])
l_observer = omega + q @ velocity_gradient @ q.T
d_observer = (l_observer + l_observer.T) / 2
assert np.allclose(d_observer, q @ d @ q.T)
rate = sqrt(2 * np.sum(d*d))
mu = .004
print(f"Shear-rate invariant: {rate:.6f} 1/s")
print(f"Newtonian shear stress: {(2*mu*d)[0, 1]:.6f} Pa")
stretch, modulus = 1.2, 10000.
nominal = modulus*(stretch-stretch**-2)
cauchy = modulus*(stretch**2-stretch**-1)
assert np.isclose(cauchy, stretch*nominal)
print(f"Nominal/Cauchy axial stress: {nominal:.6f}, {cauchy:.6f} Pa")
print("Objectivity, metric and stress-area checks passed")
