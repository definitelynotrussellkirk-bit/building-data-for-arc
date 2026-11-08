# Working notes: 56e5ade4e829

## Review repair — assignment `review-7e59c84bf90dd5ed`

No prior review index existed for this selected task, so no earlier return was used as evidence or as a patch source. The current pinned generator, canonical row, selected Racket source, and fresh before battery were the starting point.

### Reproduced baseline defects

- Missing canonical `RULE_HASH` and selected-source comment drift.
- Advertised overrides were ignored; the before override matrix reported 32,568 mismatches.
- No executable semantic/lesson contract, despite canonical examples lacking the marker-3 intersection branch.
- Weak validation and no guaranteed per-lesson teaching coverage.
- Hard-band canonical-profile support was absent in the small profile probe.

### Repair

- Replaced retry-based placement with deterministic connected-polyomino construction and strict validation.
- Restricted default dimensions to exact canonical profiles and made all four declared axes exact and observable.
- Added partial-overlap and strict-subset relations while requiring distinct intersection, union, and XOR crops.
- Added a five-demo/one-query period-three curriculum, explicit witnesses, the canonical-fitting `ignore_intersection_marker` rival, and query-rotation identifiability checks.
- Added task-local regression tests and `workspace/reference_probe.py`, an independent geometry/rival/schedule/Racket-parity audit.
- Synchronized selected `target_code` to the unchanged canonical Racket text; executable semantics did not change.

### Intermediate failure retained

The first period-three implementation used a linear seed phase. Under a sampler advancing seed and sample index together, each difficulty band collapsed to one control branch. The failing three-case regression and the 120-sample-per-band audit are retained under `checks/tdd-red/schedule-alias-red.log` and `checks/independent/audit-python.json`. A SHA-256-derived seed phase fixes the algebraic alias; final evidence is in `audit-python-v2.json` and `audit-racket.json`.

### Final limits

Finite tests establish behavior only for the declared domain and declared rival. They do not prove unique induction against every possible hypothesis. The lesson order is intentional, but all six query rotations were also tested so the current downstream assembler may rotate queries safely.
## Current reviewer considerations

Source SHA-256: `9ba88672ca5b9dea4a4ca9b7505365f192220b69b08aef1cddaef7599b4629f6`.

# Decisions for `56e5ade4e829`

## D1 — Preserve the canonical Racket behavior

**Original rationale:** unknown; the selected rule already matched all five canonical labelled pairs and the rule smoke stage passed.

**Decision:** leave executable behavior unchanged. The only authority-file edit removes explanatory comments from selected `target_code` so it is byte-for-byte aligned with the already-selected canonical/raw source.

**Alternatives considered:** rewrite the rule in Python; change marker meanings; broaden behavior for malformed grids. All were rejected because labels must remain sourced from the existing Racket authority and no semantic defect was reproduced.

**Probe/failure mode:** canonical parity and authority-sync checks. Remaining limitation: equality of tested outputs does not prove arbitrary malformed inputs have intended semantics.

## D2 — Use exact canonical dimension profiles

**Original baseline:** independent random ranges produced some plausible sizes but missed hard-band profile support.

**Decision:** default dimensions cycle through `(8,10)`, `(8,11)`, `(9,12)`, `(9,13)`, and `(10,12)`, the exact canonical profiles. Exact `grid_h` and `grid_w` overrides remain independently selectable across their lawful ranges.

**Alternatives considered:** retain wider ranges, or lock every band to one profile. Wider ranges spend training mass off the observed task domain; one profile would create a size shortcut and reduce nuisance variation.

**Probe/failure mode:** profile-floor 60/60 and override matrix. Limitation: exact canonical support is not evidence that the canonical empirical frequencies are optimal.

## D3 — Keep the palette structural and minimal

**Decision:** every lawful input has exactly background 0, one color-1 object, one color-2 object, and one singleton marker. Marker 3 means intersection, 4 means union, and 5–9 mean XOR.

**Rationale:** operand colors and marker semantics are part of the authority, while arbitrary extra colors would create unsupported objects and brittle parser behavior.

**Rejected alternative:** treating the marker as optional. The baseline summary called it optional, but canonical inputs always contain a singleton marker; “no 3 or 4” means XOR, not “no marker.”

**Probe/failure mode:** strict `self_check`, marker-isolation tests, and Racket parity. Malformed/multiple markers are rejected rather than assigned guessed semantics.

## D4 — Construct connected operands instead of retrying random walks

**Decision:** cache every normalized connected 3–7-cell mask that fits in a 4×4 bounding box, then sample only operand pairs satisfying the requested relation and observability constraints.

**Rationale:** constructive support terminates deterministically, exposes the legal domain for testing, and avoids hidden rejection bias from capped retries.

