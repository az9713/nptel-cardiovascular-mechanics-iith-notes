import math
import numpy as np

# Stipulated teaching parameters: pressures mmHg, volumes mL, times s.
Ca, Cv, R, tau, K, deficit = 1.2, 6.0, 1.0, 2.0, 2.0, 10.0
C = Ca*Cv/(Ca+Cv)
A = np.array([[-1/(R*C), 1/C], [-K/tau, -1/tau]])
b = np.array([-deficit/C, 0.0])
steady = -np.linalg.solve(A, b)
assert np.allclose(steady, [-R*deficit/(1+K*R), K*R*deficit/(1+K*R)])
eigen = np.linalg.eigvals(A)
assert np.all(eigen.real < 0)

def integrate(h):
    y = np.zeros(2)
    minimum = 0.0
    for _ in range(round(20/h)):
        f = lambda z: A@z+b
        k1=f(y); k2=f(y+h*k1/2); k3=f(y+h*k2/2); k4=f(y+h*k3)
        y += h*(k1+2*k2+2*k3+k4)/6
        minimum = min(minimum, y[0])
    return y, minimum
end, minimum = integrate(.002)
end_half, _ = integrate(.001)
assert np.max(np.abs(end-end_half)) < 1e-9
assert np.max(np.abs(end-steady)) < 1e-5
# Incremental storage identity at independently chosen states.
for x,u,d in [(2.,3.,10.),(-4.,6.,10.),(.7,-2.,0.)]:
    xdot=(-x/R+u-d)/C
    assert math.isclose(C*x*xdot, -x*x/R+x*u-x*d, abs_tol=1e-12)
# Both compliance pairs have the same reduced pressure-difference dynamics.
for ca,cv in [(1.2,6.),(1.5,3.)]:
    assert math.isclose(ca*cv/(ca+cv), C)
beta=Cv/(Ca+Cv)
assert math.isclose(C/beta, Ca) and math.isclose(C/(1-beta), Cv)
# Unchanged total resistance can hide redistribution between parallel beds.
q0=np.array([90/2, 90/2]); q1=np.array([90/3, 90/1.5])
assert math.isclose(q0.sum(),q1.sum())
assert math.isclose(q1[0]/q0[0],2/3)
head=1060*9.81*.30/133.322387415
omega=math.sqrt(K*K-1/(R*R))/C
critical_delay=math.acos(-1/(K*R))/omega
s=1j*omega
assert abs(C*s+1/R+K*np.exp(-s*critical_delay)) < 1e-12
crossing=K*s*np.exp(-s*critical_delay)/(C-K*critical_delay*np.exp(-s*critical_delay))
assert crossing.real > 0
power=90*90*133.322387415e-6
print(f'Reduced compliance: {C:.6f} mL/mmHg')
print(f'Steady pressure/control deviations: {steady[0]:.6f} mmHg, {steady[1]:.6f} mL/s')
print(f'Poles: real {eigen[0].real:.6f}; imaginary magnitude {abs(eigen[0].imag):.6f} 1/s')
print(f'20-s pressure/control: {end[0]:.6f}, {end[1]:.6f}; RK4 refinement passed')
print(f'Parallel-bed flows: {q0[0]:.1f}/{q0[1]:.1f} to {q1[0]:.1f}/{q1[1]:.1f} mL/s')
print(f'30-cm hydrostatic pressure magnitude: {head:.6f} mmHg')
print(f'Delayed-model imaginary-root frequency/delay: {omega:.6f} 1/s, {critical_delay:.6f} s')
print(f'Baseline hydraulic power: {power:.6f} W; conservation and identifiability checks passed')
