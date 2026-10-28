(() => {
'use strict';
const root = document.getElementById('vessel-lab');
if (!root) return;
const radius = document.getElementById('radius-ratio');
const demand = document.getElementById('demand-ratio');
const mode = document.getElementById('driving-condition');
const results = document.getElementById('vessel-results');
const q0 = Math.PI * 0.001 ** 4 * 1000 / (8 * 0.004 * 0.1) * 60000;
const m0 = q0 * 3;
const x = a => 65 + a / 1.2 * 545;
const y = q => 265 - q * 120;
document.getElementById('radius-curve').setAttribute('d', Array.from({length:121}, (_, i) => {
  const a = i / 100;
  return (i ? 'L' : 'M') + x(a).toFixed(2) + ' ' + y(a ** 4).toFixed(2);
}).join(' '));
function update() {
  const a = Number(radius.value), m = Number(demand.value);
  const qRatio = mode.value === 'pressure' ? a ** 4 : 1;
  const dpRatio = mode.value === 'pressure' ? 1 : a ** -4;
  const shearRatio = mode.value === 'pressure' ? a : a ** -3;
  const q = q0 * qRatio, consumption = m0 * m, cv = 9 - consumption / q;
  document.getElementById('radius-value').textContent = a.toFixed(2);
  document.getElementById('demand-value').textContent = m.toFixed(2);
  const values = [['Volume flow', q.toFixed(6) + ' L/min'], ['Flow ratio', qRatio.toFixed(6)],
    ['Pressure drop', (1000 * dpRatio).toFixed(2) + ' Pa'], ['Wall shear stress', (5 * shearRatio).toFixed(3) + ' Pa'],
    ['Oxygen consumption', consumption.toFixed(6) + ' mmol/min'],
    ['Calculated outlet oxygen content', cv.toFixed(3) + ' mmol/L']];
  results.replaceChildren();
  const dl = document.createElement('dl');
  values.forEach(([label, value]) => {const dt = document.createElement('dt'), dd = document.createElement('dd');dt.textContent=label;dd.textContent=value;dl.append(dt,dd);});
  const status = document.createElement('p');status.className='callout';
  status.textContent = cv < 0 ? 'Prescribed steady state is impossible: demand exceeds the incoming oxygen content flow.' : 'Algebraic capacity check passes: the model gives a nonnegative outlet content. This does not establish adequate tissue oxygenation.';
  results.append(dl,status);
  const point = document.getElementById('current-flow-point');point.setAttribute('cx',x(a));point.setAttribute('cy',y(qRatio));
}
[radius,demand,mode].forEach(control=>control.addEventListener('input',update));
document.getElementById('reset-vessel').addEventListener('click',()=>{radius.value='1';demand.value='1';mode.value='pressure';update();});
update();
})();
