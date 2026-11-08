# Largest blue object — size-keyed partner family

This opt-in family preserves the canonical setting byte-for-byte:

- `mode=canonical`: find the uniquely largest blue (`1`) 4-connected object and
  recolor it orange (`7`).
- `mode=size_keyed_partner`: perform the canonical step, retain the largest
  object's measured size `s`, then find the unique blue object of size `s-3`
  and recolor that partner red (`2`).

The input grammar contains four blue objects of sizes `2,3,4,s`, where `s` is
`5`, `6`, or `7`, plus neutral gray (`8`) distractors that both rules preserve.
Thus the second target changes across examples and cannot be chosen until the
first step determines `s`. Demo counts are independently supported from 2 to 6;
all episodes contain exactly four distinct queries, including a substantive
30×30 boundary/distractor case.

Run focused checks and the protected-Racket self-audit from the packet root:

```bash
python3 review.py run python3 -m pytest \
  generators/16d18a416d57/tests/test_parametric_largest_partner.py -q
python3 review.py run python3 \
  generators/16d18a416d57/workspace/parametric/audit.py \
  --out generators/16d18a416d57/workspace/parametric/evidence/current/self_audit.json
```

The finite audit covers declared shortcuts and selected seeds/counts; it is not a
proof of uniqueness against every possible program. Native qualification and
owner acceptance remain separate gates.
