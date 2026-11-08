# Working notes: d546d87fec58

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `6a6a48ba29262b038b94c5d3dc9693704bd2283b5551427b78ff2238706e0762`.

# Decisions

## D1 — Anchor canonical scale without replacing the broad distribution

The baseline could not produce the canonical 16×16 / 8-or-9-input-color profile in
several difficulty bands because its difficulty-shaped size and palette draws made the
joint profile impossible. I added a one-third curriculum anchor: absent exact caller
overrides, one of three keyed profile choices uses size 16 and latent palette size 7
or 8; the other two preserve the original 10–20 and 2–8 broad ranges. Exact overrides
still pass through the original validators.

I rejected a 75% anchor after the full distribution gate measured a modal-background
object-count median of 1 versus canonical 9, outside the allowed 3× band. That failed
iteration is retained under `checks/after-v3/`. One-third support satisfies the pinned
profile floor in every band while the morphology regression keeps the 120-draw median
at or above 3.

## D2 — Declare the real semantic rival rather than inventing new rule branches

Every usable canonical example is also solved by the cheaper `rot180_only` rule, so
frequency or output parity alone cannot establish that fallback mirrors are taught.
I declared `fallback_required` as a witness and `rot180_only` as the semantic rival,
canonical shortcut, and lesson competitor. `strict_canonical_like` delegates to the
existing exact scene validator with `MIN_STRICT_FRAC = 1.0`.

This follows retained decisions GNOTE-000677 and GNOTE-000678: generate a fully
horizontal/vertical/180-symmetric latent texture and exercise fallback branches only
where all visible counterparts agree. I did not introduce conflicting mirror values;
GNOTE-000679 explicitly rejects that unsupported hypothesis.

## D3 — Schedule profile coverage at lesson scale

Uniform per-instance profile sampling passed witness-frequency checks but produced
2/300 assembled lessons where all four visible examples used the rotate-180 profile.
I changed only the default profile selector to a three-instance cycle:
`rot180`, `horizontal_fallback`, `mixed_fallback`. Every four-consecutive-demo window
therefore contains a fallback witness. Exact `mask_profile` overrides remain supported.

The final implementation records the scheduled value through
`GenCtx.draw_choice(label, (scheduled_value,))`. A first attempt returned the cyclic
value directly; the 11/12 battery exposed that it omitted keyed provenance. That
failure is retained under `checks/after-final/`, and the corrected override stage is
under `checks/override-final/`.

## D4 — Keep canonical authority immutable

No Racket program, canonical row, base solution, rule hash, or frozen retained fixture
was changed. `RULE_HASH` remains `5c0ceb196b2a`. The final changes are limited to the
selected generator plus two task-local test-support files.

## D5 — Preserve the immutable legacy test and adapt only the portable runtime view

The retained task fixture assumes a historical `generators/<task>/data` path, while
source-bound portable tests copy the pinned authority to runtime-root `data/`. I did
not edit the frozen fixture. A task-local `conftest.py` creates a relative alias only
inside an `ARCPUZZLES_HOME` runtime, verifies the canonical snapshot first, and fails
if an unexpected target already exists. This is a compatibility adapter, not a second
authority source.

## D6 — Supported domain and remaining limitations

The generator intentionally remains the retained rectangular corner-mask family:
one to three 2–4-cell-side occlusions, grid sizes 10–20, and latent palettes 2–8. It
does not claim arbitrary disconnected masks, arbitrary mask color, or priority
semantics when mirror values conflict. The final census is finite and checks only the
declared rival callables; 300 clean lessons are strong regression evidence, not a
proof against every possible shortcut. Query start rotations are covered by all six
requested residues, but the training assembly policy itself remains four consecutive
demos and one query.
