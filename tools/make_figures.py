from pathlib import Path
import os
os.environ.setdefault('MPLCONFIGDIR', str(Path.cwd()/'work'/'matplotlib-cache'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path.cwd();A=R/'assets';W=R/'work';plt.style.use('dark_background')
plt.rcParams.update({'font.family':'DejaVu Serif','font.size':11,'svg.fonttype':'none'})
r=np.linspace(0.4,1.2,201);q=r**4
fig,ax=plt.subplots(figsize=(7,4));ax.plot(r,q,color='#77c7f7',lw=2)
ax.plot([0.5,1.0],[0.5**4,1.0],'o',color='#ffc875')
ax.set(xlabel='Radius / initial radius',ylabel='Flow / initial flow',title='Fixed pressure drop, viscosity and length')
ax.grid(alpha=.2);fig.tight_layout();fig.savefig(A/'radius-flow.svg');plt.close(fig)
fig,ax=plt.subplots(figsize=(7,4));ax.fill([120,120,50,50],[10,100,100,10],color='#77c7f7',alpha=.2)
ax.plot([120,120,50,50,120],[10,100,100,10,10],color='#77c7f7',lw=2)
ax.set(xlabel='Chamber volume (mL)',ylabel='Chamber pressure (mmHg)',title='An illustrative closed pumping cycle')
ax.annotate('isovolumic pressure rise',(120,50),xytext=(72,50),arrowprops={'arrowstyle':'->','color':'#ffc875'})
ax.grid(alpha=.2);fig.tight_layout();fig.savefig(A/'pressure-volume.svg');plt.close(fig)
g=np.linspace(0,.4,201);energy=1000*g*g
fig,ax=plt.subplots(figsize=(7,4));ax.plot(g,energy,lw=2,color='#77c7f7',label='Shear: added coupling energy')
ax.plot(g,np.zeros_like(g),lw=2,color='#ffc875',label='Coaxial biaxial stretch: zero gap')
ax.set(xlabel='Shear amount (dimensionless)',ylabel='Energy difference (J/m^3)',title='A parameter invisible to one experiment')
ax.legend();ax.grid(alpha=.2);fig.tight_layout();fig.savefig(A/'identifiability.svg');plt.close(fig)
h=np.linspace(.01,.5,201);inner=(1+(1+h)**2)/((1+h)**2-1);average=1/h
assert np.isclose((1+1.1**2)/(1.1**2-1),10.5238095238095)
fig,ax=plt.subplots(figsize=(7,4));ax.plot(h,inner/average,lw=2,color='#77c7f7')
ax.set(xlabel='Wall thickness / inner radius',ylabel='Inner hoop stress / wall-average hoop stress',title='A membrane average does not give the peak stress')
ax.grid(alpha=.2);fig.tight_layout();fig.savefig(A/'wall-stress.svg');plt.close(fig)
theta=np.linspace(0,np.pi/2,181)
fig,ax=plt.subplots(figsize=(7,4));ax.plot(theta*180/np.pi,np.cos(theta)-1,lw=2,color='#ffc875',label='Infinitesimal strain component')
ax.plot(theta*180/np.pi,np.zeros_like(theta),lw=2,color='#77c7f7',label='Green strain component')
ax.set(xlabel='Rigid rotation angle (degrees)',ylabel='Axial strain component (dimensionless)',title='A rotation changes orientation, not line lengths')
ax.legend();ax.grid(alpha=.2);fig.tight_layout();fig.savefig(A/'rotation-strain.svg');plt.close(fig)
print('Generated five computed SVG teaching figures; no measured patient data.')
