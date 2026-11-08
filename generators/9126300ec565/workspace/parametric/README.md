# Frame-axis parametric family

Native adapter for task `9126300ec565`, with an exact canonical default and
three episode-fixed settings. Owner native qualification/acceptance after
integration remains required; this workspace does not activate training data.

| Private setting | Executed transformation |
| --- | --- |
| `axis=vertical` | Exact selected canonical Racket source, byte for byte |
| `axis=horizontal` | Reflect the selected frame's original contents across its horizontal center |
| `axis=long_axis` | Select the largest-perimeter frame; a tall frame uses vertical reflection, a wide frame horizontal |

All modes preserve both outlines and all content outside the selected frame.
They copy original interior cells; they do not iterate newly copied content.
The canonical production generator and its authority are unchanged.

## Input grammar and teaching

The extended sampler draws two disjoint monochrome rectangular outlines with
odd dimensions, an untied maximum perimeter, and a nonsquare selected frame.
Frame colors vary geometrically. Interior colors exclude both frame colors.
Each fourfold reflection orbit starts with at most one colored cell; axis cells
are also supported. This avoids conflicting writes under every declared mode.
The decoy contains unfinished content, so completing the wrong frame or both
frames is observably different. Exterior pixels remain unchanged.

The first two demonstrations have opposite selected-frame orientations. Their
decoy has greater area but shorter perimeter. The selected frame occurs first
in scan order once and last once, including after transposition. Exterior
source/empty-partner pairs expose whole-canvas reflection under both axes.
These examples distinguish the three settings and the bounded declared rivals
without increasing the demo count. The two mandatory canvases have the same
orientation while their selected frames have opposite orientations, separating
frame geometry from canvas geometry.

`generate(seed, settings, demos=3, queries=4)` supports independent exact integer
counts: 2–6 demonstrations and 1–4 queries, with 3/4 the ordinary request.
Seeds are exact integers in `0..2**63-1`. Unknown settings, Boolean counts,
out-of-range counts and invalid seeds fail explicitly. All inputs are distinct.
Input RNG streams ignore the rule setting and the requested total query count.

Four queries cover a 13×19 small scene, a 21×25 medium scene (or their
transposes), and two 30×30 scenes. The large selected frame is 13×27 or 27×13,
with roughly 48 off-axis source marks and additional axis marks; the larger
canvas carries larger frames and more content. It is not empty padding.
Default labels and variant labels are obtained from protected Racket through
the existing same-checkout evaluator. The native qualifier independently
replays them.

## Causal dependency

A extracts candidate outlines and selects the unique maximum perimeter.
Its input-dependent intermediate is the selected frame's bounds, dimensions,
center and derived long-axis direction. B reflects that frame's contents in
the derived direction. A smaller, larger-area decoy can have the opposite
orientation, so selecting it changes both the target and the direction.
The qualified counterfactual witness is retained under
`checks/9126300ec565/causal/` in the reviewer return. This is a derived-geometry
dependency; it does not claim iterative state simulation.

## Run and export

From the packet's outer directory, using its prepared interpreter:

```sh
WORK/.venv/bin/python review.py run python \
  generators/9126300ec565/workspace/parametric/export_examples.py \
  --seed 17 --demos 3 --queries 4 --out ../checks/9126300ec565/examples

WORK/.venv/bin/python review.py run python \
  generators/9126300ec565/workspace/parametric/self_audit.py \
  --seed 0 --seed 14 --seed 17 --demos 2 --queries 4 \
  --out ../checks/9126300ec565/new-audit.json
```

Outputs must be new. `export_examples.py` writes `private.json` with labels,
settings, programs and ordered turn filenames. Each `turns/public/<hash>.json`
contains only the original demonstrations and one current query. Serve one
such file after each answer; no turn number, total count or future query is
present. The first turn is identical for one-query and four-query requests.
Full four-query `public/` files are authoring projections, not the sequential
model input. Public filenames hash exact visible bytes only. The reusable
writer/verifier checks projection and rejects tampering; native Racket
qualification establishes label correctness separately.

For owner qualification after source integration:

```sh
python -m arcpuzzles parametric qualify 9126300ec565 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out var/review/frame-axis-qualification --summary
```

The task's native manifest, retained checks and return `RESULTS.json` give the
exact source/evidence binding. Acceptance is a separate owner action.

## Bounded evidence and limits

The final self-audit exercises seeds 0, 14 and 17 at two demos/four queries
under all three settings: 9/9 usable lessons, 181 protected Racket evaluations.
It tests 15 named rivals for fixed-axis settings and 19 for the long-axis
setting. Rivals are fitted to demonstrations only; an equivalent survivor is
allowed only when all four query predictions agree. Execution errors fail the
audit. This is not universal identifiability or a measured learning gain.

Three earlier teaching failures are retained as executed before-cases: seed 14
let exterior mirroring survive; seed 17 let first-frame selection and then
canvas-orientation selection survive.
The final sampler constructs the missing witnesses. The audit's negative
control deliberately removes the opposite-orientation example and detects
the surviving fixed-axis rule. Exact hand-written expected grids independently
test frame selection and vertical/horizontal/shape-derived labels.

Tied outlines, even dimensions, square selected frames and conflicting
reflection colors are outside the sampled grammar. This does not narrow the
unchanged production canonical generator. No claim covers every possible
wrong rule or arbitrary out-of-grammar inputs.
