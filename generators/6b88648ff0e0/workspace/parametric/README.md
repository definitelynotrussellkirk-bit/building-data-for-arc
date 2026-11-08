# Native strip-order family (current reviewer build)

`adapter.py` promotes the retained strip-stack renderer without copying or changing
its canonical default. Native `stack_order` has three values: `top_to_bottom`,
`bottom_to_top`, and `key_frequency`. The first two reuse `strip_stack.py` exactly.
The third detects/crops the cyan-delimited strips, finds the dominant color of the
first extracted two-row strip, and stably orders all whole strips by descending
count of that color. Equal counts retain marker-row order. Modal ties, outside the
constructed unique-mode grammar, use the smaller color deterministically.

A = detect/crop the first cyan-delimited strip and compute its dominant color.
Intermediate = this input-dependent color (not an episode-fixed parameter).
B = count that color in every cropped strip and sort whole two-row strips.
The protected counterfactual reads the noisy whole-field mode instead; its order
changes. This is contextual selection followed by ordering, not physical simulation.

## Native generation and self-review

Native requests use 2–6 demos and 1–4 prefix-stable queries; ordinary episodes use
three demos and all four queries. Demo/query streams are independent. Settings,
programs, seeds and answers stay private; `public_turn` exposes only the current
query with the same first-turn bytes as a one-query request. Python results are
claims, not authority: qualification and the audit execute matching Racket labels.

The first two constructive lessons teach nonmonotone order and stable ties. Both
rows are needed to derive the cue: the first cell/top row suggest the wrong color.
The second lesson uses a low-valued cue against a high-valued decoy so row sums
cannot imitate frequency ordering; a zero-prefixed middle strip refutes lexical
sorting. Other-color counts refute fixed-color sorting. These choices repair
observed two-demo holes without increasing demonstration count. The second-demo
cue is deliberately 1, 2 or 3; first demos and queries vary over all eight nonzero,
non-cyan colors. No rejection sampling is used.

Four queries span 8x8/2 strips, 16x23/4 strips, 25x21/6 strips and 30x30/8 strips.
The 30x30 case has 26-cell-wide interiors, 16 output rows and dense content touching
all boundaries. This separately extends the original generator's 1–4 strips and
3–7-cell interiors; the unchanged canonical Racket rule naturally supports it.
Finite self-review checks 26 supported/shortcut policies, including global/first-cell/
top-row/minimum/maximum cues, nine fixed colors, row sums, lexical and marker-column
ordering, per-strip mode frequency, reversed ties/rows and incorrect crops.
These are bounded controls, not unrestricted scene diversity or universal uniqueness.

```sh
# From the outer packet; choose new output paths on repeat runs.
python3 review.py run python3 generators/6b88648ff0e0/workspace/parametric/verify_native.py --out ../checks/6b88648ff0e0/audit-fresh
python3 review.py task-tests 6b88648ff0e0 --phase after --out ../checks/6b88648ff0e0/tests-fresh
python3 review.py run python3 -m arcpuzzles parametric qualify 6b88648ff0e0 --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/6b88648ff0e0/qualification-fresh --summary
```

The current inventory/qualification apply to the native strip family only. Owner
acceptance and downstream training admission are separate. Legacy `episodes.py`
and the unrelated focus reconstruction proposal below remain available, unchanged;
their historical 1–8-count interface is NOT the new native contract.

---

# Proposed parametric prototypes

These task-local prototypes are opt-in authoring work. They do not change the
selected production generator, its canonical reference, approval, or training
admission. The selected family remains `training:aab50785`, generator
`6b88648ff0e0`.

## Families and settings

| CLI family | Parameter | Default | Alternative |
|---|---|---|---|
| `strip` | `stack_order` | `top_to_bottom` | `bottom_to_top` |
| `focus` | `resolution` | `piece` | `template` |

**Strip extraction.** Exact 2×2 cyan markers delimit two-row strips of a shared
width. The default returns the selected canonical Racket source byte-for-byte.
The alternative reverses the order of whole strips; marker detection, cropping,
and the two rows within each strip retain their original meaning.

**Focus reconstruction.** This is a separate inspired proposal for public
evaluation challenge `898e7135`; its relationship to the strip family is
unverified. Match detached block-scaled pieces to holes in a perforated carrier,
using rotations and reflections (D4), then fill each hole with its piece color.
The default `piece` renders at the inferred block size; `template` renders at
unit-cell resolution. Both settings retain shape matching and reconstruction.
Only visible demonstrations and the public query input informed this proposal;
no official query answer is assumed or used.

