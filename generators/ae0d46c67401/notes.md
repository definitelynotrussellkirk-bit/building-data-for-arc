# Working notes: ae0d46c67401

## Accepted rule

The selected canonical authority is the square-grid overlay of the input and its
main-diagonal transpose. Each nonzero source at `(r, c)` remains in place and is
copied to `(c, r)`. The authority was not edited and is pinned by
`RULE_HASH = "2b970065d6a3"`.

## Baseline findings

Baseline version `2.0.1` generated only above-diagonal sources even though the
canonical inputs include below-diagonal cells. Its validator therefore rejected
all three labeled canonical inputs. It also advertised dead or unprobeable
controls, mixed ordinary and negative textures, and omitted the authority hash.
The interrupted before battery retained these failures under `checks/before/`.

## Review repair: version 3.0.0

The replacement samples one occupied endpoint from each selected transpose orbit,
with the other endpoint empty. Five controls are exact and recoverable from pixels:
`size`, `cells`, `palette_size`, `side_profile`, and `anchor_corner`. Unknown or
invalid controls fail closed. Production inputs cover both sides of the diagonal,
canonical 5×5/6×6 scales in every band, 3–9 cells, and 1–3 source colors.

The four-position teaching schedule is `mixed, above, mixed, below`. Thus every
four consecutive pairs contain two mixed-side examples, and every leave-one-out
query rotation retains a witness against both one-sided reflection shortcuts.
Palette scheduling similarly leaves a multi-color witness after any rotation.

## Reusable probes and tests

`workspace/reference_probe.py` provides an independent Python oracle, canonical
pair loader, pixel-level axis observer, generator loader, and public Racket
adapter. `tests/test_generator.py` checks canonical acceptance, exact joint
overrides, validation failures, deterministic breadth, canonical-profile floors,
all cyclic schedule starts exercised in the test range, semantic witnesses,
mutation rejection, RNG purity, and authority parity.

Final focused evidence includes 55/55 portable task tests and a production-sampler
census of 300 lessons / 1,200 leave-one-out rotations / 1,200 unique inputs with
zero materialization errors, scoring errors, or declared-rival ambiguities.

## Limits

The generator intentionally supports sparse inputs with empty transpose targets;
it does not teach collision precedence for both endpoints of one transpose orbit.
The declared competitors are a finite adversarial set, not a proof of unique
program induction. Training approval remains a catalog decision outside this
review.
## Current reviewer considerations

Source SHA-256: `9568dff1aa64072e3227f54d947d61cda7373d74252d3986e0cd37bed4cb218b`.

# Decisions for `ae0d46c67401`

## D1 — Preserve and pin the selected authority

The canonical executable rule overlays the input with its transpose. It matches
all labeled canonical pairs and passed rule smoke, Racket lint, and exact authority
synchronization, so changing Racket would add risk without fixing the generator.
The generator now pins normalized `RULE_HASH=2b970065d6a3`.

## D2 — Sample transpose orbits instead of one triangle

Baseline `2.0.1` placed sources only above the main diagonal. The original reason
for that restriction is unknown, and it contradicted canonical inputs containing
below-diagonal sources. Version `3.0.0` samples one endpoint from each selected
transpose orbit and leaves the paired target empty. This constructively creates a
visible copy operation while preventing collision ambiguity.

Rejected alternatives were (a) retaining above-only generation and merely
loosening `self_check`, which would preserve the teaching shortcut, and (b)
allowing both endpoints of an orbit, which would introduce untested overlay
precedence not needed by the canonical examples.

## D3 — Replace decorative metadata with five exact controls

The old surface included dead helpful textures, negative textures inside the
ordinary domain, and an unprobeable palette declaration. The reviewed surface is
`size`, `cells`, `palette_size`, `side_profile`, and `anchor_corner`. Every value
is pixel-observable, feasible joint requests are exact in every band, invalid and
unknown requests fail closed, and no incompatibility exceptions are needed.

## D4 — Make two-sided evidence rotation-safe

A single mixed-side witness would teach the rule in production order but could be
removed by leave-one-out query rotation. The selected four-step schedule is
`mixed, above, mixed, below`, so every four consecutive pairs contain two mixed
examples. Any one held-out pair leaves at least one example that refutes both
`above_only` and `below_only`. The palette schedule likewise leaves a multi-color
example to refute the single-color mirror rival.

Rejected alternatives were increasing lesson size, making every sample mixed, or
using stochastic resampling. The chosen schedule keeps one-sided diagnostic
profiles while making the guarantee simple and testable.

## D5 — Keep canonical-scale anchors in every band

Every 20-draw window re-enters 5×5 or 6×6 support, including hard difficulty,
while other positions cover sizes through 14. This preserves canonical proximity
without collapsing distribution breadth. The strict profile gate measured 17/60
exact-profile and 19/60 envelope hits with all three canonical inputs accepted.

## D6 — Declare executable rivals and independent probes

The semantic contract names identity, transpose-only, above-only, below-only, and
single-color alternatives. `workspace/reference_probe.py` deliberately does not
reuse generator implementation helpers: it loads canonical pairs, computes an
independent oracle, observes axes from pixels, and can query the public Racket
authority. The portable suite covers canonical support, exact controls,
determinism, cyclic schedule behavior, witnesses, mutation rejection, RNG purity,
and authority parity.

## D7 — Use measured curriculum evidence, not label correctness alone

The final production census materialized 300 lessons (100 per band), 1,200 pairs,
and all 1,200 leave-one-out rotations. It found 1,200 unique inputs, no
materialization/scoring errors, and zero ambiguity against the declared rivals.
This is finite evidence, not a universal induction proof.

## D8 — Keep audit targets findings-only

`fd2ddef14b82` has ignored exact controls and a retained example where an ordinary
BFS rival matches the key/door authority; `6a289c5b0897` showed no issue under its
portable suite, finite schedule probe, and authority-sync check. Neither audit
target was modified.

## Remaining limitations

The reviewed generator intentionally excludes occupied transpose pairs and main-
diagonal sources, so it does not teach collision precedence or no-op diagonal
cases. The semantic rival set is finite. Catalog approval and train safety remain
outside this review.
