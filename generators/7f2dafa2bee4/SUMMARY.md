# 7f2dafa2bee4

Recolor each nonzero same-color 4-connected object by its degree in the object-contact graph: degree 0→1, degree 1→2, degree 2→3, and degree 3+→4. Canonical contact is cardinal (shared-side) contact.

Kind: `per_puzzle`. Reviewed version: `1.3.0`. Rule hash: `c4e5aa9ad5fd`.

## Reviewed contract

- The canonical Racket rule and canonical labels are unchanged.
- A period-three curriculum places degree-zero witnesses in two residues, so every four-pair window and every held-out-query rotation leaves a degree-zero demonstration.
- The declared lesson competitor `degree_zero_as_two` matches the retained ambiguous lesson but is rejected by every reviewed lesson rotation; canonical examples already refute it, so it is not misdeclared as a canonical shortcut.
- `self_check`, `rule_mirror`, semantic witness declarations, and `lesson_identifiable` are pixel-derived and deterministic.
- `workspace/parametric/` contains a proposed episode-level `contact_mode` family: exact canonical `cardinal` contact or alternate `eight_neighbor` contact, with 2–6 demonstrations and 1–4 queries.
- Parametric public turns exclude the hidden setting, rule source, and query answer; public IDs hash exactly those visible bytes.

Focused checks and protected-Racket parity are retained under `WORK/checks/`. The parametric family remains proposed authoring work until the owner explicitly qualifies and accepts it for downstream use.
