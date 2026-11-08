# Working notes: 974fee515740

## Review-a6774a1d00d02ab4

- **Base repair:** upgraded generator `3.0.1` to `4.0.0`. The retained source silently accepted unknown/inert overrides, did not reliably cover all operation/rotation branches, allowed color-valued controls to become singleton objects that hijacked selection, treated helpful textures as inert labels, lacked an exact Python rule mirror, and included a purported `no_overlap` fixture that still overlapped.
- **Repair:** added strict override validation, explicit operation/rotation axes, a deterministic 4x4 branch schedule, lawful source-object construction, connected color-1/color-2 controls, meaningful decoy palettes, exact `analyze`/`apply_rule` semantics, and a genuinely empty-intersection negative fixture rejected by `self_check`.
- **Canonical preservation:** `composition_order=rotate_then_combine` uses the byte-exact canonical Racket program, SHA-256 `cecae49ded2ec6fe5b5e294aa3d8de4f2b18b5f54252d71a091ffc291582d93a`.
- **Native family:** added `composition_order=combine_then_rotate`. Step A decodes both controls and boolean-combines normalized unrotated red/blue masks. Step B rotates that input-derived combined mask and renders the minimal cyan result.
- **Teaching:** the first two demonstrations deliberately use subtraction with a quarter turn and intersection with a three-quarter turn. They reject the other setting plus bounded direction, fixed-rotation, fixed-operation, and reversed-subtraction rivals.
- **Coverage:** supports independently selected 2–6 demonstrations and 1–4 prefix-stable queries; the fourth query is a distributed substantive 30x30 case. Inputs are matched across settings.
- **Evidence:** focused task tests passed; the optimized 128-seed finite audit evaluates one complete bank per seed and literal prefixes, covering 1,280 episodes / 10,240 labeled pairs with zero harmful declared-rival survivors; authoring preflight, protected-Racket wrong-order replay, and public projection checks passed.
- **Limit:** this is reviewer-ready source, not owner acceptance. The next action is exact-source native owner qualification, witness replay, and fresh acceptance after integration.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
