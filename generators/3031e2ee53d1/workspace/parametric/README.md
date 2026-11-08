# Translated motifs with an episode-fixed edge rule

Native-qualified reviewer proposal for `3031e2ee53d1` / ARC `53b68214`.
Owner integration and fresh exact-source acceptance remain pending. This does
not activate training. The canonical production generator and reference data
are unchanged.

## Rules and input grammar

`edge=linear` returns the exact canonical Racket bytes. It infers the smallest
row period and horizontal drift, then extends the pattern to a width-by-width
square, clipping at the sides. `edge=bounce` uses that same inference but
reflects the rigid whole-period motif at each horizontal boundary. Reflection
preserves the motif's orientation and consumes overshoot distance; it does not
pause at or clamp to the wall.

The reflected position depends on the union of all motif phases. If their
occupied columns range from L to R, the allowed left anchor is 0 through
S = width - (R-L+1). For block q, reflect L+q*shift through that interval and
translate every phase by the resulting anchor minus L. A zero-width movement
interval is handled without division by zero. The full union envelope must
fit throughout the observed prefix, including a partial final period.

The separate constructive grammar has periods 1–3, drift 0 or ±1/±2, one
foreground color, varying motif widths, and optional coherent internal gaps.
Gaps create repeated fragments with the same phase and drift, not unrelated
noise. Generated widths span 10–30 and input heights 4–21. Ordinary queries
cover widths 10/14, 18/22, 26, and 30. The dense 30-column profile enlarges both
the motif and its observed prefix; all labels remain square completions.
An exact 30×30 input has no continuation here, so the meaningful boundary is a
non-square input followed by a substantive 30×30 output.

## Lessons, visibility, and native API

`generate(seed, settings, demos=3, queries=4)` supports exact integer seeds
0 through 2**63-1, 2–6 demonstrations, and 1–4 queries independently. Ordinary
lessons use three demos and four distinct novel queries. Query inputs do not
change with demo count, query count, or the selected setting. Separate seeded
streams and disjoint demo/query width sets prevent cross-count deduplication
from changing the first query. Returns have independent mutable grids.

The first two demos teach opposite drift signs, different periods, a later-row
motif extreme, and magnitude-two overshoot. The first always ends partway
through its period. The third teaches zero drift. This avoids the demonstrated
phase-reset hole without increasing the demonstration count.

`public_challenge(episode, query_index)` returns only the demonstrations and
one query input. The four-query episode is private controller data. Its first
projection equals the one-query projection exactly; future inputs, settings,
programs, query answers and total counts stay out of the model-visible object.
`public_id` uses the existing shared public-byte helper, so private changes
cannot change the visible identifier. No turn controller is implemented here.

`adapter.py` imports only its exact adjacent `prototype.py`. `promotion.json`
declares the two settings, count limits, and both Racket resources. Python
labels are claims; native qualification independently executes them in Racket.

## Verified evidence and finite limits

- **109 task tests passed:** 23 existing canonical tests and 86 prototype
  tests, including exact default bytes, all five canonical pairs, reflection,
  count boundaries, public identifiers, and the phase-reset regression.
- **24/24 bounded sampler episodes succeeded.** Both settings at the maximum
  seed and six-demo/four-query boundary passed 32 protected evaluations.
  Their 30×30 outputs occupy all rows and contain 470/510 foreground cells.
- **76 protected evaluations in `audit.py`:** six minimum-demo lessons at
  seeds 0, 12 and 17; all chosen labels checked; all 54 combinations of nine
  named rivals and six lessons rejected by demonstrations. Rivals preserve
  the observed prefix. These include first-row/phase-only envelopes, clamping,
  clamp-and-reverse, wrapping, no drift, period one, phase reset and the other
  declared setting. This is finite rival coverage, not universal uniqueness.
- **Native qualification:** both settings on seeds 0 and 17, three demos and
  four queries each, 40 protected evaluations. The sibling execution file
  contains the four complete verified episodes and demo-only certificates.
- **Causal witness:** replacing the whole-period envelope with the first-row
  envelope changes 23 output cells in a qualified reflected demonstration.
  Both programs were executed and independently replayed by the existing
  witness helper. Its causal interpretation remains reviewer-authored.

Current task-local reports are in `evidence/current/`; the native source
inventory is `evidence/manifest.json`. Return evidence is at
`checks/3031e2ee53d1/qualification/{qualification,execution}.json` and
`checks/3031e2ee53d1/causal/{witness,replay}.json`.

The original seed-12 lesson had two full-period demonstrations. A reusable
phase-reset rule fitted both and disagreed on a partial-period query. The
original private lesson and protected replay are retained in
`evidence/current/phase-reset-before.json`; a separate candidate for the
existing alternative-answer workflow is in
`evidence/alternative-solutions/phase-reset-seed12.json`. It is not part of
the repaired ordinary supervised sampler and has no training admission.

## Reproduce or promote

From the outer review packet, use its passing interpreter:

```sh
WORK/.venv/bin/python review.py run python3 -m pytest -q generators/3031e2ee53d1/tests/test_parametric_3031e2ee53d1.py
WORK/.venv/bin/python review.py run python3 generators/3031e2ee53d1/workspace/parametric/audit.py
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify 3031e2ee53d1 --out ../checks/3031e2ee53d1/qualification-fresh --summary
```

After integration, the owner must refresh any stale inventory, qualify the
exact live bytes to a new directory, inspect the finite evidence, and use the
existing native acceptance command. Preserve the canonical approval and
training-admission boundaries described in `docs/parametric-promotion.md`.
