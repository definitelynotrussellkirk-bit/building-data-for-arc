# Working notes: 4e102ec13fc8

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `947af8f0f8a0d749857c4d3b2a83a7b60bddae3027a39271fa8410654d9fdd32`.

# Decisions for `4e102ec13fc8`

## D1 — Preserve the selected Racket authority

**Choice.** Keep the canonical program unchanged and pin `RULE_HASH = "6a515fd5e427"`.

**Original rationale.** Unknown; the baseline Python summary incorrectly narrowed the authority to a contiguous palette and one solid rectangle.

**Alternatives considered.** Rewrite the Racket rule to match the old generator, or change canonical examples. Both would discard valid authority behavior without evidence.

**Probe.** Canonical mirror comparison, Racket rule smoke, authority-sync, and task-local Racket parity.

**Failure mode/limit.** The Python mirror can be wrong; it is never used as label authority. Final parity checks use the public Racket path.

## D2 — Model arbitrary component depth instead of rectangle depth

**Choice.** Use four non-rectangular 5×5/7×7 shape families, orientation transforms, and 1–3 separated components. Onion depth is defined by repeated cardinal-boundary erosion independently per component.

**Original rationale.** The old rectangle construction was convenient but contradicted a canonical non-rectangular example and hid component semantics.

**Alternatives considered.** Random-walk polyominoes offered more geometry but made full override construction and depth guarantees rejection-heavy. A large fixed library was unnecessary.

**Probe.** Tests require every default largest component to be non-rectangular, at least four normalized shapes, depth ≥2, component separation, and Racket parity.

**Failure mode/limit.** The family remains finite, and extra components are singleton satellites. It does not claim complete coverage of connected polyominoes.

## D3 — Teach all nonzero header entries, including entries after gaps

**Choice.** Default headers contain one or two interior zero gaps, with a guaranteed gap immediately after the first palette entry. `header_gaps=0..2` is an exact observable override.

**Original rationale.** Baseline assumed a contiguous prefix although the authority filters all nonzero header cells.

**Alternatives considered.** Random arbitrary header placement could create difficult packing constraints at width 8 for four colors plus two gaps. The selected layout covers the semantic distinction constructively.

**Probe.** `contiguous_header_prefix` fits every canonical pair, while all 512 independent default samples and the exact seed-712 witness refute it.

**Failure mode/limit.** The first palette entry remains at column 0; leading-zero headers are outside the teaching grammar.

## D4 — Decouple body color from the canonical blue color

**Choice.** Use one body color from 1–8, disjoint from the header palette; defaults exclude blue and bands use disjoint color sets (`2–3`, `4–5`, `6–8`).

**Original rationale.** Canonical inputs all use blue, so a blue-only recoloring shortcut fits them.

**Alternatives considered.** Multicolor components would exercise the authority more broadly but conflict with the exact `shape_color` contract and substantially enlarge the validator/override surface.

**Probe.** `blue_cells_only` fits all canonical pairs but is refuted by every default sample. Band-difference regression prevents a recurrence of byte-identical difficulties.

**Failure mode/limit.** Bodies remain monochrome; multicolor binary shapes are not taught.

## D5 — Include multiple independently peeled components

**Choice.** Default `component_count` is 2 or 3; exact overrides allow 1–3.

**Original rationale.** A largest-component-only rule fits all canonical demonstrations because they contain one target component.

**Alternatives considered.** Multiple large components would increase visual coverage but cannot be packed for every 8×8 combination without complex rejection logic. Separated corner satellites make all exact combinations constructive.

**Probe.** `largest_component_only` fits all canonical pairs but is refuted by every default sample; the semantic gate verifies its witness 600/600 times.

**Failure mode/limit.** Satellites are singletons and therefore do not test deep secondary components.

## D6 — Replace decorative axes with six exact pixel-observable axes

**Choice.** Advertise only `grid_h`, `grid_w`, `palette_size`, `header_gaps`, `component_count`, and `shape_color`; reject unknown keys and out-of-range/non-integer values. No ordinary degenerate textures remain.

**Original rationale.** Baseline exposed dead singleton/decorative axes and negative textures as ordinary values, causing override errors and ambiguous validation.

**Alternatives considered.** Keep textures as diagnostic-only axes, or declare incompatibility combinations. Neither was needed because all 636 matrix cases are constructively realizable.

**Probe.** The strict override matrix executed 57,240 draws across three bands with 57,240 accepted, zero findings, and zero explicit incompatibility rejections.

**Failure mode/limit.** Shape family/orientation/placement are latent randomized dimensions rather than exact public axes.

## D7 — Make the grammar strict but canonical-compatible

**Choice.** Validate dimensions, ARC literals, 2–4 distinct header colors, ≤2 interior gaps, one body color disjoint from the palette, 1–3 components, no ordinary sentinel 9, and at least one depth-two cell.

**Original rationale.** Baseline accepted full-color grids and 2×2 impostors and rejected broader canonical semantics.

**Alternatives considered.** An authority-complete recognizer would admit empty headers, color 9, and arbitrary bodies; that is too broad for a high-signal training grammar.

**Probe.** All three canonical inputs are accepted; malformed/minimal impostors are rejected; 600/600 semantic strict samples and 60/60 exact-profile plus 60/60 envelope samples pass.

**Failure mode/limit.** It recognizes the documented teaching domain, not every input on which the Racket program is defined.

## D8 — Add executable semantic and lesson contracts

**Choice.** Declare three canonical-fitting rivals and witnesses, then reject any lesson where a rival fits every demonstration but changes the query answer.

**Original rationale.** Baseline had no semantic contract, so correct labels alone could not show that lessons teach the intended rule.

**Alternatives considered.** Frequency-only witnesses are insufficient because a witness can appear only in the held-out query. The lesson hook evaluates demos and query jointly.

**Probe.** Small gate: 12/12 lessons and 0/48 ambiguous rotations. Large source-bound census: 300/300 lessons, 0 ambiguity, and 0/1,200 ambiguous rotations.

**Failure mode/limit.** This is finite competitor testing; undeclared rivals remain possible.

## D9 — Retain independent review tooling

**Choice.** Add `workspace/reference_probe.py` using an independent BFS depth oracle and a portable `find_root` lookup, plus 50 task-local tests.

**Original rationale.** Future agents need a reproducible way to audit geometry, override observability, canonical shortcut fit, determinism, and band behavior without rebuilding it.

**Probe.** The probe reports 485 unique inputs among 512 draws, 0 self-check/determinism failures, and complete declared-rival refutation. The exact patch replayed in a fresh packet and the portable suite passed 50/50.

**Failure mode/limit.** The independent oracle is still Python authored by the reviewer; retained Racket parity is the authority check.
