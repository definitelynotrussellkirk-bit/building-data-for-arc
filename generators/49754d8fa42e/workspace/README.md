# Workspace

The selected implementation is `../generator.py`. Workspace files are audit
utilities and drafts; they are never selected automatically.

## Reproducible distribution and lesson audit

From the repository root, with Python 3.12+, Racket on `PATH` (or `RACKET_PATH`),
NumPy, and Pillow installed:

```bash
PYTHONPATH=src python generators/49754d8fa42e/workspace/probe_distribution.py \
  --out var/checks/49754d8fa42e-distribution.json
```

`--help` lists the replay and denominator controls. Positive counts below 100
are allowed for API smoke checks and debugging. Such reports explicitly set
`meets_required_lesson_count` to false and `audit_scope` to `smoke_or_debug`;
a passing smoke run does not establish the required distribution denominator. The default audit requests
100 independent lessons in each of `easy`, `medium`, and `hard` through public
`Catalog.generate`, using seed root 271828, five demonstration pairs, and two
query pairs. This exercises the actual public sampler, its self-check and
rejection handling, and authoritative canonical Racket labels. The public
sampler advances the seed per lesson and begins every lesson at sample index
0; it does **not** exercise every cyclic start by increasing episode count.

A second audit explicitly checks all starts 0 through 11 for nine reproducible
seeds per band: 108 overlapping lessons per band. It generates one schedule of
18 inputs for each seed and obtains its labels through public `Catalog.apply`
batches of at most 64 inputs. Window seeds begin at
`seed + count + 10000`, avoiding the independent sampler's seed range. These
108 lessons contain 756 pair occurrences but only 162 seed/sample tuples
before any errors; actual unique input counts are reported separately. The
script does not generate correct labels with a Python solver and does not
call private runner functions.

The audit reads the selected module's actual `SEMANTIC_RIVALS`,
`CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS` dictionaries. It checks each
claimed canonical shortcut against every usable labeled canonical pair in
all variants, including labeled queries. Every generated lesson records each
rival's refutation or survival on demonstrations, disagreement with each
query answer, and prediction errors. It also checks the module's
`lesson_identifiable` result using visible demonstration pairs and query
inputs. Surviving declared lesson competitors cause failure even when they
happen to agree with these particular queries.

The JSON report contains the exact generator SHA256 at the beginning and end,
the probe's own SHA256, canonical and executed rule hashes, public API call
arguments, generation rejections, reference batch receipts, seed/sample-index
tuples, input/output hashes, and per-band axis histograms for `grid_h`,
`grid_w`, `mode_color`, `mode_count`, and `palette_size`. Axis histograms count
unique inputs within each sampler and band; repeated inputs in overlapping
windows do not inflate those distributions. `mode_color` and `mode_count`
are descriptive observations of nonzero cell counts and do not supply labels.

Successful examples retain hashes and replay arguments instead of duplicating
full grids. Every failure retains its category and replay location; a bounded
number of full-grid examples per category makes failures easy to inspect.
Exceptions and materializer process receipts remain in the report. The script
returns status 1 on validation, canonical-shortcut, source-identity, rival,
reference execution, or lesson failures. Partial materializer results are
retained and are not presented as complete batches. The report is research
evidence and does not change the generator's approval or safety label.

`--out` is mandatory and replaces an existing report at that path. Select a
fresh path when retaining an earlier source-bound audit. Re-run the audit after
any generator edit; a receipt from an earlier source is not evidence for the
new source.

## Small generated counterexamples

`counterexamples.py` emits four actual generator outputs. The first two retain
exact 5×5 / mode-2 / count-5 / palette-4 endpoint controls. The last two are
unpinned spatial counterexamples with the mode at neither foreground endpoint
and at one endpoint, respectively. It records current source identity, replay
arguments, observed axes, and predictions from the actual current
`CANONICAL_SHORTCUTS` registry. No correct Python labels are supplied.

The verifier requires a separate successful canonical Racket receipt, checks its
rule/source binding and input alignment, regenerates each input from its recorded
arguments, and recomputes every declared rival prediction. It rejects stale or
altered predictions and omitted rivals. Verification uses explicit errors, not
assertions that vanish under `python -O`. The four inputs jointly refute all ten
current rivals, but are a witness set rather than a complete teaching lesson.
The emitter refuses to overwrite retained input, metadata, or reference evidence;
use a new directory for each run. A supplied receipt is checked for consistency,
not externally authenticated.

In a review packet, from packet root, use a fresh directory for retained runs:

```bash
python3 run_with_racket.py python3 generators/49754d8fa42e/workspace/counterexamples.py emit --out-dir ../checks/counterexamples-new
python3 run_with_racket.py python3 -m arcpuzzles apply 49754d8fa42e --input ../checks/counterexamples-new/input.json --out ../checks/counterexamples-new/racket.json
python3 run_with_racket.py python3 generators/49754d8fa42e/workspace/counterexamples.py verify --out-dir ../checks/counterexamples-new
```

The final retained receipt is `checks/counterexamples/racket.json` in this
return. The directory contains generated arguments and all four complete grids,
not merely a manually constructed lookalike.
