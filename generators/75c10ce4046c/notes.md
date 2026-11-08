# Working notes: 75c10ce4046c

## 2026-10-24 review `review-7944861aa83ee6b1`

Repaired both retained audit findings in version `2.2.0`. The source and
candidate bank now includes tetrominoes and pentominoes matching the canonical
domain. `source_size`, `candidate_count`, and `matching_candidates` are typed,
consumed axes; requesting 1–5 matches among six candidates returns exactly that
count, while impossible combinations and unknown overrides fail instead of
being coerced or resampled. Placement uses an exhaustive legal-position set
with one-cell component separation.

Six focused tests cover all canonical inputs, source sizes 4/5, exact match
counts, invalid controls, and deterministic fresh returns. Protected Racket
replay checked three canonical and two generated cases against the independent
Python mirror. A bounded densest-layout probe exercised 400 cases at 14×18 with
seven candidates, source sizes 4/5, and match-count extremes 1/6; it observed no
failure. The probe is finite and does not prove every seed or packing schedule.