**Alternatives considered:** retain the baseline random-walk/retry loop; enumerate much larger shapes. The former had opaque coverage; the latter adds cost and departs from canonical morphology without a teaching benefit.

**Probe/failure mode:** task tests enumerate connectivity, size, deterministic replay, relation, and operation-output distinctness. Limitation: this finite shape bank omits connected masks requiring a bbox larger than 4×4.

## D5 — Generate both partial overlap and strict subset

**Decision:** normalized operands use `partial` or `subset`, weighted 4:1 by default. Identical and disjoint operands are forbidden.

**Rationale:** canonical examples contain four partial-overlap cases and one subset case. Both relations exercise the same rule while changing the geometry of all three set operations.

**Rejected alternatives:** partial only, which would drop a canonical mode; arbitrary overlap including identity, which can make XOR empty or collapse operation outputs.

**Probe/failure mode:** 600-sample semantic evidence observed 474 partial and 126 subset cases; independent per-band probes also saw both. Frequency is a design choice, not a learned estimate.

## D6 — Require all three operation outputs to be distinguishable

**Decision:** an operand pair is lawful only when cropped intersection, union, and XOR outputs are all different.

**Rationale:** a marker-control lesson is weak when two marker branches happen to have the same label. Distinct branch outputs make control supervision locally observable.

**Rejected alternative:** allow all nonempty overlaps. That is label-correct but can create demonstrations that provide no evidence about the marker branch.

**Probe/failure mode:** operation-distinctness tests and `strict_canonical_like`. This does intentionally exclude some lawful authority inputs; the generator targets teaching quality, not exhaustive input validity.

## D7 — Separate physical objects and isolate the marker

**Decision:** place operand bboxes with at least one completely blank separating row or column and require the marker to be Chebyshev-distance greater than one from all operand cells.

**Rationale:** the Racket object extractor must recover exactly two operand objects and one unambiguous control marker. Absolute placement is nuisance variation because operands are normalized before combination.

**Alternatives considered:** arbitrary placement with retry, touching bboxes, or embedding the marker adjacent to an object. These raise accidental connectivity/object-extraction ambiguity.

**Probe/failure mode:** strict validation and destructive mutation tests. Limitation: horizontal placement is more common than vertical placement in this implementation; this should not affect the normalized rule but is a residual visual bias.

## D8 — Five demonstrations plus one query, period three

**Decision:** set `EXAMPLES_NEEDED = 5`. Across six consecutive accepted samples, the control schedule contains XOR, intersection, and union exactly twice. Therefore removing any one item as query leaves every branch represented at least once.

**Rationale:** the canonical examples contain no marker-3 case, so the plausible rival “4→union, everything else→XOR” fits them all. Five demos are the smallest rotation-safe window for a period-three schedule: six total examples permit two copies of each branch.

**Rejected alternatives:** random control draws, which can omit a branch; three or four demos, which cannot guarantee every arbitrary query rotation retains all three branches; a fixed query position only, which unnecessarily couples correctness to assembly order.

**Intermediate failure:** the first seed phase was linear. Along `seed = base+i`, `sample_index = 17i+5`, modular cancellation locked each difficulty band to one branch. `checks/tdd-red/schedule-alias-red.log` is the failing test. A SHA-256-derived seed phase preserves local periodicity without algebraic cancellation.

**Probe/failure mode:** 648 exhaustive small-start rotations, the required-rotation gate, and 1,800 production census rotations. Limit: these checks refute the declared rival and test a finite schedule lattice; they do not prove uniqueness against every imaginable hypothesis.

## D9 — Declare only real exact controls

**Decision:** expose only `grid_h`, `grid_w`, `ctrl`, and `relation`. `None` means unset; unknown keys, booleans masquerading as integers, and out-of-range values raise `ValueError`.

**Rationale:** the baseline advertised controls it did not honor. A small truthful API is more useful to dataset assembly and audit tooling than a large decorative axis list.

**Probe/failure mode:** 68 override cases × 30 seeds × 3 bands = 6,120 accepted draws with zero findings. No incompatible combinations are currently declared.

## D10 — Add executable semantic hooks and an independent probe

**Decision:** provide strict validation, observers, branch witnesses, the canonical-fitting rival, semantic lesson scoring, and `workspace/reference_probe.py`.

**Rationale:** unit correctness is insufficient when a complete training lesson admits a wrong rule. The independent probe reimplements geometry and the rival instead of calling the generator's oracle, then optionally checks Racket parity.

**Rejected alternative:** rely only on the general distribution/diversity gates. Those gates cannot detect missing marker branches or sampler aliasing.

**Probe/failure mode:** final task tests 99/99, independent 360-sample audit, 648 rotations, and 41 Racket parity checks. The probe is task-specific by design and is not an authority.
