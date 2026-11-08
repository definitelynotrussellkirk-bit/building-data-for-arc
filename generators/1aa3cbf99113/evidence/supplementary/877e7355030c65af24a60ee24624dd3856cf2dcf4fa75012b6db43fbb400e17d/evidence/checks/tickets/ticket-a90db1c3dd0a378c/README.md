# Adversarial witness: total color frequency is insufficient

Status: **completed**. This ticket retains one lawful witness against one plausible shortcut; it does not claim a new safety finding.

The shortcut counts each nonzero input color across the whole grid, then paints every cell of that color red (2) when its count is at most three, or cyan (8) otherwise. It agrees with connected-object sizing whenever each color belongs to one connected object. The generator's ordinary `same_color` palette mode provides a supported way to separate those rules.

The one generated 16×16 input has a singleton and a 4×4 rectangle, both color 5, for 17 colored cells total. Its independently measured monochromatic 4-connected component sizes are `[1, 16]`; `self_check` returns `[]`. It satisfies both documented size branches and uses no degenerate texture. The pinned canonical Racket rule paints the singleton red and the rectangle cyan, agreeing with an independent connected-component implementation. The shortcut paints both cyan, disagreeing at zero-based `(row=12, col=2)`.

## Source binding and replay

Generator: `repo/generators/1aa3cbf99113/generator.py`, SHA-256 `4191b4dfb59a84201e339c9abcf3f24ce084116de9c87050a7de140bc1f263e7`. The probe uses `load_selected_generator` and checks this exact digest before generation.

Canonical rule task `1aa3cbf99113`, source `custom`, normalized rule hash `1121b582d471`; raw program SHA-256 `abed5e6da1a90f820c83ad76188bfc781bd73e84f3714c971b683ac5ad9e8b36`; executed callable SHA-256 `41baf411a6de87aeafe2e549b6f5a85b2cc084ce3ecedbe77eb710cb6c21086e`. The probe checks the rule pin before Racket execution and uses the repository's `wrap_rule` normalizer.

Seed is the ticket's full hexadecimal seed converted with `int(seed_hex, 16)`; sample index is 0. The complete supported override configuration is recorded in `receipt.json` and `probe.py`.

From packet root, the exact command was:

```text
python3 review.py run python3 ../checks/tickets/ticket-a90db1c3dd0a378c/probe.py
```

The payload's working directory was `WORK/repo`. The command exited **0**, took **3.050041 seconds** measured externally, and performed exactly one generation and one reference-rule application. The inner probe measured **2.405832 seconds**. Total authoring time was not instrumented, so the result row leaves `elapsed_minutes` null. `execution.json` records absolute working directories, argv, exit code, elapsed time, and the absence of timeout; `probe.log` retains compact stdout. `witness.json` contains input, both outputs, component cells, and the differing cell.

## Scope and existing evidence

There is one canonical row and zero canonical training/test pairs. No claim about fitting canonical examples is possible. This probe did not measure production lesson frequency, alternative configurations, or shortcut prevalence.

Current `evidence/review_index.json` already retains the source-matched `needs_triage` report `review-25485a577009d7e1:v0001` concerning missing large-object branches in easy draws. That prior report informed source inspection but was not rerun, resolved, or duplicated here. A successful witness against this different shortcut provides no clearance for the pre-existing report.

No generator, canonical rule, task notes, or root reports were edited. No supplementary `AUDIT.md` section is warranted for this completed witness ticket.
