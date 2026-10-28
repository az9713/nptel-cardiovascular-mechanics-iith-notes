"""Validate chapter provenance, local links, body digests and offline reader behavior."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
START, END = '<!-- BOOK-CONTENT-START -->', '<!-- BOOK-CONTENT-END -->'


def body(document):
    return document.split(START, 1)[1].split(END, 1)[0]


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def static_checks():
    manifest = json.loads((ROOT/'source-manifest.json').read_text())
    recordings = {r['id']: r for r in manifest['lectures']}
    files = sorted(ROOT.glob('*.html'))
    parsed = {p.name: BeautifulSoup(p.read_bytes().decode('utf-8'),
                                  'html.parser') for p in files}
    errors, inventory = [], []
    chapters = sorted(ROOT.glob('chapter-??-*.html'))
    if len(chapters) != len(manifest['chapters']):
        errors.append('Available chapter count differs from planned chapter count')
    for path in files:
        source = path.read_bytes().decode('utf-8')
        soup = parsed[path.name]
        ids = [x['id'] for x in soup.select('[id]')]
        if len(ids) != len(set(ids)):
            errors.append(path.name+': duplicate HTML id')
        if START not in source or END not in source:
            errors.append(path.name+': authored body markers missing')
            continue
        if re.search(r'(?<!\\)\bqquad\b', body(source)):
            errors.append(path.name+': unescaped TeX spacing command')
        checksum = sha(body(source))
        tag = soup.select_one('meta[name="book-content-sha256"]')
        if not tag or tag.get('content') != checksum:
            errors.append(path.name+': wrapper body digest mismatch')
        for element in soup.select('a[href],script[src],link[href],img[src]'):
            href = element.get('href', element.get('src', ''))
            url = urlsplit(href)
            if url.scheme in {'http', 'https'}:
                if url.netloc.endswith('youtube.com') and url.path == '/watch':
                    query = parse_qs(url.query)
                    vid = query.get('v', [''])[0]
                    stamp = query.get('t', [None])[0]
                    if stamp is not None:
                        if vid not in recordings:
                            errors.append(path.name+': timestamp video absent from manifest')
                        elif not re.fullmatch(r'\d+s?', stamp):
                            errors.append(path.name+': unparseable timestamp')
                        elif int(stamp.rstrip('s')) > recordings[vid]['duration']:
                            errors.append(path.name+': timestamp exceeds recording')
                continue
            if url.scheme or url.netloc:
                errors.append(path.name+': unsupported link scheme '+href)
                continue
            target = (path.parent/unquote(url.path)).resolve() if url.path else path
            if not target.is_relative_to(ROOT) or not target.is_file():
                errors.append(path.name+': unresolved local link '+href)
                continue
            if url.fragment and target.suffix == '.html':
                target_soup = parsed.get(target.name)
                if target_soup and not target_soup.find(id=unquote(url.fragment)):
                    errors.append(path.name+': unresolved local anchor '+href)
        if path in chapters:
            meta_path = path.with_suffix('.meta.json')
            if not meta_path.exists():
                errors.append(path.name+': chapter sidecar missing')
                continue
            meta = json.loads(meta_path.read_text(encoding='utf-8'))
            if meta.get('authored_body_sha256') != checksum:
                errors.append(path.name+': sidecar digest mismatch')
            acceptance = meta.get('acceptance', {})
            rounds = meta.get('review_rounds', [])
            if not isinstance(acceptance, dict) or acceptance.get('status') != 'accepted' or acceptance.get('accepted_body_sha256') != checksum:
                errors.append(path.name+': no current scientific acceptance')
            if len(rounds) < 2 or not rounds[-1].get('accepted') or rounds[-1].get('reviewed_body_sha256') != checksum:
                errors.append(path.name+': independent final review missing or stale')
            elif any(rounds[-1].get(key, 1) != 0 for key in ('blocking_findings', 'major_findings', 'minor_findings')):
                errors.append(path.name+': final scientific findings remain open')
            for section in meta.get('sections', []):
                vid = section.get('video_id')
                if vid:
                    if vid not in recordings or not (0 <= section['start']
                        < section['end'] <= recordings[vid]['duration']+2):
                        errors.append(path.name+': invalid section source span')
                if not soup.find(id=section['anchor']):
                    errors.append(path.name+': section anchor absent')
                for span in section.get('source_spans', []):
                    vid = span.get('video_id')
                    if vid not in recordings or not (0 <= span['start'] < span['end'] <= recordings[vid]['duration']+2):
                        errors.append(path.name+': invalid additional source span')
        text = BeautifulSoup(body(source), 'html.parser').get_text(' ', strip=True)
        inventory.append({'path': path.name, 'body_sha256': checksum,
                          'words': len(re.findall(r'\b[\w-]+\b', text)),
                          'sections': len(soup.select('article h2')),
                          'exercises': len(soup.select('article details')),
                          'runnable_listings': len(soup.select('pre[data-run]'))})
    report = {'passed': not errors, 'errors': errors, 'html_count': len(files),
              'chapter_count': len(chapters), 'scope': 'Static structure, local links, '
              'recording timestamp bounds and exact authored-body digests. '
              'Counts do not establish scientific depth or acceptance.'}
    (ROOT/'package-validation.json').write_text(json.dumps(report, indent=2)+'\n')
    (ROOT/'content-inventory.json').write_text(json.dumps({'pages': inventory}, indent=2)+'\n')
    return report


def browser_checks():
    temporary = ROOT/'work'/'browser-tmp'
    temporary.mkdir(parents=True, exist_ok=True)
    os.environ.update(TEMP=str(temporary), TMP=str(temporary))
    tempfile.tempdir = str(temporary)
    from playwright.sync_api import sync_playwright
    result = []
    files = [ROOT/'index.html', *sorted(ROOT.glob('chapter-??-*.html')),
             ROOT/'source-map.html', ROOT/'references.html', ROOT/'numerical-lab.html']
    with sync_playwright() as p:
        chrome = Path(os.environ.get('PROGRAMFILES', 'C:/Program Files'))/'Google'/'Chrome'/'Application'/'chrome.exe'
        browser = p.chromium.launch(executable_path=str(chrome), headless=True) if chrome.is_file() else p.chromium.launch(headless=True)
        for width in (1440, 390):
            context = browser.new_context(viewport={'width': width, 'height': 1000})
            context.route('http://**/*', lambda route: route.abort())
            context.route('https://**/*', lambda route: route.abort())
            page = context.new_page()
            for path in files:
                page.goto(path.as_uri())
                page.evaluate('async () => {if(window.MathJax) await MathJax.startup.promise}')
                page.wait_for_function("document.documentElement.dataset.bookReady === 'true'")
                errors = page.locator('mjx-merror,[data-mml-node="merror"]').count()
                overflow = page.evaluate('document.documentElement.scrollWidth > innerWidth+2')
                math = page.locator('mjx-container').count()
                page.locator('#theme-toggle').click()
                theme = page.locator('body.light').count() == 1
                page.locator('#theme-toggle').click()
                page.locator('#text-toggle').click()
                text = page.locator('body.large-text').count() == 1
                page.locator('#text-toggle').click()
                page.locator('#solutions-toggle').click()
                solutions = (page.locator('article details').count()
                             == page.locator('article details[open]').count())
                page.locator('#solutions-toggle').click()
                specific = True
                if path.name == 'index.html':
                    page.locator('#lecture-search').fill('myocardial')
                    specific = page.locator('[data-lecture]:visible').count() == 1
                    page.locator('#lecture-search').fill('no-such-chapter-zzzx')
                    specific = specific and page.locator('[data-lecture]:visible').count() == 0
                    page.locator('#lecture-search').fill('')
                if path.name == 'numerical-lab.html':
                    page.locator('#radius-ratio').evaluate("el => {el.value='0.5';el.dispatchEvent(new Event('input',{bubbles:true}))}")
                    pressure = page.locator('#vessel-results').inner_text()
                    page.locator('#driving-condition').select_option('flow')
                    flow = page.locator('#vessel-results').inner_text()
                    specific = 'impossible' in pressure and '-39.000 mmol/L' in pressure and '16000.00 Pa' in flow and '40.000 Pa' in flow
                    page.locator('#reset-vessel').click()
                    specific = specific and '6.000 mmol/L' in page.locator('#vessel-results').inner_text()
                required_math = path.name.startswith('chapter-') or path.name == 'numerical-lab.html'
                passed = (not errors and not overflow and theme and text and solutions and specific
                          and (math > 0 or not required_math))
                result.append({'page': path.name, 'width': width, 'passed': passed,
                               'math_count': math, 'math_errors': errors,
                               'horizontal_overflow': overflow, 'theme': theme,
                               'text_size': text, 'expand_solutions': solutions,
                               'page_specific_controls': specific})
                if path.name == 'index.html' and width == 1440:
                    page.screenshot(path=str(ROOT/'assets'/'site-preview.png'))
            context.close()
        browser.close()
    report = {'passed': all(r['passed'] for r in result), 'results': result,
              'scope': 'Actual offline headless Chromium desktop/mobile math rendering '
              'and reader controls. Separate from scientific and audiovisual review.'}
    (ROOT/'reader-validation.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', action='store_true')
    args = parser.parse_args()
    report = static_checks()
    print('Static reader checks:', report['passed'])
    if report['errors']:
        print('\n'.join(report['errors']))
    browser = browser_checks() if args.browser else {'passed': True}
    if args.browser:
        print('Offline browser checks:', browser['passed'])
    return 0 if report['passed'] and browser['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
