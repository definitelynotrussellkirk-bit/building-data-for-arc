# Proposed parametric macro-panel prototype

Original family: **training:4e7e0eb9**, selected task `2b34f380ed25`.
This task-local research prototype does not change the production generator,
canonical Racket authority, runtime interfaces, approval, or training admission.

## Rule parameter

| Parameter | Allowed values | Default |
|---|---|---|
| `mark_action` | `half_swap`, `reflection` | `half_swap` (exact canonical source) |

The canonical program decodes exact run-three macro bands, splits panels at
uniform nonzero/non-yellow divider lines, recognizes all-yellow gap strips,
and acts only on balanced marked panels. Its `half_swap` pairs left and right
halves in their original order. For macro row `[2,3 | 6,8]`, it produces
`[6,8 | 2,3]`. The alternative `reflection` reverses the partner half before
pairing, producing `[8,6 | 3,2]`. The same distinction applies to rows above and
below horizontal marks. Only two `zip-lists` expressions change in Racket.

Everything else remains the canonical program: unbalanced marks do not swap,
marks suppress the unmarked fill branch, an unmarked panel with exactly one
nonzero/non-1 color fills its 1s with that color, other panels are preserved,
and only detected macro intersections are repainted. Both branches read the
original macro board as in the canonical rule. Multiple intersecting marks
retain the original overwrite behavior; the prototype does not call that
sequential geometric composition. Authored episodes use at most one mark per
panel and uniform 3x3 blocks with zero gaps/margins.

`select_setting(seed)` selects the setting once using a separate deterministic
hash stream; `draw_inputs(seed)` samples the colors independently. Every pair
in one episode executes that same exact program. An explicit setting is offered
only to make review of both values reproducible.

## Runnable evidence command

Run from the **outer review extraction directory**, using a new output path:

```bash
python3 review.py run python3 generators/2b34f380ed25/workspace/parametric/prototype.py --seed 17 --all-settings --out ../checks/parametric/episodes-s17-v1
python3 review.py run python3 generators/2b34f380ed25/tests/test_parametric_mark_action.py
```

The second command runs ten focused prototype tests independently of canonical
repair coverage. The first writes two complete episodes, each with three
demonstrations and two larger queries. The same inputs are used for both
settings, providing direct lawful counterfactual witnesses. Demonstration 0
uses an asymmetric four-column marked panel plus an unmarked fill panel;
demonstration 1 transposes it to teach the horizontal action; demonstration 2
contrasts multicolor preservation with filling. Queries contain more active
macro cells than demonstrations and use 30x30 canvases. The 30x30 boundary
includes zero padding; this is not a claim that every added cell is meaningful.

All labels and all rival predictions execute through the included RacketBridge
and the existing rule normalization helper. The public runtime copier is used
in a temporary directory for mapped helper imports; no runtime tree is retained.
The prototype verifies all six original canonical input/output pairs under the
default exact Racket source on each evidence run.

## Evidence and visibility

Only `public/episode-N.json` is model-visible: exactly `train` demonstration
input/output pairs and `test` input-only objects. It contains no parameter,
program, seed metadata, or query label. Public filenames are opaque indices.
Keep `private/`, the controller manifest, source code, this README and logs
away from the model. Private records retain parameter/seed, roles, exact Racket,
raw-text SHA-256, every executed rival prediction, and hidden outputs. A
separate `.rkt` file materializes each exact program. The manifest binds all
retained files plus prototype, test, canonical ledger, bridge, and normalizer
source hashes. It records argv/cwd; outer command and exit code are captured
in the review command log.

For each episode the other setting must disagree on **both** first two demos;
otherwise generation fails. The selected setting must be the only member of
the finite declared two-setting set consistent with all demos. Both queries
also distinguish the settings. The two-band witness deliberately records that
a panel with one macro band per side is ambiguous: half-swap and reflection
then coincide. These are finite declared-rival checks, not proof against all
possible puzzle rules, all seeds, or future production sampling schedules.
