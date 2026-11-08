# Color-role support probe

The selected implementation is `../generator.py`. This directory contains an
authoring probe, not an alternative selected generator.

From the repository root, using the packet's configured Python:

```sh
../.venv/bin/python3 generators/34f8510e39d0/workspace/probe_color_roles.py \
  --all-profiles --indices 8 \
  --out var/color-role-probe/report.json \
  --witness-inputs var/color-role-probe/inputs.json
```

The default seeds are 0, 1, 7 and 99. Five explicit profiles crossed with three
bands, four seeds and eight indices give 480 calls; the report also counts unique
inputs so repeated difficulty/profile settings are not mistaken for diversity.
Without `--all-profiles`, it audits the default teaching schedule. The tool
records source hashes, canonical fit of a size-only rival, geometry matching,
lawfulness, exact replay settings, and minimal/generated color-role exchanges.

Generated and counterfactual labels in this CPU probe are **Python mirror
predictions**. Obtain selected Racket labels with the public `arcpuzzles apply`
command printed in the report; in a packet, run it through `review.py run`.
The report and witness destinations must be new, distinct paths. The CLI rejects
equal resolved destinations before scanning or writing. `--generator-source`
supports an explicitly retained historical generator for before/after checks;
it does not select that generator for production.

The minimal 3x7 witness is lawful under `self_check`, but not strict-canonical
in canvas dimensions. Generated matched-role witnesses retain canonical-sized
profiles. Color roles are exchanged in the input and relabeled; output colors
must not be permuted as if the rule were color-equivariant.

Run all selected tests with the supported staged command from the outer root:

```sh
WORK/.venv/bin/python3 review.py check --stage task_tests --phase after \
  --timeout 600 --out ../checks/new-task-tests
```
