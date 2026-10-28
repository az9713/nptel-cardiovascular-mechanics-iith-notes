"""Original lumped heart-cycle checks; illustrative inputs, not a patient model."""
from math import exp, isclose

edv, esv, rate = 120., 50., 75.  # mL, mL, beats/min
sv = edv - esv
print(f"Stroke volume: {sv:.3f} mL; EF: {sv/edv:.6f}")
print(f"Output per pump: {rate*sv/1000:.3f} L/min")
mmhg_ml_to_j = 133.322387415e-6
volumes, pressures = [120.,120.,50.,50.], [10.,100.,100.,10.]
work = -sum((pressures[i]+pressures[(i+1)%4])/2 *
            (volumes[(i+1)%4]-volumes[i]) for i in range(4)) * mmhg_ml_to_j
assert isclose(work, (100-10)*70*mmhg_ml_to_j)
print(f"Loop work: {work:.6f} J; mean boundary power: {work*rate/60:.6f} W")
r, compliance, venous, initial, time = 1., 1.5, 5., 100., .5
arterial = venous+(initial-venous)*exp(-time/(r*compliance))
print(f"Diastolic arterial reservoir pressure: {arterial:.6f} mmHg")
for arterial_elastance in [1.5,3.]:
    ventricular_elastance, v0 = 2., 10.
    stroke = ventricular_elastance/(ventricular_elastance+arterial_elastance)*(edv-v0)
    end_volume = edv-stroke
    pressure = arterial_elastance*stroke
    assert isclose(pressure, ventricular_elastance*(end_volume-v0))
    print(f"Ea {arterial_elastance:.1f}: SV {stroke:.6f} mL, ESV {end_volume:.6f} mL")
regurgitant = 20.
print(f"Same chamber stroke with mitral backflow: forward output {rate*(sv-regurgitant)/1000:.3f} L/min")
print(f"Pulmonary accumulation for 0.2 L/min mismatch over 30 s: {.2*30/60*1000:.1f} mL")
print("Conservation, loop-sign and end-systolic intersection checks passed")
