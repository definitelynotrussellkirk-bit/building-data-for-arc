# Proposed rectangle-shape packing episodes

Status: **prototype**, separate from the selected fixed-rule generator and its
approval. This parameter changes the rectangle into which the same kinds of
colored polyominoes must be packed.

| Parameter | Allowed values | Canonical default | Executed effect |
| --- | --- | --- | --- |
| `target_rows` | integer `2` or `3` | `3` | Output is `target_rows` by `12 // target_rows`: 2x6 or 3x4. |

The rule retains four-connected monochrome component extraction, descending-area
then ascending-color piece order, and the selected translation / rotation /
reflection backtracking sequence. Every input has twelve foreground cells,
three colors and three to five separated components. `target_rows=3` emits the
exact original Racket program; the alternative changes only its two named output
dimension declarations. The original source's full SHA256 is checked before use.

## Run and reuse

From the outer packet directory:

```sh
python3 review.py run python3 generators/42a152269589/workspace/parametric/prototype.py --seeds 17 29 41 --out ../checks/parametric
```

The destination must be new. The command writes the exact `.rkt` programs, a
checkpointed `result.json`, and six complete episodes (two settings at each of
three seeds). A fresh Racket bridge executes all 24 episode labels, both settings
on a common lawful input, and all alternate-setting demonstration predictions.
The result records the Racket executable/prelude identity and source hashes.
Exceptions leave a failed receipt and propagate a nonzero exit.

Python API: `generate_episode(seed)` chooses the parameter once with a seeded
local RNG. `generate_episode(seed, target_rows=2)` fixes a setting for controlled
experiments. These constructors initially mark their Python labels as pending
Racket verification. Use the CLI materializer for verified artifacts.

Each `episode-NNN/public.json` contains only three input/output demonstrations
and one query input. Only this file is model-visible. `private.json` retains the
seed, parameter, query label, actual alternate-rule predictions, construction
attempt counts and verification status. The top-level report and rule sources
are also authoring evidence, not model input. The public filenames do not reveal
the hidden parameter.

## Construction, evidence and limits

The canonical setting calls the selected generator with sample indices 0,1,2,3
and difficulty `medium`, preserving its ordinary input draws. The 2x6 setting
grows connected partitions of that rectangle, transforms and scatters the pieces,
and keeps a draw only when the Python mirror classifies the required solver
depth. The three demonstrations require translation, rotation, and reflection;
the final query uses the translation profile. Labels are checked against the
full emitted Racket rule. Solver-depth classifications are mirror checks, not
independent Racket ablation proofs.

This is an **ordered** three-demonstration curriculum. Arbitrary query rotations
are not promised. Demonstrations distinguish the finite alternative target
setting before its query: their output geometry exposes the rule's target shape.
Every alternate Racket output is retained, including `false` when that alternative
cannot pack an input. A separate common input packs under both settings and has
different real Racket outputs, so the variation changes executed geometry even
on the shared domain.

Alternative 2x6 inputs need not be solvable under the canonical 3x4 rule, and are
not canonical training inputs. They are checked in the alternative rule's domain.
The alternative sampler has a 512-attempt bound per profile and fails loudly if
it cannot find the requested witness. The retained seeds are finite evidence,
not a guarantee over every seed, parameter extension, rival, or query policy.

The module uses public `reviewer_support` root/source helpers in both library and
portable layouts. It reuses the selected task's component and shape helpers.
For this exact hash-pinned plain-Racket lambda, `callable_rule` uses shared
`strip_rule_wrapper`; the general `wrap_rule` currently imports a legacy
`scripts` namespace absent from direct repository commands. That tooling issue
and the genuine failed attempt are retained in the return feedback/evidence.
