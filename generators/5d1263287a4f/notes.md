# Working notes: 5d1263287a4f

## Current decision — 2026-10-23

Baseline generator `2.0.0` (`e88a731c55edf29fc56e15aaf9c56d0f379c262f63d569caeab9af498822339d`) preserved the canonical crop-left rule but sampled shortcut-breaking panel layouts probabilistically. The retained audit shows that the canonical examples admit the simpler “return the rightmost third” rule, so a three-demonstration lesson could still fail to identify position.

The production repair is generator `2.1.0` (`5013bec072129d3bd32c38f5eca1be22561aa9834b12a3c6218a3e7d81fcc7e0`):

- Default `panel_layout` now follows the four-slot cycle `right_mirror`, `all_same`, `both_mirror`, `middle_mirror`. Every cyclic three-example demonstration window contains a case where the rightmost panel differs from the canonical output.
- Explicit `panel_layout` overrides remain exact. The scheduled value is still recorded through the normal keyed-draw provenance as a singleton choice.
- Mirror-seam layouts normally keep the source right edge background, preserving the default three-component fragmentation envelope. Default 2×2 draws use three colors when four cannot fit that seam constraint.
- The declared `rightmost_panel` rival, witness, and `lesson_identifiable` hook make the teaching obligation executable rather than implicit.
- The canonical Racket source and rule hash `92f6a0f9f7b3` are unchanged.

A separate proposed prototype under `workspace/parametric/` adds the episode-fixed parameter `output_transform = identity | horizontal_mirror | vertical_flip`. `identity` is byte-for-byte the canonical Racket program. Demonstration and query counts are independent; inputs are retained only when all three settings produce distinct outputs; public exports redact query labels/private metadata, use IDs derived only from exact visible bytes, are sorted by public ID, and reject duplicate visible payloads.

## Retained evidence

- `checks/final-task-tests-v2/result.json`: 35/35 focused tests passed.
- `checks/final-selfcheck/result.json`, `checks/final-rule-smoke/result.json`, and `checks/final-dist-gate/result.json`: production structural, Racket, and distribution checks passed.
- `checks/after-override-v2/result.json`: all 31,410 override draws passed.
- `checks/after-diversity/result.json`: diversity gate passed.
- `checks/after-semantic-schedule/result.json`: every query rotation in the complete four-slot schedule was identifiable.
- `checks/parametric/5d1263287a4f-output-transform-v1/report.json`: three fixed settings, four demonstrations plus four distinct queries per setting, 72 protected Racket applications, exact labels, identifiable demonstrations, setting-sensitive queries, sorted/deduplicated public batch.

## Limits and next action

The prototype evidence retains one episode per setting and is bounded rather than exhaustive. It is proposed authoring evidence, not catalog approval or training admission. An explicit 2×2, four-color, mirror-seam override may use one foreground seam cell to honor the declared override; default tiny draws avoid that case, and semantic correctness remains intact. The next useful action is maintainer assessment of the `2.1.0` production repair, followed by a separate decision on whether the `output_transform` prototype should enter a broader authoring queue.
