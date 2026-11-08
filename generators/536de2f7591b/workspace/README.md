# Task-local review tools

Selected implementation is `../generator.py`; these tools are not generators or
label authorities. They need the retained ARCpuzzles repository and Racket.
From the **extracted packet root**, after `python3 setup_racket.py`:

```sh
python3 -m pytest -q repo/generators/536de2f7591b/tests/test_review_536de2f7591b.py
python3 run_with_racket.py python3 generators/536de2f7591b/workspace/review_probe.py --lessons-per-band 100 --out ../checks/replayed-lessons.json
python3 run_with_racket.py python3 generators/536de2f7591b/workspace/audit_probe.py --out ../checks/replayed-audits.json
```

Use new output filenames. `run_with_racket.py` switches cwd to `repo`, supplies
runtime paths, and selects the offline Racket. Both probes then construct a
fresh temporary portable layout and record its actual cwd; they do not guess a
repository import path inside that layout. No installed runtime is in the delta.

## review_probe.py
Runs real `runner.run_one` with 4 train and 1 query, all difficulty bands,
100 pinned independent lesson seeds per band by default and start index 11*k.
Evaluates actual `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and witness mappings,
checks all usable canonical pairs, counts unique inputs and every cycle start,
checks Racket against a separately written stepwise Python calculation, and
preserves exact first rival disagreements plus all failing lessons/pairs.
Exits nonzero on a qualification failure; errors/timeouts are also preserved.
No Python fallback silently supplies Racket labels.

The report's fixed `phase: final` is only a convenience label: **always compare
its generator_sha256 to the source being assessed**. The first review run became
intermediate after a source correction; its preserved hash disambiguates it.
Finite rival qualification does not prove universal induction or approval.

## audit_probe.py
Findings-only reproducible audits for assigned targets 9c75b1456763 and
cdf26af5c935. Reproduces rectangle underfill, a validator hole, a broader-rule
same-color-rectangle counterexample, and 300 actual target teaching lessons.
Both targets stay unchanged. Reports actual Racket and rival outputs with source
identity and domain status. An exit-zero audit means execution/reproduction
succeeded, **not that the targets have no defects**. The target IDs are specific
to this assignment; generalize only through a separately reviewed shared tool.

## Tests and evidence
The local regression suite is explicitly invoked above; the root suite is a
separate command. `REVIEW.md`, `DECISIONS.md`, and `RESULTS.json` in the delta ZIP
record before/intermediate/final evidence and exact original invocations.
Tools refuse to overwrite prior outputs so failures remain available.
