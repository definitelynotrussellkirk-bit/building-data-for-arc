# Proposed output-colour variant for 23a0c42b8a1c

**Status: proposed prototype, unapproved.** This task-local interface produces
small complete episodes. It does not replace `generate(...)`, change the
canonical rule, change a catalog kind, or confer variant approval.

## Parameter and interface

| Item | Contract |
|---|---|
| Parameter | `output_colour`, Python integer in `{8, 2}` |
| Original/default | `8`; `materialize_rule()` returns the exact canonical source |
| Episode selection | One `random.Random(seed).choice((8, 2))` draw before any pair |
| Input draws | Four original hand-authored fixtures, shuffled by a separate local seeded RNG |
| Complete episode | Three labeled demonstrations and one query |
| Python interface | `make_episode(seed)`, `public_challenge(episode)`, `write_evidence(seeds, out=...)` |
| CLI | `prototype.py --seeds 0 1 --out NEW_DIRECTORY` |

All inputs have background 0, one colour-1 marker component, and exactly two
cardinally adjacent objects of unequal sizes. Connected same-colour components
form objects. Distractors may be remote, diagonally adjacent to the marker, or
inside the selected object's bounding box. Input constraints and fixture grids
do not depend on `output_colour`. The smaller marker neighbour is selected,
only its cells are cropped, and those cells receive the episode's output colour.

Every source materialization checks the **full exact canonical SHA-256**:

`5af80c67d3907183931a179f7ff8ad18fc3c41ab97c1030589b0a4649a5ca7c7`

The production rule hash remains `5af80c67d390`. The sole permitted source
substitution is `(extract-union g objs (list target) 8)` to the same expression
with final literal `2`. Other source changes, including whitespace changes,
fail the source guard. Booleans, floats, strings, and unsupported colours fail
parameter validation.

`execute_rule` uses the included `RacketBridge`. There is no Python answer
mirror. `rule_callable` verifies the original pin after reversing the allowed
colour substitution, removes the outer `rule!` wrapper, and binds `g` around the
unchanged body. This narrowly scoped adapter is necessary because the general
`puzzle_generators.rule_wrap` imports `scripts.comment_solutions`, which is
absent from the direct packet payload layout. This exact body needs no shorthand
conversion or implicit `h`/`w` bindings. Exact rule text, executed callable text,
and both hashes are retained privately.

## Run from the outer extraction directory

Use the packet's Python environment for both the public wrapper and its payload.
The payload runs from `WORK/repo`; `--out` must name a new directory.

```bash
parametric_python="$(pwd)/.venv/bin/python"
"$parametric_python" review.py run "$parametric_python" \
  generators/23a0c42b8a1c/workspace/parametric/prototype.py \
  --seeds 0 1 --out ../checks/parametric/replay-001

"$parametric_python" review.py run "$parametric_python" -m pytest -q \
  generators/23a0c42b8a1c/tests/test_parametric_variant.py
```

`find_root(__file__)` binds canonical data to this source tree. No fixed ancestor
depth, predecessor source, sibling checkout, selected-generator import, or
Python global RNG state is required. The fixture generator is intentionally
independent of ordinary repairs to `generator.py`.

## Retained complete episodes

Paths below are relative to `WORK/`. Only the `public/episode-*.json` files are
model-visible challenges; their explicit allowlist contains `train` input/output
pairs and `test` inputs. They contain no parameter fields, seeds, reference code,
private metadata, or query answers.

| Seed | Selected colour | Public challenge | Private complete episode |
|---|---:|---|---|
| 0 | 2 | `checks/parametric/episodes/public/episode-000.json` | `checks/parametric/episodes/private/episode-000.json` |
| 1 | 8, canonical | `checks/parametric/episodes/public/episode-001.json` | `checks/parametric/episodes/private/episode-001.json` |

The shared lawful distinguishing input is retained in
`checks/parametric/episodes/private/distinguishing_witness.json`. Its cropped
L-shaped output is `[[8,8],[8,0]]` under the canonical setting and
`[[2,2],[2,0]]` under the alternative. Every one of the three demonstrations in
each episode refutes the other colour setting. The same-setting rival matches
all pairs. No parameter rival is ambiguous on these two episodes.

`checks/parametric/episodes/report.json` binds source snapshots, exact rules,
relevant runtime files, seeds, file hashes, canonical comparisons, deterministic
replays, and rival results. Private rules live under
`checks/parametric/episodes/private/rules/`; source snapshots live under
`checks/parametric/episodes/private/source_snapshot/`.

## Evidence and limits

The retained CLI execution covers **2 episodes, 6 demonstrations, 2 queries,
4 distinct authored input grids, and both allowed settings**. It performs 37
task-rule applications through Racket: 16 for the two episodes and their two
parameter rivals, 16 for exact deterministic replays, 3 for every labeled
canonical pair, and 2 for the shared witness. Bridge startup canaries are not
included in that count. All three canonical comparisons match.

| Retained command receipt | Actual outcome |
|---|---|
| `checks/parametric/red/command.json` | Initial preimplementation run: 15 missing-prototype setup errors; not semantic failure evidence |
| `checks/parametric/green/command.json` | 9 passed, 6 failed because the general wrapper requires the absent `scripts` package |
| `checks/parametric/verified/command.json` | 11 passed, 4 failed on the original tied-neighbour fixture; old source and partial evidence retained |
| `checks/parametric/final-tests/command.json` | 15 focused prototype cases passed after restricting fixtures to the declared executable domain |
| `checks/parametric/execution/command.json` | CLI exit 0; two complete episodes and deterministic replays retained |

Each receipt records actual argument arrays, working directory, source hashes,
exit status, stdout/stderr paths, and applicable JUnit/report paths. Failing
source snapshots remain alongside the corresponding failed receipts. Prototype
tests are separate from canonical generator repair coverage; no full repository
suite or production parametric acceptance is claimed.

**Known authority limitation:** the unchanged canonical tie branch calls
`top-left` on an object record. The included prelude defines `top-left` as a grid
accessor, and Racket raises `list-ref: index reaches a non-pair`. Equal sizes are
excluded for all marker neighbours, including larger candidates above a unique
minimum. The failed prototype receipt retains the original tie witness in its
source snapshot and traceback. Independent public reference execution is at
`checks/repair-authority/public-racket-result.json`; that evidence is not copied
or replaced here. The restricted fixtures do not establish working tie behavior.

This is finite evidence for two settings and two seeds on four authored grids.
Input order changes with seed; this is not a replacement input distribution.
Rival checks only address the declared output-colour alternatives and do not
prove identifiability against every possible rule. Acceptance of the canonical
repair does not approve this extension.
