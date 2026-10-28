# Production and verification workflow

This is an independent textbook rewrite of **Introduction to Cardiovascular Mechanics**, taught by Prof. Anand Mohan at IIT Hyderabad for NPTEL. The recordings provide the topic sequence. New arguments, numerical inputs, code, figures and exercises are identified as teaching constructions.

1. Verify the complete playlist and actual official course attribution. Preserve every original playlist position, including review recordings, alternate uploads, discussion and promotional material. Reorder chapters only for pedagogical sequence, with the original mapping retained in source-manifest.json.
2. Acquire full publisher captions when accessible. Otherwise decode full audio and produce local machine ASR. Record decoded duration, media digest, chunk coverage and recognition limitations. Read every substantive source sequentially; an outline or title does not establish coverage. Keep raw recordings, captions and internal material outside the public package.
3. Inspect primary mathematical and scientific references, recording what was actually read. Distinguish historical cohort results from current population claims, and mechanics models from clinical recommendations. A citation does not certify an entire source or every statement in a chapter.
4. Calibrate a full pilot against substantial reference chapters before scaling. Develop a consequential recurring example, define objects and units before use, expose assumptions, derive the algebraic hinges, show limiting cases and counterexamples, and integrate research beside the claims it supports. Supply complete exercise solutions and actual executable outputs.
5. Keep authorship separate from independent scientific review. Complete at least two review/repair rounds. Bind the final zero-blocking review to the exact authored-body SHA256, not a mutable chapter filename. Source reading, scientific acceptance, execution checks and browser checks establish different things.
6. Assemble the root-level dark offline reader and chapter sidecars. The builder preserves the authored body between explicit markers and rejects an unexplained digest change. HTML interpolation uses escaping. The listing runner executes authored code in isolated temporary directories within the project and compares actual stdout with displayed output and checks that each chapter download exactly matches its embedded listing. The separate numerical_lab.py module provides additional reusable calculations and checks; it is not a byte-for-byte export of the short interactive-lab example.
7. Validate recording coverage and timestamp bounds; exact body digests; code; equations and local links; real offline desktop/mobile reader controls; the explicit public inventory; and a source-free export/rebuild. Inspect source-free operation separately from operation with private acquisition files present.
8. Commit and push only the reviewed, validated public package. Enable GitHub Pages and check served file bytes plus actual live reader behavior. Exclude publication-validation.json from its own hash manifest; finalize completion.json after the first successful publication probe. Record any unavoidable limitations honestly.

## Local commands

Install the optional build/check dependencies from requirements.txt in a local environment. Playwright is additionally needed for actual browser checks; its package and a Chromium-compatible browser are environment dependencies, not reader dependencies. The public reader itself requires no server or network.

~~~text
python numerical_lab.py
python tools/make_figures.py
python tools/build_book.py
python tools/export_code.py
python tools/check_chapter_code.py
python tools/validate_books.py --browser
python tools/audit_public.py
python tools/verify_source_free.py --browser
python tools/verify_publication.py --browser
~~~

The final JSON records state which stages actually passed. A successful build, word count, generated heading, ASR file or Git push does not establish scientific acceptance.

## Evidence boundaries

Machine ASR remains fallible, particularly for technical terms, numerical values and chunk boundaries. Full audio decoding does not imply perfect recognition. Selected visual frames do not constitute a full audiovisual review. Original model coefficients are illustrative unless explicitly tied to an inspected measurement. Educational mechanics calculations do not select treatment, diagnose disease or establish an individual's risk.

The offline renderer includes a vendored MathJax bundle; its upstream license is retained in assets/mathjax-LICENSE. The numerical figures are original calculations.