The focus parser requires black background, a unique monochrome rectangular
carrier with a complete border, and three to six internal 4-connected holes,
including a singleton. Pieces use exact 2×2 or 3×3 blocks. Each hole shape class
must have matching piece multiplicity and one unambiguous color; duplicate
pieces of the same shape and color are allowed. Small components below one
block are distractors. The feasible block size must be unique, and outputs must
fit within 30×30. Unsupported or ambiguous scenes fail visibly. Generated
scenes use separated placement slots on 29/30-cell canvases; the parser also
admits the visible focus examples' different dimensions.

## Run from the packet's outer directory

Use the directory containing `review.py`. The wrapper selects the bundled
Racket runtime and runs payloads from `WORK/repo/`; therefore
`../checks/parametric/` resolves to `WORK/checks/parametric/`.

The bundled batch uses the default build options:

```bash
python3 review.py run python3 \
  generators/6b88648ff0e0/workspace/parametric/episodes.py build \
  --family both --seed 20261023 --n-demo 2 --n-query 4 \
  --out ../checks/parametric/batch
```

The writer refuses existing destinations. Since the bundled `batch` directory
already exists, use a fresh path to rebuild, for example:

```bash
python3 review.py run python3 \
  generators/6b88648ff0e0/workspace/parametric/episodes.py build \
  --family both --seed 20261023 --n-demo 2 --n-query 4 \
  --out ../checks/parametric/batch-rebuild
```

Verify the bundled batch, or substitute the fresh rebuild path:

```bash
python3 review.py run python3 \
  generators/6b88648ff0e0/workspace/parametric/episodes.py verify \
  --batch ../checks/parametric/batch
```

`--family` accepts `strip`, `focus`, or `both`. Build enumerates each selected
family's declared settings. One setting is fixed for every demonstration and
query in its episode; settings are never resampled per pair. Matching settings
use the same input seed for direct comparison.

Demonstration and query counts are separate exact integers in `1..8`.
The default requests two demonstrations and four queries. Every query input
must differ from the demonstrations and the other queries. The Python API
`build_episode(..., n_demo=2, n_query=4, input_seed=None, max_attempts=64)`
has a default budget of 64 input attempts; the CLI uses this default.
An exhausted distinct-input budget raises an error instead of returning fewer
pairs. The API accepts a larger explicit budget up to 4096.

## Labels, certificates, and model access

Every label is executed through the matching protected Racket program and
cross-checked against the family module's Python implementation. A certificate
fits all declared parameter settings to demonstrations only, then checks that
the surviving settings agree separately on each query. Query answers do not
select the survivors. This certificate covers the finite declared setting
family, not uniqueness among all possible rules or measured learning benefit.

Give a model only `batch/public/*.json`. Each file contains demonstration
inputs/outputs and query inputs. Public filenames are SHA-256 identifiers of
exact visible bytes; they expose no setting, seed, setting-associated ordinal,
reference program, or query answer.

Keep `batch/private/episodes.json` and `batch/private/verification.json` with
the controller. They retain query labels, settings, seeds, exact programs,
source/program hashes, certificates, and runtime identity. Verification
re-executes labels and certificates and checks source bindings, counts,
distinctness, public projection bytes, and the stored runtime report.
Read actual command output and retained evidence for verification results;
this README does not declare a completed verification run.

## Focus source hashes

Both hashes below identify the same visible challenge object: `train` contains
input/output pairs and `test` contains input grids only. Serialize with
`json.dumps(visible, sort_keys=True, separators=(",", ":"), ensure_ascii=False)`
and UTF-8 encoding.

| Recipe | SHA-256 |
|---|---|
| Compact sorted JSON, no trailing newline; packet assignment hash | `830589fa6baf6cfa593626ea8782a4bb331cda222066b538755dc6211e4f268a` |
| Same JSON plus one LF; `reviewer_support.public_challenge_bytes` recipe | `98c4b873531603b1812537135810ecd86954302f580894bb2d9ac75652e069fe` |

The second recipe also defines exported public identifiers. These hashes are
distinct serialization bindings, not conflicting challenge versions.

## Focused tests

```bash
python3 review.py run python3 \
  generators/6b88648ff0e0/tests/test_parametric_episodes.py -v
python3 review.py run python3 \
  generators/6b88648ff0e0/tests/test_focus_reconstruction.py -v
```

Tests and exports remain prototype evidence. Production qualification,
acceptance, and any downstream training decision are separate steps.
