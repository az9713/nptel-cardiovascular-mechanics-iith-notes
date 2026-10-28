"""Original dimensioned teaching calculations; no patient-specific predictions."""
from __future__ import annotations

import math
import numpy as np

MMHG_TO_PA = 133.322387415
ML_TO_M3 = 1e-6


def poiseuille(radius, length, viscosity, pressure_drop):
    """Return m^3/s for steady Newtonian flow in a rigid circular tube."""
    if min(radius, length, viscosity) <= 0:
        raise ValueError('radius, length and viscosity must be positive')
    return math.pi*radius**4*pressure_drop/(8*viscosity*length)


def pump_metrics(edv_ml, esv_ml, beats_per_minute):
    """Return stroke volume mL, ejection fraction and output L/min."""
    if not 0 <= esv_ml <= edv_ml or edv_ml <= 0:
        raise ValueError('require 0 <= ESV <= EDV and EDV > 0')
    if beats_per_minute <= 0:
        raise ValueError('heart rate must be positive')
    stroke = edv_ml-esv_ml
    return stroke, stroke/edv_ml, stroke*beats_per_minute/1000


def loop_work(volumes_ml, pressures_mmhg):
    """Return -integral p dV in J for a closed, linearly joined P-V loop."""
    v = np.asarray(volumes_ml, dtype=float)*ML_TO_M3
    p = np.asarray(pressures_mmhg, dtype=float)*MMHG_TO_PA
    if v.ndim != 1 or p.shape != v.shape or len(v) < 3:
        raise ValueError('matching one-dimensional polygon vertices required')
    return -float(np.sum((p+np.roll(p, -1))/2*(np.roll(v, -1)-v)))


def finite_kinematics(deformation):
    """Return J, C and E for an orientation-preserving 3-by-3 map."""
    f = np.asarray(deformation, dtype=float)
    if f.shape != (3, 3):
        raise ValueError('F must have shape (3, 3)')
    j = float(np.linalg.det(f))
    if j <= 0:
        raise ValueError('F must preserve orientation and have nonzero volume')
    c = f.T @ f
    return j, c, (c-np.eye(3))/2


def shear_rate(velocity_gradient):
    """Return sqrt(2 D:D), in reciprocal seconds for L in s^-1."""
    l = np.asarray(velocity_gradient, dtype=float)
    if l.shape != (3, 3):
        raise ValueError('velocity gradient must have shape (3, 3)')
    d = (l+l.T)/2
    return math.sqrt(2*float(np.sum(d*d)))


def carreau(rate, mu_zero=0.016, mu_infinity=0.004, time_scale=2.0,
            exponent=0.5):
    """Return Pa s for nonnegative rate in s^-1; illustrative parameters."""
    if rate < 0 or min(mu_zero, mu_infinity, time_scale) <= 0:
        raise ValueError('positive viscosity/time and nonnegative rate needed')
    if mu_zero < mu_infinity or not 0 < exponent <= 1:
        raise ValueError('require mu_zero >= mu_infinity and 0 < n <= 1')
    return mu_infinity+(mu_zero-mu_infinity)*(
        1+(time_scale*rate)**2)**((exponent-1)/2)


def thin_wall_stress(pressure_pa, radius_m, thickness_m, geometry):
    """Return membrane stress Pa for positive transmural pressure."""
    if min(pressure_pa, radius_m, thickness_m) <= 0:
        raise ValueError('pressure, radius and thickness must be positive')
    if geometry not in {'cylinder', 'sphere'}:
        raise ValueError('geometry must be cylinder or sphere')
    factor = 1 if geometry == 'cylinder' else 2
    return pressure_pa*radius_m/(factor*thickness_m)


def uniaxial_neo_hookean(stretch, shear_modulus_pa):
    """Return nominal and Cauchy axial stress for lateral traction-free pull."""
    if stretch <= 0 or shear_modulus_pa <= 0:
        raise ValueError('stretch and shear modulus must be positive')
    nominal = shear_modulus_pa*(stretch-stretch**-2)
    cauchy = shear_modulus_pa*(stretch**2-stretch**-1)
    return nominal, cauchy


