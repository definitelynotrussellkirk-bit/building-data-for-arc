# Working notes: c4f6a0585dbf

## Current decision — 2026-10-23

- Generator `3.2.0` addresses the retained palette-authority audit by fixing every port and target marker to literal color `4`. `palette_kind` and the former palette texture aliases are rejected; `self_check` now rejects recolored non-`{0,1,4}` inputs plus missing, boundary, excess, or non-port template holes. The canonical Racket source and `RULE_HASH = d401b3cd92ff` are unchanged.
- Focused repair evidence: `WORK/checks/canonical-repair/c4f6a0585dbf-literal-port-v1/result.json`. The repaired seed-13/index-5 control is lawful and changes under Racket; `no_targets` and `full_grid` remain declared identity boundaries; the old warm alias and a `4 -> 2` recolor are rejected.
- Proposed parametric extension: `workspace/parametric/prototype.py` varies `min_visible_ports` once per episode over `{2,3}`. Setting `2` is byte-for-byte canonical; setting `3` changes only the one visible-port guard. Each episode has three demonstrations and four distinct queries.
- Retained parameter evidence: `WORK/checks/parametric/c4f6a0585dbf-min-visible-ports-v2/report.json`. Both paired settings use the same seven inputs, every demonstration rejects the rival, every query changes, all ten canonical labels reproduce, and public outputs use exact visible bytes/full content IDs.
- Bounded adversarial evidence: `WORK/checks/parametric/c4f6a0585dbf-adversarial-v1/result.json` covers 238 generated grids, extreme integer seeds, exact integer/color constraints, 14 fresh Racket parity labels, 14 rival labels, public masking, and duplicate-visible-payload rejection.
- Limits: the parameter sampler is an isolated lawful subset, not a production generator interface. Evidence retains two main episodes and one additional paired seed; it does not establish exhaustive placement coverage, approval, or training admission.
- Next useful action: maintainers can separately decide whether `min_visible_ports=3` is worth integrating as an opt-in authoring axis after reviewing the bounded lesson evidence.

Imported associated notes retain their original evidence and timestamps in `evidence/associated_notes.jsonl`; this section supersedes their palette-alias recommendation for current source.
