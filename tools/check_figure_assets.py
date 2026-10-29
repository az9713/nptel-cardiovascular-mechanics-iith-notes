"""Inspect actual external SVGs, which inline-only skill helpers cannot see."""
from __future__ import annotations

import hashlib
import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'work' / 'compliance-2026-10-28' / 'figures'


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    rows = []
    chrome = Path(os.environ.get('PROGRAMFILES', 'C:/Program Files')) / (
        'Google/Chrome/Application/chrome.exe')
    with sync_playwright() as player:
        browser = player.chromium.launch(executable_path=str(chrome),
                                         headless=True)
        page = browser.new_page(viewport={'width': 1008, 'height': 576})
        for asset in sorted((ROOT / 'assets').glob('*.svg')):
            source = asset.read_bytes()
            parsed = ET.fromstring(source)
            ids = [x.attrib['id'] for x in parsed.iter() if 'id' in x.attrib]
            page.goto(asset.as_uri())
            page.wait_for_function('document.fonts.status === "loaded"')
            probe = page.evaluate('''() => {
                const svg = document.documentElement;
                const v = svg.viewBox.baseVal;
                const labels = [...svg.querySelectorAll('text')].map(el => {
                    const b=el.getBBox();
                    const m=svg.getCTM().inverse().multiply(el.getCTM());
                    const corners=[[b.x,b.y],[b.x+b.width,b.y],
                      [b.x,b.y+b.height],[b.x+b.width,b.y+b.height]]
                      .map(([x,y]) => new DOMPoint(x,y).matrixTransform(m));
                    return {text:el.textContent,
                      x0:Math.min(...corners.map(p=>p.x)),
                      x1:Math.max(...corners.map(p=>p.x)),
                      y0:Math.min(...corners.map(p=>p.y)),
                      y1:Math.max(...corners.map(p=>p.y))};
                });
                return {viewbox:[v.x,v.y,v.width,v.height],labels,
                  clipped_labels:labels.filter(b=>b.x0<v.x-1||b.y0<v.y-1||
                    b.x1>v.x+v.width+1||b.y1>v.y+v.height+1)};
            }''')
            page.locator('svg').screenshot(path=str(WORK / (asset.stem + '.png')))
            rows.append({'asset': asset.relative_to(ROOT).as_posix(),
                         'sha256': hashlib.sha256(source).hexdigest(),
                         'unique_ids': len(ids) == len(set(ids)),
                         'viewbox': probe['viewbox'],
                         'label_count': len(probe['labels']),
                         'clipped_labels': probe['clipped_labels'],
                         'passed': len(ids) == len(set(ids)) and
                         not probe['clipped_labels']})
        browser.close()
    report = {'passed': all(x['passed'] for x in rows), 'figures': rows,
              'scope': 'Actual standalone SVG DOM label geometry and ID checks. '
                       'All five generated chart screenshots additionally need '
                       'a recorded manual semantic/overlap review. These are '
                       'quantitative plots, not anatomical body figures.'}
    (WORK / 'asset-validation.json').write_text(
        json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
