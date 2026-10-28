from math import pi

radius, length, viscosity, pressure_drop = 0.001, 0.1, 0.004, 1000.
flow = pi*radius**4*pressure_drop/(8*viscosity*length)
flow_l_min = flow*1000*60
arterial_content, venous_content = 9., 6.
consumption = flow_l_min*(arterial_content-venous_content)
ratio = 0.5
reduced = flow_l_min*ratio**4
required_venous = arterial_content-consumption/reduced
minimum_ratio = ((arterial_content-venous_content)
                 / arterial_content)**0.25
assert abs(required_venous+39) < 1e-10
assert abs((ratio**4)*16-1) < 1e-12
print(f'initial flow: {flow_l_min:.6f} L/min')
print(f'initial oxygen extraction: {consumption:.6f} mmol/min')
print(f'flow after radius halving: {reduced:.6f} L/min')
print(f'required venous oxygen content: {required_venous:.3f} mmol/L')
print(f'capacity-bound radius ratio: {minimum_ratio:.6f}')
print(f'wall-shear ratio at fixed pressure drop: {ratio:.3f}')
print(f'wall-shear ratio at fixed flow: {ratio**-3:.3f}')
