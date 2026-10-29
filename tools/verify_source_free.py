"""Rebuild and test a public-only copy without recordings, ASR or editorial work files."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

from audit_public import ROOT, public_files


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', action='store_true')
    parser.add_argument('--git', action='store_true', help='Export committed HEAD using git archive')
    parser.add_argument('--install', action='store_true',
                        help='Create a fresh venv and install public requirements')
    args = parser.parse_args()
    parent = ROOT / 'work' / 'source-free'
    parent.mkdir(parents=True, exist_ok=True)
    export = Path(tempfile.mkdtemp(prefix='export-', dir=parent))
    files = public_files()
    commit = None
    if args.git:
        committed = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT)
        tracked = set(committed.decode('utf-8').strip('\0').split('\0'))
        allowed = {p.relative_to(ROOT).as_posix() for p in files}
        if tracked != allowed:
            raise ValueError('Git inventory differs from the explicit public package')
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        archive = subprocess.check_output(['git', 'archive', '--format=tar', 'HEAD'], cwd=ROOT)
        with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
            bundle.extractall(export, filter='data')
    else:
        for source in files:
            target = export / source.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    before = {p.name: sha(p) for p in export.glob('*.html')}
    commands = [
        ['tools/build_book.py'], ['tools/check_chapter_code.py'], ['numerical_lab.py'],
        ['tools/validate_books.py'] + (['--browser'] if args.browser else []),
        ['tools/audit_public.py'],
    ]
    environment = os.environ.copy()
    temporary = export / 'work' / 'tmp'
    temporary.mkdir(parents=True)
    environment.update(TEMP=str(temporary), TMP=str(temporary),
                       TMPDIR=str(temporary), PYTHONDONTWRITEBYTECODE='1',
                       PIP_CACHE_DIR=str(export / 'work' / 'pip-cache'),
                       MPLCONFIGDIR=str(export / 'work' / 'matplotlib-cache'),
                       PYTHONUTF8='1')
    results = []
    executable = sys.executable
    installation = None
    if args.install:
        venv = export / 'work' / 'venv'
        create = subprocess.run(
            [sys.executable, '-m', 'venv', str(venv)], cwd=export,
            env=environment, capture_output=True, text=True, timeout=180)
        if create.returncode:
            raise RuntimeError('Fresh venv creation failed: '+create.stderr)
        executable = str(venv / ('Scripts/python.exe' if os.name == 'nt'
                                 else 'bin/python'))
        install = subprocess.run(
            [executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
            cwd=export, env=environment, capture_output=True, text=True,
            timeout=900)
        (export / 'work' / 'installation.log').write_text(
            install.stdout+install.stderr, encoding='utf-8')
        if install.returncode:
            raise RuntimeError('Fresh dependency installation failed; see export log')
        packages = subprocess.check_output(
            [executable, '-m', 'pip', 'freeze'], cwd=export,
            env=environment, text=True)
        isolated = subprocess.check_output(
            [executable, '-c', 'import sys; print(sys.prefix != sys.base_prefix)'],
            cwd=export, env=environment, text=True).strip() == 'True'
        installation = {'passed': isolated, 'fresh_venv': isolated,
                        'system_site_packages': False,
                        'requirements_sha256': sha(export / 'requirements.txt'),
                        'resolved_packages': packages.splitlines(),
                        'installation_log_sha256': hashlib.sha256(
                            (install.stdout+install.stderr).encode()).hexdigest()}
    for command in commands:
        run = subprocess.run([executable, '-B', *command], cwd=export, env=environment,
                             capture_output=True, text=True, timeout=240)
        def redact(text):
            return text.replace(str(export), '<public-export>').replace(
                str(ROOT), '<course-root>')
        results.append({'command': 'python '+' '.join(command),
                        'returncode': run.returncode, 'stdout': redact(run.stdout),
                        'stderr': redact(run.stderr)})
    changed = [name for name, digest in before.items() if sha(export / name) != digest]
    passed = (not changed and all(r['returncode'] == 0 for r in results)
              and (not args.install or installation['passed']))
    report = {
        'passed': passed, 'public_file_count': len(files), 'html_count': len(before),
        'byte_identical_html_rebuild': not changed, 'changed_html': changed,
        'raw_source_files_available': False, 'browser_checks_requested': args.browser,
        'git_archive_commit': commit,
        'fresh_dependency_installation': installation,
        'export_method': 'git archive HEAD' if args.git else 'fresh allowlisted file copy',
        'scope': 'A source-free export inside ignored work/; no acquisition sources or '
                 'private review reports copied. '+
                 ('Python dependencies were installed into a fresh isolated venv. '
                  if args.install else 'Existing Python dependencies were reused. ')+
                 'Installed Chrome and the host OS remain platform prerequisites; '
                 'this is not a fresh operating-system installation test.',
        'html_sha256': before, 'checks': results,
    }
    (ROOT / 'source-free-validation.json').write_text(
        json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print('Source-free export:', passed, '; byte-identical HTML:', len(before)-len(changed))
    if not passed:
        print(json.dumps(report, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
