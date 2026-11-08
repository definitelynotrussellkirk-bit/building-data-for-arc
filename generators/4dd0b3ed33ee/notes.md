# Working notes: 4dd0b3ed33ee

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-26 parametric review decision

Built a native two-setting family under `workspace/parametric/`.
`match_selector=first` preserves canonical program bytes exactly;
`match_selector=largest_area` keeps the header-driven four-connected-hole filter
and chooses the unique largest occupied-area member before the same cyan
boundary rendering. Inputs are matched across settings, demonstrations are
prefix-stable for counts 2–6, and every episode stores four distinct private
queries for sequential reveal.

Adversarial work found and repaired fixed density/interior/aspect, missing-cell,
rank, color, dimension, and vertical-shelf shortcuts. It also found that the
initial promotion contract used non-native field names and that the certifier
did not bind `program_sha256`; both are now regressions. The retained probe at
`workspace/parametric/adversarial_probe.py` covers 64 seeds, 2/3/6 demos,
malformed certificate/export inputs, and protected-Racket minimum/maximum
lessons. The fourth query is a substantive 30x30 boundary-touching scene.

The source-bound authoring preflight and skip-topology-filter causal witness are
reviewer-ready, not owner acceptance or training admission. Next action: owner
source review, native qualification/acceptance on exact integrated bytes, then a
separate training-admission decision.