def orthotropic_energy(deformation, coupling_pa=0.0):
    """Illustrative incompressible tissue energy in J/m^3; not a fitted law."""
    _, c, _ = finite_kinematics(deformation)
    mu, k_f, k_s = 1000., 2000., 1500.
    return (mu*(np.trace(c)-3)/2 + k_f*(c[0, 0]-1)**2/2
            + k_s*(c[1, 1]-1)**2/2 + coupling_pa*c[0, 1]**2/2)


def demonstrations():
    radius, length, mu, dp = 0.001, 0.1, 0.004, 1000.
    flow = poiseuille(radius, length, mu, dp)
    assert math.isclose(poiseuille(radius/2, length, mu, dp), flow/16)
    stroke, fraction, output = pump_metrics(120, 50, 70)
    assert math.isclose(stroke, 70) and math.isclose(output, 4.9)
    work = loop_work([120, 120, 50, 50], [10, 100, 100, 10])
    assert math.isclose(work, 90*70*MMHG_TO_PA*ML_TO_M3)
    f = np.diag([1.2, 1/math.sqrt(1.2), 1/math.sqrt(1.2)])
    j, c, e = finite_kinematics(f)
    q = np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]])
    assert np.allclose(finite_kinematics(q @ f)[1], c)
    assert math.isclose(j, 1.)
    l = np.array([[0., 10., 0.], [0., 0., 0.], [0., 0., 0.]])
    assert math.isclose(shear_rate(l), 10.)
    assert math.isclose(shear_rate(l+np.array(
        [[0., -3., 0.], [3., 0., 0.], [0., 0., 0.]])), 10.)
    rates = [0., 1., 100., 10000.]
    viscosities = [carreau(x) for x in rates]
    assert all(x >= y for x, y in zip(viscosities, viscosities[1:]))
    assert math.isclose(viscosities[0], 0.016)
    nominal, cauchy = uniaxial_neo_hookean(1.2, 10000.)
    assert math.isclose(cauchy, 1.2*nominal)
    print(f'rigid-tube flow: {flow*1e6:.6f} mL/s')
    print(f'stroke: {stroke:.1f} mL; EF: {fraction:.6f}; output: '
          f'{output:.3f} L/min')
    print(f'rectangular pressure-volume loop work: {work:.6f} J')
    print(f'isochoric stretch J: {j:.6f}; E11: {e[0, 0]:.6f}')
    print(f'simple-shear invariant: {shear_rate(l):.6f} 1/s')
    print('illustrative viscosities Pa s: '+', '.join(
        f'{v:.6f}' for v in viscosities))
    print(f'neo-Hookean nominal/Cauchy stress: {nominal:.6f}, '
          f'{cauchy:.6f} Pa')
    biaxial = np.diag([1.2, 1.1, 1/(1.2*1.1)])
    assert math.isclose(orthotropic_energy(biaxial, 0),
                        orthotropic_energy(biaxial, 2000))
    gamma, coupling = 0.2, 2000.
    def shear(g):
        return np.array([[1., g, 0.], [0., 1., 0.], [0., 0., 1.]])
    def added_energy(g):
        return (orthotropic_energy(shear(g), coupling)
                - orthotropic_energy(shear(g), 0))
    delta = 1e-6
    added_stress = (added_energy(gamma+delta)
                    - added_energy(gamma-delta))/(2*delta)
    assert math.isclose(added_stress, coupling*gamma, rel_tol=1e-8)
    print(f'invisible biaxial coupling; shear energy gap: '
          f'{added_energy(gamma):.6f} J/m^3')
    print(f'shear stress gap from independent finite differences: '
          f'{added_stress:.6f} Pa')
    print('independent limiting, symmetry and scaling checks passed')


if __name__ == '__main__':
    demonstrations()
