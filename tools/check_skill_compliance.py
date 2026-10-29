"""Run the installed rigorous-explainer helpers without zero-coverage passes.

Supply --skill-root pointing to the rigorous-explainer skill directory. Static
snapshots normalize only supported delimiters and pre/code attributes. Browser
helpers inspect the actual reader. External SVG assets receive separate probes.
All snapshots, browser profiles and detailed logs stay in ignored work/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
STATIC = ("checktex", "checklt", "check_links", "check_svg", "check_prose",
          "check_proofs", "check_code", "check_probfig")
BROWSER = ("verify_dom", "check_overlap", "check_frame", "check_bodyprop")
MATH = re.compile(r'\\\((.*?)\\\)|\\\[(.*?)\\\]|\$\$(.*?)\$\$|(?<!\\)\$(.*?)(?<!\\)\$', re.S)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def snapshot(source):
    source = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", "", source,
                    flags=re.S | re.I)
    source = re.sub(r"<pre\b[^>]*>\s*<code\b[^>]*>", "<pre><code>",
                    source, flags=re.I)
    original_payloads = [next(x for x in m.groups() if x is not None)
                         for m in MATH.finditer(source)]
    def normalize(match):
        if match[1] is not None:
            return "$" + match[1] + "$"
        if match[2] is not None:
            return "$$" + match[2] + "$$"
        return match[0]
    adapted = MATH.sub(normalize, source)
    adapted_payloads = [next(x for x in m.groups() if x is not None)
                        for m in MATH.finditer(adapted)]
    if original_payloads != adapted_payloads:
        raise ValueError("Static syntax adapter changed mathematical payloads")
    return adapted


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-root", type=Path, required=True)
    parser.add_argument("--pass-name", default="final")
    parser.add_argument("--static-only", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", args.pass_name):
        parser.error("pass-name must be a simple label")
    run = ROOT / "work" / "compliance-2026-10-28" / args.pass_name
    run.mkdir(parents=True, exist_ok=True)
    temporary = run / "tmp"
    temporary.mkdir(exist_ok=True)
    env = dict(os.environ, TMP=str(temporary), TEMP=str(temporary),
               TMPDIR=str(temporary), PYTHONDONTWRITEBYTECODE="1",
               PYTHONUTF8="1")
    scripts = args.skill_root.resolve() / "scripts"
    commands = STATIC if args.static_only else STATIC + BROWSER
    helpers = {}
    for name in commands:
        path = scripts / (name + ".py")
        helpers[name] = sha(path.read_bytes())
    checks, coverage = [], []
    for page in sorted(ROOT.glob("*.html")):
        source = page.read_bytes().decode("utf-8")
        soup = BeautifulSoup(source, "html.parser")
        expected = len(soup.select("pre[data-run]"))
        adapted = snapshot(source)
        payloads = [next(x for x in m.groups() if x is not None)
                    for m in MATH.finditer(adapted)]
        target = run / page.name
        target.write_text(adapted, encoding="utf-8")
        recognized = len(re.findall(r"<pre><code>.*?</code></pre>",
                                    adapted, re.S))
        if expected and recognized < expected:
            raise ValueError("Code coverage lost: " + page.name)
        math = len(re.findall(r"(?<!\\)\$", adapted))
        if expected and not math:
            raise ValueError("Math coverage lost: " + page.name)
        coverage.append({"page": page.name,
                         "page_sha256": sha(page.read_bytes()),
                         "expected_runnable_blocks": expected,
                         "recognized_code_blocks": recognized,
                         "recognized_dollar_delimiters": math,
                         "recognized_math_spans": len(payloads),
                         "math_payload_sequence_sha256": sha(
                             json.dumps(payloads).encode()),
                         "math_payloads_unchanged": True,
                         "inline_setupfig_count": len(soup.select(
                             "svg.setupfig")),
                         "external_svg_assets": [x["src"] for x in
                             soup.select('figure img[src$=".svg"]')]})
        for name in commands:
            actual = page if name in BROWSER else target
            result = subprocess.run(
                [sys.executable, "-B", str(scripts / (name + ".py")),
                 str(actual)], cwd=ROOT, env=env, capture_output=True,
                encoding="utf-8", errors="replace", timeout=150,
                creationflags=(subprocess.CREATE_NO_WINDOW
                               if os.name == "nt" else 0),
            )
            output = result.stdout + result.stderr
            (run / (page.stem + "--" + name + ".log")).write_text(
                output, encoding="utf-8")
            checked = None
            if name == "check_code":
                found = re.search(r"(\d+) Python code block\(s\) checked",
                                  output)
                checked = int(found[1]) if found else 0
                if expected and checked < expected:
                    raise ValueError("Helper checked zero code: " + page.name)
                if "pycodestyle" not in output:
                    raise ValueError("Full PEP8 engine is required")
            checks.append({"page": page.name, "helper": name,
                           "returncode": result.returncode,
                           "passed": result.returncode == 0,
                           "checked_python_blocks": checked,
                           "log_sha256": sha(output.encode())})
            print(page.name, name, result.returncode, flush=True)
    report = {
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "pass_name": args.pass_name,
        "passed": all(x["passed"] for x in checks),
        "static_only": args.static_only,
        "helper_source_sha256": helpers,
        "coverage": coverage, "checks": checks,
        "scope": "Fresh installed-helper execution, not historical proof. "
                 "Syntax adaptation is limited to static snapshots. "
                 "Browser helpers target actual pages; external SVGs need "
                 "the separately recorded asset and semantic audit. "
                 "Advisories require editorial disposition.",
    }
    (run / "summary.json").write_text(json.dumps(report, indent=2) + "\n",
                                      encoding="utf-8")
    print("Summary:", report["passed"])
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
