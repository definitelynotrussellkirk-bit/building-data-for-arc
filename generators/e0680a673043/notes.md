# Working notes: e0680a673043

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-26 — source review and parametric family

- Repaired the ordinary generator to expose only consumed axes, validate exact scalar/override types, provide a deterministic independent rule mirror, and preserve the canonical command-header semantics.
- Added the native `rank_policy` episode family: `size_desc` (exact canonical default), `size_asc`, and `color_asc`.  Step A removes the two header cells, ranks and selects the requested object; Step B crops that selected object and applies the command transform.
- The adapter supports 2–6 demonstrations and exactly four sequential queries.  The bounded probe covers all settings and demo counts 2/3/6, forces size/color ranking to disagree, randomizes selected-object location, and includes substantive 30×30 cases.
- Protected-Racket authoring preflight and a wrong-selected-object causal witness replayed successfully.  Public projection/first-turn invariance also passed.  These are reviewer authoring results only; owner source acceptance, native qualification, acceptance, and training admission remain pending.
- `defect_lint` still reports the pre-existing behavior-equivalent beautified rule text in `shared/data/base/solutions/banks/26462ff56908/M79__e0680a673043.json` as divergent from canonical authority.  That archival bank is outside the assigned task homes; active canonical behavior and sampled execution agree.
