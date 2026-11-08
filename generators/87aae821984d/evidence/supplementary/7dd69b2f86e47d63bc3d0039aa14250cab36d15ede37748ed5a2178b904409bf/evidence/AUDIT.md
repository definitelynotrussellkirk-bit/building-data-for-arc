## 87aae821984d

**Supplementary audit replay — existing finding reproduced, not broadened or cleared.** Ticket `ticket-d0dc88ccac0dd203` verified the pinned generator SHA-256 `15a3c012540738dee4d3d31f9ffe68b8eebfcdfda23836b0cc4c3be0fd9b99b8`, rule hash `6f52927247b0`, audit-index hash `ecadc958b61f14d95b3dd176ffa904f6bd19797facddccaf2d88b6f024d49538`, audit-record hash `9d9e39283923932aeb7e401e4be62a69c944f7e4945749ca5037437317d00c8b`, and all 14 retained asset hashes.

The documented generated witness `generate(87002026, 0, difficulty="medium", n_4_cells=2)` reproduced byte-for-byte. `self_check` returned `[]`; observed axes remained 9×9, two yellow counters, and `shape_kind="span_3x3"`. Fresh live Racket and the current Python mirror reproduced the retained 3×6 output, while the bbox-only rival reproduced its retained 3×3 output and still disagreed.

A bounded recheck of medium default sample indices 0–3 reconfirmed the coupled schedule `(3×3→1, 2×3→2, 3×2→3, 2×2→4)` and the rival matched all four default outputs. This replay does not rerun or extend the retained 28-draw/64-rotation census; those assets were hash-verified only. The existing distribution-shortcut audit therefore remains unresolved. Evidence: `checks/tickets/ticket-d0dc88ccac0dd203/audit_replay.json`.
