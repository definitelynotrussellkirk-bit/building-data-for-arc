# Working notes: 79a30e61d332

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `02b862a0f357a8ac34aa72ead821990192619899851ff0182dd16d0e6b6c85b0`.

# Decisions — 79a30e61d332

## D1: Preserve canonical Racket authority

Keep `RULE_HASH = 0b623466d0bd` and the existing canonical Racket program unchanged. The canonical rule already matched all four labelled pairs; the repair concerned the Python generator's public boundary and distribution, not rule behavior. Rewriting a behaviorally equivalent Racket program would add authority risk without improving the task.

## D2: Validate public call scalars before generation

Require `seed` to be an exact integer (not bool/float/string), `sample_index` to be an exact nonnegative integer, and `difficulty` to be `None`, `easy`, `medium`, or `hard`. Reject unknown or malformed values rather than silently treating them as defaults. This decision follows the strict detector's concrete reproductions and is covered by test-first red/green receipts.

Rejected alternative: relying on downstream coercion or `gen_ctx` errors. That produced inconsistent behavior—some malformed values were accepted, while others failed later for incidental reasons.

## D3: Retain the canonical dense lattice and honest exact controls

Keep the 17×25 dense 4×6 lattice, fixed color roles, nonempty 3×3 tiles, and only three advertised exact axes: `layout_profile`, `n_keys`, and `key_cells`. The generator can construct every legal combination of those controls and reports them through `observe_overrides`.

Rejected alternatives: advertising fixed dimensions/palette labels as configurable axes, adding sparse/empty tiles, permuting semantic colors, or changing key orientations. Those would either be false controls or broaden the domain beyond the canonical authority.

## D4: Teach exact masks rather than row summaries

Every sample includes a non-key tile with the same three row-occupancy totals as the key but a different exact 3×3 mask. This directly refutes the strongest compact canonical shortcut found, `row_sums_only`, instead of depending on a lucky random distractor.

Rejected alternative: matching only total area. It is weaker and does not isolate the exact-mask distinction. Randomly hoping for a row-sum collision made lesson identifiability seed-dependent.

## D5: Use 3–6 keys and explicit horizontal/vertical/mixed profiles

The baseline's exactly-two-key, one-axis manifold admitted “first two keys,” “seed lines only,” and axis-only shortcuts. The replacement schedules layouts that include more than two exact keys, horizontal and vertical bridges, and bridges between non-seed keys. “Mixed” requires each axis to contribute at least one observable bridge tile not covered by the other axis.

Rejected alternative: a merely nominal mixed layout in which all bridge tiles overlap. A rotation probe showed that an axis-only rival could survive such examples.

## D6: Keep a three-demonstration deterministic curriculum

Cycle `horizontal → vertical → mixed` by sample index, independent of seed and difficulty, with `EXAMPLES_NEEDED = 3`. Any consecutive three production demonstrations cover the branches; task tests and the larger census also check arbitrary held-out query positions against declared rivals.

Rejected alternative: unconstrained random ordering. It did not guarantee that every lesson supplied all distinguishing witnesses. The evidence remains finite rather than a universal induction proof.

## D7: Restore canonical topology with a sparse anchor, not a global restriction

For hard-band samples only, activate a topology anchor when `sample_index % 10 == 5`. It uses connected key/collision/filler masks and exactly four singleton distractors, reproducing the canonical `(24 object components, 4 singleton markers)` support. All other samples retain the ordinary mask sampler.

Rejected alternatives:

- suppress the structural detector warning, which would hide a real support gap;
- force connected masks globally, which would erase lawful disconnected-symbol diversity;
- copy canonical grids, which would add memorization rather than compositional support.

## D8: Difficulty changes composition and density

Easy uses 3–4 keys and 3–4 occupied key cells; medium 4–5 keys and 5–6 cells; hard 5–6 keys and 7–8 cells. This makes the knob observable while staying on the canonical manifold. It is not claimed to impose a monotone cognitive difficulty ordering.

## D9: Keep reusable independent probes and portable tests

Retain task-local tests plus `workspace/reference_probe.py` for canonical loading, exact-mask introspection, rival outputs, Racket parity, and source hashing. Portable helpers locate the repository/runtime rather than assuming a fixed `parents[...]` depth.

## D10: Propose `bridge_scope` only as a separate parametric prototype

Use two rule settings chosen once per episode:

- `all_pairs` (canonical/default): every aligned key pair contributes bridges;
- `seed_only`: only pairs containing the color-8 seed contribute bridges.

This is the smallest nearby semantic parameter that preserves the family's objects and reasoning structure while changing a meaningful relational choice. The sampler guarantees a non-seed bridge witness, and all six retained demonstrations distinguish the two settings.

Rejected alternatives: a bridge-color parameter adds little reasoning value; horizontal-only versus vertical-only requires a more restrictive episode sampler and a larger interaction matrix; key count, mask density, and layout are input parameters rather than executed-rule parameters.

Status: prototype/proposed only, under `workspace/parametric/`; not production behavior, not canonical authority, and not training approval.

## D11: Retain exact failures and compress only oversized evidence losslessly

Keep the v4.0.0 baseline, the post-scalar structural failure, focused red tests, and final green evidence. Compress the 25,503,059-byte census with gzip, preserve its exact raw SHA-256 and size in `checks/lesson-census-final-v402.compression.json`, and retain the readable summary separately.

## Prior evidence and limitations

Prior-return lead: `review-6f4de424444f2bc1:v0001`. It informed where to look, but current decisions were revalidated on this packet's pinned source.

Known limits: declared rivals are not exhaustive; geometry and color roles remain fixed; non-key masks may repeat; adjacent keys can produce no intervening bridge; and the deterministic constructive fallback may be slower than rejection sampling even though all advertised combinations are supported.
