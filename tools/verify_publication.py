"""Check served book bytes, live reader behavior and the GitHub README preview."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import subprocess
import tempfile
import time
from urllib.parse import quote
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup
from audit_public import ROOT, public_files


def fetch(url):
    request = Request(url, headers={'User-Agent': 'Cardiovascular-notes-publication-check/1.0',
                                    'Cache-Control': 'no-cache'})
    with urlopen(request, timeout=40) as response:
        return response.read()


def browser_checks(base):
    from playwright.sync_api import sync_playwright
    temporary = ROOT / 'work' / 'publication-browser'
    temporary.mkdir(parents=True, exist_ok=True)
    os.environ.update(TEMP=str(temporary), TMP=str(temporary))
    tempfile.tempdir = str(temporary)
    pages = ['index.html', *[p.name for p in sorted(ROOT.glob('chapter-??-*.html'))], 'numerical-lab.html']
    results = []
    with sync_playwright() as playwright:
        from pathlib import Path
        chrome = Path(os.environ.get('PROGRAMFILES', 'C:/Program Files'))/'Google/Chrome/Application/chrome.exe'
        browser = playwright.chromium.launch(executable_path=str(chrome), headless=True) if chrome.is_file() else playwright.chromium.launch(headless=True)
        for width in (1440, 390):
            context = browser.new_context(viewport={'width': width, 'height': 1000})
            page = context.new_page()
            for filename in pages:
                response = page.goto(base+filename)
                page.wait_for_function('!window.MathJax || !!MathJax.startup?.promise')
                page.evaluate('async () => {if(window.MathJax) await MathJax.startup.promise}')
                page.wait_for_function("document.documentElement.dataset.bookReady === 'true'")
                math_count = page.locator('mjx-container').count()
                math_errors = page.locator('mjx-merror,[data-mml-node="merror"]').count()
                overflow = page.evaluate('document.documentElement.scrollWidth > innerWidth+2')
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
                extra = True
                if filename == 'index.html':
                    page.locator('#lecture-search').fill('myocardial')
                    extra = page.locator('[data-lecture]:visible').count() == 1
                    page.locator('#lecture-search').fill('')
                if filename == 'numerical-lab.html':
                    page.locator('#radius-ratio').evaluate("el => {el.value='0.5';el.dispatchEvent(new Event('input',{bubbles:true}))}")
                    pressure = page.locator('#vessel-results').inner_text()
                    page.locator('#driving-condition').select_option('flow')
                    flow = page.locator('#vessel-results').inner_text()
                    extra = 'impossible' in pressure and '-39.000 mmol/L' in pressure and '16000.00 Pa' in flow and '40.000 Pa' in flow
                    page.locator('#reset-vessel').click()
                passed = (response.status == 200 and not overflow and not math_errors
                          and (filename == 'index.html' or math_count > 0)
                          and all((theme, text, solutions, extra)))
                results.append({'page': filename, 'width': width, 'passed': passed,
                                'math_count': math_count, 'math_errors': math_errors,
                                'horizontal_overflow': overflow, 'theme': theme,
                                'text_size': text, 'solutions': solutions,
                                'page_specific_controls': extra})
            context.close()
        browser.close()
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='https://az9713.github.io/nptel-cardiovascular-mechanics-iith-notes/')
    parser.add_argument('--repo', default='https://github.com/az9713/nptel-cardiovascular-mechanics-iith-notes')
    parser.add_argument('--browser', action='store_true')
    args = parser.parse_args()
    base = args.base.rstrip('/')+'/'
    exclusions = {
        'publication-validation.json': 'This report cannot contain a verifiable hash of itself.',
    }
    records = []
    for path in public_files():
        relative = path.relative_to(ROOT).as_posix()
        if relative in exclusions:
            continue
        expected = hashlib.sha256(path.read_bytes()).hexdigest()
        error, actual = None, None
        for attempt in range(3):
            try:
                actual = hashlib.sha256(fetch(base+quote(relative))).hexdigest()
                if actual == expected:
                    break
                error = 'served bytes differ'
            except Exception as exception:
                error = str(exception)
            if attempt < 2:
                time.sleep(2)
        records.append({'path': relative, 'sha256': expected, 'served_sha256': actual,
                        'passed': actual == expected, 'error': None if actual == expected else error})
    publication_report_present = False
    publication_report_error = None
    try:
        served_report = json.loads(fetch(base+'publication-validation.json'))
        publication_report_present = isinstance(served_report, dict) and isinstance(served_report.get('passed'), bool)
        if not publication_report_present:
            publication_report_error = 'Served report must be a JSON object with a boolean passed field'
    except Exception as exception:
        publication_report_error = str(exception)
    reader = browser_checks(base) if args.browser else []
    preview_error, preview = None, False
    try:
        document = BeautifulSoup(fetch(args.repo), 'html.parser')
        for image in document.find_all('img', alt='Preview of the cardiovascular mechanics textbook'):
            link = image.find_parent('a')
            if link and link.get('href') == base:
                preview = True
    except Exception as exception:
        preview_error = str(exception)
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    passed = all(r['passed'] for r in records) and publication_report_present and preview and all(r['passed'] for r in reader)
    report = {'passed': passed, 'checked_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'base_url': base, 'repository_url': args.repo, 'payload_commit': commit,
              'served_file_count': len(records), 'files': records,
              'excluded_from_served_hashes': exclusions,
              'live_reader': reader, 'github_readme_preview_links_to_book': preview,
              'preview_error': preview_error,
              'served_publication_report_present': publication_report_present,
              'served_publication_report_error': publication_report_error,
              'scope': 'Exact public payload bytes, representative desktop/mobile browser controls, '
                       'and rendered GitHub README image/link. No new audiovisual or mathematical review.'}
    (ROOT / 'publication-validation.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print('Publication:', passed, '; served files:', len(records), '; live reader checks:', len(reader))
    if not passed:
        print(json.dumps({'files': [r for r in records if not r['passed']],
                          'reader': [r for r in reader if not r['passed']],
                          'preview': preview, 'preview_error': preview_error}, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
