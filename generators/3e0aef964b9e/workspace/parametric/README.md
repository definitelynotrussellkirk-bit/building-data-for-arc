# Proposed output-policy prototype

**Status: proposed, unapproved, task-local prototype.** This does not change the
selected canonical generator, Racket rule, approval hash, or production API.

The invariant reasoning is to identify the strict modal background, consider
both foreground role assignments, build 8-connected candidate objects, compute
their canonical pixel-corner convex-hull background gaps, and choose the unique
positive gap whose cell count equals the total donor-colour cell count.

Two parameters are fixed once per episode:

| Parameter | Allowed values | Executed output behavior | Canonical default |
|---|---|---|---|
| `donor_policy` | `move`, `copy` | Clear all donor cells, or retain all donor cells | `move` |
| `fill_policy` | `donor`, `target` | Fill the selected missing hull cells with the donor-role or target-role colour | `donor` |

Default `move` + `donor` returns the exact canonical Racket text without any
substitution. Alternatives retain selection verbatim and modify only its final
clearing/filling expressions. Role colours come from the scene; numeric colour
IDs are not parameters. No input constraints depend on these policies: every
lawful scene has positive donor/gap counts and distinct background, donor and
target colours, so each input distinguishes all four outputs.

## Exact command

From the outer extraction folder containing `review.py`, use a fresh destination:

```bash
python3 review.py run python3 generators/3e0aef964b9e/workspace/parametric/prototype.py --seed 73 --episodes-per-setting 1 --out ../checks/parametric/episodes
```

The wrapper selects the included offline Racket and runs from `WORK/repo`.
Python 3.12+, NumPy/Pillow (selected generator dependencies), and the included
Racket bridge/prelude are required. Tests additionally require pytest:

```bash
python3 review.py run python3 -m pytest -q generators/3e0aef964b9e/tests/test_parametric.py
```

`build_episode(seed, episode_index)` selects one setting through a stable SHA-256
mapping of the seed, then holds it fixed for all three demonstrations and the
query. The CLI covers all four settings by deterministically finding the first
seed that selects each setting in each 1,024-seed window, starting at `--seed`.
It calls the native seed-selecting builder and fails if a setting is absent
from that bounded window. Explicit `setting=(donor_policy, fill_policy)` is also
available for same-input authoring comparisons. Sample indices are `4*episode_index` through
`4*episode_index+3`. Policy choice never changes the input draw. Difficulty is
optional and forwarded unchanged to the selected generator.

All chosen and rival outputs are executed through `RacketBridge`. The public
`strip_rule_wrapper` helper removes only the outer `rule!` registration form;
the selected canonical program is already a self-contained `(lambda (g) ...)`
with local dimensions and needs no shorthand conversion. The general
`wrap_rule` route was tried but its `scripts.comment_solutions` import is absent
from this extracted repository; that failed attempt is retained in the receipts.
Each episode must refute all three alternative policy settings on demonstrations
alone. Query answers are never used to decide identifiability. The canonical
default is also checked against the selected generator's Python mirror; the
focused tests check all six canonical pairs against authoritative Racket.

## Evidence and separation

The CLI emits one complete episode per setting (or 1–8 per setting when requested),
four exact materialized Racket files with SHA-256 hashes, selected generator and
prototype/runtime source hashes, replay seeds and indices, demo-only rival
refutation receipts, and one same-input four-output difference witness.

Only `public/` is model-visible: files contain exactly `train` inputs/outputs
and `test` inputs. `private/` contains parameters, query answers, references,
hashes and replay metadata. Never give private files to the solver. Public file
names contain only opaque sequential episode numbers.

Retained command/output receipts live under `WORK/checks/parametric/`; the
exact actual argv, working directory, exit and evidence paths are recorded in
`command-records.json`. Evidence is source-bound and must be regenerated if
the selected generator or dependencies change.

## Finite limits

This extends only the selected generator's existing constructive input manifold;
it adds no new geometry, palette, donor-count, or layout controls. The prototype
checks only the four declared policy rivals, not all conceivable programs or
the canonical generator's broader shortcut family. The default CLI census is
four episodes, twelve demonstrations and four queries. A separate witness
compares all settings on the exact same input. It is bounded authoring
evidence, not universal seed coverage, independent curriculum certification,
training admission, or approval of alternative Racket rules. The CLI refuses to
overwrite an existing evidence directory. Canonical output-tail changes fail
loudly and require a new design review.
