# Proposed inspired template expansion

This is a separate, opt-in **proposed prototype**, inspired by public evaluation
task `65b59efc`. It is stored with review target `1e7c25b06dac` for transport.
The target's canonical E38 rule fills blank cells from their transposed partners;
that family does not contain the template dictionary, placement masks, swatches,
or output expansion needed here. This prototype does not replace or parameterize
E38, establish accepted lineage, qualify a parametric family, or admit data to
training. Its `identity` setting is the inferred public parent's baseline, not
the target's canonical setting.

## Source and transferred reasoning

Source: `shared/data/raw/arc-agi_evaluation_challenges.json`, exactly parent
`65b59efc`, compact sorted JSON object SHA-256 (without a trailing newline)
`ee576437bcd000a274eb9a3ab26c827d293736f23a2940e227f575b1423ee067`.
Only this task's three demonstrations and two public query inputs are used.
The CLI checks that pinned task hash, records the containing file hash, executes all three demonstration labels in
Racket, and checks them against the supplied outputs. It also executes the two
public query inputs, recording inferred output sizes/hashes; no official query
answers are present, so those executions are not query correctness evidence.

Each input has three roles:

1. Top panels define monochrome square templates keyed by their source colors.
2. Middle panels provide disjoint masks in a shared coarse coordinate space.
   Their order can differ from the top panels. A mask's color selects its
   template by color, independently of its current column.
3. A bottom swatch recolors the template directly above it. The swatch follows
   the template's top-column position, not the mask panel's position.

Superimpose the middle masks, then substitute each occupied coarse cell with
its selected and recolored template. Template holes remain background, and
empty coarse cells become blank square tiles. The public demonstrations require
all three roles; column matching and copying the masks alone are insufficient.

## One fixed rule parameter

`coarse_placement` has exactly two allowed values:

| Setting | Placement of the tile selected by mask cell `(r,c)` | Template orientation |
|---|---|---|
| `identity` | Coarse position `(r,c)` | Unchanged |
| `transpose` | Coarse position `(c,r)` | Unchanged |

The setting is fixed for every demonstration and query in one episode. It
changes the executed transformation, not input sampling. Both settings use the
same lawful inputs and ordering for a shared `input_seed` and count request.
The seed selects a separate input stream; it is never mixed with the setting.
Inputs deliberately have asymmetric coarse arrangements, distinct template
shapes, and asymmetric template geometry, so whole-output transposition cannot
stand in for coarse placement transposition.

## Run

From `WORK/`, using the packet's configured Python interpreter:

```bash
python3 run_with_racket.py python3 generators/1e7c25b06dac/workspace/parametric/inspired_template_expansion.py \
  --input-seed 137 --n-demos 3 --n-queries 4 \
  --settings identity transpose --out ../checks/parametric/final
```

Equivalent packet-root command, including the isolated interpreter used in
this review:

```bash
review_python="$PWD/WORK/.review/venv/bin/python"
"$review_python" review.py run "$review_python" \
  generators/1e7c25b06dac/workspace/parametric/inspired_template_expansion.py \
  --input-seed 137 --n-demos 3 --n-queries 4 \
  --settings identity transpose --out ../checks/parametric/final
```

The output directory must be new. The API separately accepts `n_demos=1..12`
and `n_queries=1..8`; defaults are three demonstrations and four queries. Counts,
seeds, dimensions, and cell values require exact integers, rejecting booleans
and floats. `input_seed` is `0..2**63-1`. All requested inputs are distinct
across demonstrations and queries; a bounded sampler raises on exhaustion and
never silently returns fewer examples. No query answer is reused as a demo.

Every retained demonstration/query label is produced by the matching pure
Racket function through `RacketBridge`, with Python parity checked afterward.
The exact program text and hash are saved with each private episode and under
`private/programs/`. The CLI also executes eight boundary labels for the four
combinations of template size `3/5` and panel count `3/4`.

Focused tests, from the packet root:

```bash
review_python="$PWD/WORK/.review/venv/bin/python"
"$review_python" review.py run "$review_python" \
  -m pytest generators/1e7c25b06dac/tests/test_inspired_template_expansion.py -q
```

The isolated interpreter is a review environment choice, not a bundled runtime
dependency. A relocated checkout can use its own Python plus the repository's
Racket wrapper; tests additionally require the declared development dependency
`pytest`. No copied environment is part of the prototype.

## Demonstration-only support and public export

`certify(demonstrations, query_inputs, setting)` takes no query answers. It
filters these seven finite candidates by demonstration outputs, then compares
the survivors' predictions for each query:

- Correct identity placement.
- Correct transposed coarse placement.
- Match templates and swatches to masks by column instead of source color.
- Match the template by color but choose the swatch from the mask's column.
- Replace the template with a solid recolored tile.
- Keep the source color instead of using the target swatch.
- Apply the selected coarse placement but transpose each template's pixels.

The last five use the episode's declared placement when constructing their
predictions. Certificates retain elimination demo indices and each query's
input hash, support status, and conflicting survivors. This is support within
the named finite hypothesis set, not uniqueness against arbitrary programs.

`write_bundle` projects visible data through the shared
`reviewer_support.public_challenge_bytes` and `public_challenge_id` helpers.
Public files contain only demo inputs/outputs and query inputs. Their filenames
are the SHA-256 of those exact visible bytes, sorted lexicographically, with no
setting, seed, or ordinal. Query answers, parameter maps, programs, seeds, and
certificates live exclusively under `private/`. Altering private metadata or a
query answer cannot change public names or bytes. The writer is a projection
utility; it does not independently qualify arbitrary supplied episode labels.
Both certificate demonstration outputs and any supplied private query outputs
are validated as rectangular `1..30` grids of exact integer colors `0..9` before
comparison or writing. In particular, Python's numeric equality between
`False` and `0`, or `1.0` and `1`, cannot make inexact labels valid. Invalid
private query labels are rejected before the destination is created; valid
changed private answers still leave the public projection unchanged.

## Bounded grammar and remaining limits

- Template size is `3`, `4`, or `5`; there are three or four template panels.
  Input sides stay below 30 and output sides are `9`, `16`, or `25`.
- Sources and swatches are distinct within their respective sets and exclude
  background `0` and separator `5`. The two sets may overlap, as in the parent.
  Every source appears once as a middle mask, and mask supports do not overlap.
- Source templates have holes and asymmetric geometry in sampled examples.
  Each sampled mask has at least two occupied cells. Generated supports need
  not be connected; color-keyed roles and shared placement remain necessary.
- The parser also handles the supplied parent's blank right/bottom padding,
  trailing separator, and two-cell centered swatches for even-sized templates.
  It uses the first gray cell in the top row as the template width; rotated
  legends, gray templates, ambiguous keys, overlapping masks, other sizes, and
  arbitrary alternative layouts are outside this prototype's grammar.
- Validation belongs to the Python entry point. The emitted Racket function
  defines reference behavior only for that validated grammar; it does not
  claim total, equivalent rejection behavior on arbitrary malformed grids.
- Shape/layout retries are capped at 64 each, and collecting distinct episode
  inputs is capped at 256 draws. Exhaustion is an explicit error. The retained
  evidence is bounded; it is not an exhaustive seed census or measured model
  difficulty comparison.
- These new lessons are synthetic inspired data. Reproducing the parent's
  visible demonstrations is evidence of this inferred mechanism, not verified
  ancestry, reproduction of hidden query gold answers, owner acceptance, or
  production admission.
