"""Execute authored Python listings and compare their displayed output."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from bs4 import BeautifulSoup
import pycodestyle
from export_code import MAPPING

ROOT = Path(__file__).resolve().parents[1]


class StyleReport(pycodestyle.BaseReport):
    def __init__(self, options):
        super().__init__(options)
        self.issues = []

    def error(self, line_number, offset, text, check):
        code = super().error(line_number, offset, text, check)
        if code:
            self.issues.append({'line': line_number, 'column': offset + 1,
                                'message': text})
        return code


def main():
    temporary_root = ROOT / 'work' / 'code-checks'
    temporary_root.mkdir(parents=True, exist_ok=True)
    records = []
    for chapter in sorted(ROOT.glob('*.html')):
        soup = BeautifulSoup(chapter.read_bytes().decode('utf-8'), 'html.parser')
        for listing in soup.select('pre[data-run]'):
            identity = listing['data-run']
            code = listing.get_text()
            options = pycodestyle.StyleGuide(quiet=True).options
            style = StyleReport(options)
            pycodestyle.Checker(lines=code.splitlines(True), options=options,
                                report=style).check_all()
            exported_path = None
            exported_matches = True
            if chapter.name.startswith("chapter-"):
                number = int(chapter.name.split("-")[1])
                exported_path = MAPPING[number]
                exported_file = ROOT / exported_path
                exported_matches = exported_file.is_file() and exported_file.read_bytes() == code.encode("utf-8")

            expected = soup.select_one(f'pre[data-output="{identity}"]')
            if expected is None:
                raise ValueError(f'{chapter.name}: output missing for {identity}')
            with tempfile.TemporaryDirectory(dir=temporary_root) as directory:
                result = subprocess.run([sys.executable, '-I', '-c', code],
                                        cwd=directory, capture_output=True,
                                        text=True, timeout=90)
            passed = (exported_matches and not style.issues and
                      result.returncode == 0 and
                      result.stdout.strip() == expected.get_text().strip())
            records.append({'chapter': chapter.name, 'listing': identity,
                            'code_sha256': hashlib.sha256(code.encode()).hexdigest(),
                            'returncode': result.returncode, 'passed': passed,
                            'exported_path': exported_path, 'exported_bytes_match': exported_matches,
                            'pycodestyle_issues': style.issues,
                            'stdout': result.stdout, 'stderr': result.stderr})
            print(chapter.name, identity, 'PASS' if passed else 'FAIL')
    report = {'scope': 'Full installed pycodestyle engine and actual isolated execution of authored listings; numerical checks are not a proof audit.',
              'pycodestyle_version': pycodestyle.__version__,
              'passed': bool(records) and all(r['passed'] for r in records),
              'listing_count': len(records), 'results': records}
    (ROOT / 'chapter-code-validation.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
