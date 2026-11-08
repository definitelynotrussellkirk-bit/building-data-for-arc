# Native centroid-ray relay family

`adapter.py` adds an episode-fixed `routing` parameter to the center-color
centroid puzzle. Production `generator.py` and its canonical authority are
unchanged. This is a separate native prototype; owner acceptance remains a
distinct step after integration and qualification on the exact live source.

| Setting | Executed rule |
|---|---|
| `direct` (default) | The byte-for-byte canonical `canonical.rkt`: select the anchor color, compute its centroid quadrant, and draw that color's diagonal ray. |
| `relay` | Compute the same first direction; follow it past background and key-colored cells to the first different color. Compute that selected color's centroid, then draw its diagonal ray from the original anchor. If no eligible hit exists, use the key color. |

The intermediate is an input-dependent ray hit and its color. Changing the
first ray can change the selected color; retaining the hit but skipping the
second centroid can change the final direction. The native causal witness
replays these interventions with complete protected Racket programs.

## Input and episode contract

The separate sampler uses square profiles with side lengths 9, 11, 15, 17, 19,
21, 25, 27 and 30. The anchor is `(height // 2, width // 2)`, including `(15,15)`
for a 30-square. The exact canonical program already defines this behavior;
the production odd-grid sampler is not extended or reapproved here. Coordinate
ties point down/right. Color 7 is background; the key and relay can be color 0.

The first two demonstrations use mixed-quadrant color clouds whose centroid
can disagree with their most populated quadrant. Independent cloud counts,
balanced ray occupancy, variable hit depths, changing final directions and
large distractor clouds prevent the observed easy selectors. The chosen
demonstrations must reject the declared finite shortcuts under **both** settings
before any query is constructed. Both demonstration candidates can be replaced
within a bounded search, avoiding a dead end caused by holding an aliased first
example fixed. Remaining ambiguity outside the declared rivals is not ruled out.

`generate(seed, settings, demos=3, queries=4)` supports **2–6 demonstrations** and
**1–4 queries** independently. Its four query profiles are 9, 19, 27 and 30.
All inputs are distinct. A seed yields identical inputs under both settings and
identical shared prefixes under different requested counts. Sampling does not
read the private setting, query labels, or future model answers.

## Reproduce

From the packet directory containing `review.py`, using its configured Python:

```bash
WORK/.venv/bin/python review.py run python3 -m pytest -q \
  generators/85d3a8e1aa7f/tests/test_parametric_relay.py

WORK/.venv/bin/python review.py run python3 \
  generators/85d3a8e1aa7f/workspace/parametric/audit.py \
  --out generators/85d3a8e1aa7f/workspace/parametric/evidence/new-audit

WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  85d3a8e1aa7f --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/85d3a8e1aa7f/new-qualification --summary
```

Every audit/qualification output directory must be new. Native qualification
requires the current source inventory; rebuild it after source changes using
`arcpuzzles parametric manifest` and the guarded `--replace` hash when necessary.
Run commands from another checkout with that checkout's environment and Racket.
There are no predecessor paths or sibling imports in the adapter.

The reusable `audit.py` executes gold labels and declared rival programs in
protected Racket, compares rival programs with their Python definitions, checks
demo-only identification, exercises count boundaries and exports examples.
Its private files retain complete two-demo/four-query episodes, settings,
answers and intermediate traces. Each hash-named public file contains only the
demonstrations and **one** query input. The private mapping supplies query order
to the existing controller; filenames and public bytes contain no settings,
seed, answers, future inputs, query count or turn hints. No turn controller or
training loop is added.

## Evidence and limits

`evidence/current/` contains the protected audit, compact original ambiguity
witnesses and current check summaries. `evidence/manifest.json` is the native
source inventory. Packet `checks/85d3a8e1aa7f/qualification/` contains native
qualification and execution; `checks/85d3a8e1aa7f/causal/` contains the
source-bound causal witness and replay.

Two initial teaching defects are preserved as private before-repair lessons:
a fixed final direction and a key-minus-four color-count selector fit both
demonstrations but disagree on a query. These files are audit counterexamples,
not clean supervised episodes. A third ray-occupancy cue and a bounded-search
dead end were repaired and covered by regression tests.

Evidence is finite: it does not prove unique interpretation, universal sampling
success, measured learning benefit, owner acceptance or training admission.
Historical production validator/domain findings remain outside this prototype.
