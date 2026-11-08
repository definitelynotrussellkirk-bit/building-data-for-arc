# Forward / reverse edit-stencil prototype

This separate proposed family preserves the A/B/C panel-transfer puzzle.
The episode-fixed `direction` parameter changes which edit is transferred:

| Setting | Transformation | Authority |
| --- | --- | --- |
| `forward` | Transfer A→B additions and deletions onto C | Exact canonical Racket bytes |
| `reverse` | Transfer B→A additions and deletions onto C | Same Racket rule with before/after roles exchanged |

Both branches keep existing C cells at unchanged stencil sites, paint additions
with C's color, and erase deletions. Reversing an edit means transferring the
reverse stencil; it does not claim to invert an arbitrary previous edit of C.
The main generator, canonical authority, and outstanding canonical audits are
unchanged. This prototype has no variant acceptance or training admission.

## Run from the outer review folder

Activate the packet-local environment described in `START-HERE.md`, then:

```bash
python review.py run python generators/8a851bf5cdd7/workspace/parametric/export.py build \
  --seed 17 --direction both --demos 3 --queries 4 \
  --out ../checks/stencil-new
python review.py run python generators/8a851bf5cdd7/workspace/parametric/export.py verify \
  ../checks/stencil-new
```

Use a new output directory. `--direction forward` or `reverse` emits one setting.
Counts are independent: demos 2–6, queries 1–4; defaults 3/4. Counts, seeds and color
cells require exact integer types; `bool`, float and string aliases are rejected
at the Python API. Seeds use 0..2^63−1. There is no training loop or turn controller.

`adapter.py` exposes the native `program(settings)` and
`generate(seed, settings, demos, queries)` interfaces. `promotion.json` declares
the two settings, exact default, count bounds, and adjacent resources. Adapter
loading is by exact path, independent of another adapter's cached module name.

## Teaching and variation

The first demonstration contains every one of the eight boolean occupancy
triples `(A,B,C)` at randomized locations. Consequently both visible additions
and deletions occur under either setting. Unchanged sites include both retained
foreground and preserved background; this prevents merely recoloring A or B.
Other examples use the same constructive coverage with independently sampled
content, palettes, locations, shapes and sparse/dense/balanced profiles.
Each of the three masks is sampled separately outside the witness cells.

Every emitted label is obtained from a live protected Racket bridge.
Demonstrations are fitted against **ten total named rules**: forward, reverse,
identity, recolor-before, recolor-after, forward addition-only, forward
deletion-only, reverse addition-only, reverse deletion-only, and toggle changed
sites. The selected rule must be the only survivor. An error executing an
alternative is a failure, not a successful distinction. This is finite-rival
teaching evidence; it does not establish uniqueness against arbitrary programs.
`check_teaching` accepts only demonstrations and settings, so query answers
cannot contribute to the fit. Query labels are checked separately.

Inputs and their ordering are identical across paired settings with the same
seed and counts. Settings never enter the sampler RNG. Separate deterministic
demo/query streams make the first-turn bytes identical when only query count
changes from 1 to 4. A bounded 32-attempt duplicate guard raises rather than silently
shortening an episode. In the retained probe, 20/20 requested episodes succeeded.

The four query profiles have input shapes 3×11, 6×17, 15×23 and 30×29, with respective
panel/output shapes 3×3, 6×5, 15×7 and 30×9. The larger masks have substantive random
content across the full canvas, with boundary contacts and unchanged-cell
distractors; they are not padded copies. The legal grammar is three equal panels
and two one-column separators, hence input width is `3*panel_w+2`. **Exact 30×30 is
impossible in this grammar**; 30×29 is the largest admitted input. The probe also
executes 3×29 and 30×11 boundary cases. The prototype extends the original sampler's
3–6 panel-size range; it does not alter the original sampler's distribution.

This remains a stencil-inference and transfer task. No additional iterative
simulation or updated-state dependence is claimed.

## Public/private export contract

- `public/<sha256>.json`: demonstrations and **one** input-only query. These are
  the only files intended for a model turn. Filenames hash exactly the native
  `reviewer_support.public_challenge_bytes` representation.
- `controller/<sha256>.json`: the visible multi-query container used for dataset
  inspection; it includes future inputs and must remain controller-side.
- `private/<sha256>.json`: settings, seed, query answers, exact program, runtime
  binding, and demonstration-only certificate.
- `manifest.json`: private episode mapping, turn order and file hashes. It is
  written last, and must not be shown to the model.

Serve the next `public/` member from the private turn order only after the prior
answer. No query totals, settings, seeds, future inputs, answers, or special
last-turn markers appear in its JSON. Single-query evaluation can stop after
the same first turn. Changing private metadata or query answers cannot change
the public bytes or name. A controller challenge ID naturally depends on all its
visible query inputs; a model-turn ID depends only on that one visible turn.

The verifier checks strict file inventory, hashes, exact projections, distinct
inputs, exact programs, actual Racket labels, and newly recomputed teaching.
It rejects stale/forged certificates, program hashes, runtime claims and
approval/admission flags—even if an attacker recomputes file hashes. Replaying
retained runtime claims requires the same pinned runtime bytes. This local
integrity check is not a signature or an owner approval mechanism.

## Retained evidence and bounded scope

`evidence/current/summary.json` records 20 requests: two seeds, every demo count
2–6, both settings, four queries each. All 160 generated Racket labels also
match an independent set-based Python diagnostic. Eight extra boundary labels
were executed. `boundaries.json` retains those inputs and outputs.
`evidence/current/examples/` retains two complete 3-demo/4-query episodes and
eight single-query public projections, checked through the real writer/verifier.

The summary also records four direct protected native-worker jobs: two seeds
times two settings, each 3 demos/4 queries. These check adapter compatibility and
finite setting identification. They are **not owner qualification**, acceptance,
canonical approval, or admission to training. The issued canonical source is
unverified, and its existing audit findings remain open.

Reproduce the bounded probe into a new directory:

```bash
python review.py run python generators/8a851bf5cdd7/workspace/parametric/probe.py \
  --out ../checks/stencil-probe-new
python review.py run python -m pytest -q \
  generators/8a851bf5cdd7/tests/test_parametric_stencil.py
```

The native source inventory is `evidence/manifest.json`; it binds prototype
resources, focused tests and retained evidence, but grants no approval. To refresh
it after an edit, use the documented native `arcpuzzles parametric manifest`
command and its exact existing-hash replacement guard.
