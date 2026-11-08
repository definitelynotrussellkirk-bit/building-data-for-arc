# Working notes: 329f699c3e09

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-25 review decision

- **Base defect repaired:** ordinary sampling could place an unrelated distractor on a reflected magenta destination, while the canonical rule overwrote that cell cyan. The sampler now reserves every reflected destination before distractors are placed, and `self_check` rejects occupied or out-of-bounds destinations.
- **Canonical default preserved:** `paint_reflections` returns the exact catalog Racket program byte-for-byte.
- **Native family added:** `probe_first_hit` reflects each source to an input-derived probe, scans outward from that probe, and recolors the first-hit object color cyan.
- **Teaching shortcut repaired during final self-review:** the first sampler could also be explained as “recolor the opposite half.” Every scene now has a selected-color clone on the source side and a substantial non-hit object on the probe side. The correct global color-selection rule changes the clone and preserves the non-hit object; both the far-side-all and hit-side-only rivals now fail every sampled grid.
- **Current evidence:** 35 focused tests; 100 bounded seed/count jobs over 800 grids; both named shortcut rivals rejected 800/800 times; protected-Racket authoring preflight; causal `skip_a` witness; 16 verified one-query public projections; and shared first-turn privacy checks all passed.
- **Limit:** this is reviewer-ready source-bound evidence, not owner qualification, acceptance, universal uniqueness, or training admission. The next owner action is exact-source integration followed by fresh native qualification and acceptance.
