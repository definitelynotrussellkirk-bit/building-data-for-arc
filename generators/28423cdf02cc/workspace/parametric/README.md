# Proposed stamp-rotation episodes

This task-local prototype retains the source task's object roles: read the full
asymmetric top-left 3x3 template, find the blue marker centers, and copy the
template at every center while preserving the divider and source template.

One parameter changes the executed rule: `quarter_turns` is a clockwise rotation
of each **copied** stamp, with allowed values `0, 1, 2, 3`. The canonical default
is `0`; its Racket source is byte-for-byte the selected canonical program.
The original source template stays in its original orientation for every setting.
The alternative programs change only the template lookup used during stamping.

## Run

From the outer extracted packet directory, after creating the environment described
in `WORK/WELCOME.md`:

```bash
.venv/bin/python review.py run "$PWD/.venv/bin/python" \
  generators/28423cdf02cc/workspace/parametric/stamp_rotation.py \
  --seeds 0 17 --bands easy medium hard --turns all \
  --out ../checks/parametric/rotation-suite
```

Use a new output directory for every run. `--turns auto` chooses one setting
deterministically from each episode seed; `--turns 0`, `1`, `2`, or `3` pins it.
All four pairs in an episode use that setting. Settings never change input draws:
the same seed, band and start index produce the same inputs for all settings.
The CLI chooses start index `seed % 5`; the Python API also accepts an explicit
nonnegative `start_index`. It always emits three demonstrations and one query.

## Evidence and visibility

- `public/episode_NNN.json`: ordinary ARC challenges, with demonstration outputs
  and query inputs only. They contain no parameter, seed, rule, or query answer.
- `private/episode_NNN.json`: fixed parameter, seed, accepted sample indices,
  exact Racket text/hash, query answers, source hashes and setting comparisons.
- `rules/`: the four materialized Racket programs.
- `parameter-witness.json`: one lawful input and its four distinct Racket outputs.
- `report.json`: bounded coverage, canonical parity, runtime identity and hashes.

Every output is obtained by executing the included Racket bridge. The focused
tests independently check the rotated stamp's coordinate formula; a Python mirror
does not supply labels. The prototype verifies all four canonical outputs at the
default setting and checks each alternative setting against each saved episode.

`assess_settings` is a small reusable diagnostic for future authoring work. Feed
it the executed outputs for each proposed parameter setting on the same four
inputs. It checks the normal query and all four possible query holdouts,
distinguishing a refuted setting, an answer-equivalent surviving setting, and a
survivor that changes the query answer. The tests include both genuine ambiguity
and equivalent-setting cases so a zero ambiguity count is not confused with
parameter identification.

## Constraints and limits

The canonical generator's lawful input constraints are unchanged: a full 3x3
template with eight distinct dihedral orientations, 3–6 nonoverlapping markers,
the gray divider, and its existing size/palette bounds. Full asymmetric templates
make the four rotated outputs distinguishable. Complete nonoverlapping stamps
ensure that a distinguishing template cell cannot be clipped or hidden.

This is a **proposed prototype**, separate from canonical `generate(...)`, the
selected rule and approval records. Finite checks cover the four declared
parameter settings; they do not prove unique induction against arbitrary programs
or authorize model-training admission. The emitted manifest says so explicitly.
