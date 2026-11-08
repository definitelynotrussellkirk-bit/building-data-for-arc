# Native anti-diagonal probe-relay family for `83e70bd8c0a1`

This task-local family preserves the selected anti-diagonal-reflection puzzle
and adds one matched-input alternative with a real sequential dependency.
Neither the production generator nor the selected canonical rule is changed.

| `rule` | Transformation |
|---|---|
| `full_reflection` | Reflect the entire grid across the anti-diagonal. This is the byte-exact selected canonical Racket program. |
| `probe_relay` | Reflect the unique blue probe across the anti-diagonal, read the landing cue, then transpose only that cue color's remote payload across the main diagonal. |

## Sequential dependency

**A — probe motion.** Locate the unique blue probe and reflect its coordinate
across the anti-diagonal while leaving the rest of the scene fixed.

**Intermediate.** Read the unique nonblack, non-blue cardinal neighbor at the
probe's new coordinate. Its color is input-dependent and selects one of three
remote payloads.

**B — selected payload transform.** Transpose every cell of the selected color
across the main diagonal, preserving all other cells and the moved probe.

B cannot be chosen before A. Every generated input deliberately places a
different cue beside the probe's source coordinate. The retained protected-
Racket skip-A witness reads that source cue instead of the landing cue and
therefore transforms the wrong payload, changing the final grid.

## Episode grammar

`adapter.generate(seed, settings, demos, queries)` accepts exact integer seeds in
`0..2**63-1`, 2–6 demonstrations, and 1–4 queries. The same deterministic inputs
are used for both settings. Adding demonstrations or queries never changes any
earlier pair. The ordinary native qualification request uses three
demonstrations and four queries.

Demonstration sizes are 7, 8, 9, 11, 13, and 16. Query sizes are 10, 15, 22,
and 30. Each input contains:

- exactly one blue probe;
- a source cue and a different anti-diagonal landing cue;
- a third cue as a distractor;
- three separated, nontrivial remote payloads in colors 2, 3, and 4;
- lower-triangle texture and boundary anchors outside the causal carrier.

The 30×30 query is substantive rather than padded: it has at least 90 occupied
cells, uses all four quadrants, and touches all four canvas boundaries.

## Teaching and public projection

The first two demonstrations distinguish both admitted settings and the finite
shortcut registry. The registry includes identity, single transforms,
probe-only motion, source-cue selection, copied-probe motion, fixed payload
colors, recoloring, transposing everything, and the canonical full reflection.
This is bounded evidence, not a proof against every possible program.

`public_view(episode, query_index)` emits all labeled demonstrations and exactly
one unlabeled query. It omits settings, seeds, programs, query answers, future
queries, and total-query hints. Exact first-turn bytes are identical whether the
controller generated one query or four.

## Reproduce

From the packet outer directory after `python3 review.py setup`:

```bash
python3 review.py run python3 -m pytest -q \
  generators/83e70bd8c0a1/tests/test_parametric.py

python3 review.py run python3 \
  generators/83e70bd8c0a1/workspace/parametric/audit.py \
  --out ../checks/83e70bd8c0a1/self-audit

python3 review.py run python3 -m arcpuzzles parametric qualify 83e70bd8c0a1 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/83e70bd8c0a1/qualification --summary
```

The audit sweeps 64 seeds at 2, 3, and 6 demonstrations for both settings and
writes hash-named one-query public examples. Native qualification independently
executes every claimed label through the protected Racket runtime. These
artifacts prepare an owner review; they do not establish owner acceptance,
training admission, or measured training benefit.
