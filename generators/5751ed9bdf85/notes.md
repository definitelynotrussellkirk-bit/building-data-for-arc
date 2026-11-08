# Working notes: 5751ed9bdf85

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `b11102ec70073d50cd748858e6f631d4be643c8c280a33feb6ef379ea2c61b38`.

# Decisions for generator 5751ed9bdf85

## D1 — Treat marker-count parity as the strongest uncovered rival

**Input choice and prior rationale.** The baseline preserved the canonical role pattern exactly: one empty frame, one one-marker target, and one two-marker decoy. The original rationale is not recorded beyond canonical fidelity and the existing notes; the practical consequence was that every canonical and generated example had counts `[0, 1, 2]`.

**Hypothesis.** A solver can replace “exactly one marker” with “an odd number of markers.” On every canonical input, the only odd marked frame has one marker, so the rival is extensionally identical there.

**Probe.** I implemented the rival independently and checked it against all five retained canonical pairs before adding it to `CANONICAL_SHORTCUTS`. The pre-repair regression failed because the generator did not expose `decoy_marker_count`, never emitted `[0, 1, 3]`, and had no declared odd-count rival (`checks/tdd-red/pytest.log`).

**Alternatives rejected.** A four-marker decoy does not separate parity from exact-one. Randomizing over many counts would expand the domain without a specific teaching need and would interact badly with the smallest three-cell interior. Changing the Racket rule would be incorrect because the authority already expresses the intended exact-one behavior.

## D2 — Add `decoy_marker_count` as an exact, observable axis

The selected domain is `2..3`. Count 2 preserves canonical-like examples; count 3 is the smallest change that refutes parity. The axis is passed through `gen_ctx`, recovered by `observe_overrides`, validated at both boundaries, and included in role facts. Values 1 and 4 fail loudly. Every Cartesian combination of the advertised exact axes remains constructible, so no incompatibility declaration is needed.

The final override gate accepted 55,530/55,530 draws over 617 cases and three difficulty bands. This is stronger evidence than merely observing the default schedule.

## D3 — Use a four-slot deterministic teaching schedule

`EXAMPLES_NEEDED` remains four. Two schedule slots use a two-marker distinct-color decoy, and two use a three-marker shared-color decoy. Every cyclic start over four consecutive demonstrations therefore includes both marker multiplicities and a parity counterexample, while preserving the existing witnesses for shared-color, position, and size shortcuts.

I rejected independent random selection of marker count because a four-example lesson would then have a nonzero chance of containing no three-marker counterexample. The cyclic-window regression checks every start and every difficulty rather than only pooled witness frequency.

## D4 — Require an *observable* three-marker counterexample

The first implementation allowed the three-marker decoy to receive the smallest frame, whose interior area is exactly three. In that case all interior cells were already markers, so “fill every odd frame” selected the decoy but changed no cells. The new regression caught this exact failure (`checks/tdd-red-observable/pytest.log`).

The minimal repair keeps the target’s requested size rank exact, retains the keyed shuffle, and swaps the two remaining ranks only when a three-marker decoy would otherwise receive `smallest`. This guarantees `interior_area > marker_count` without changing the advertised axis set. The focused test then passed, followed by all 10 task-local tests (`checks/tdd-green-observable/pytest.log`, `checks/tdd-green-observable/pytest-full.log`).

## D5 — Keep canonical strictness and authority separate from teaching breadth

`strict_canonical_like` still accepts only `[0, 1, 2]`, canonical dimensions, and the canonical palette relation. Three-marker examples are lawful generated lessons but intentionally noncanonical. This preserves a meaningful strict-profile measurement: 282/600 final draws, or 47.0%, passed the strict predicate; the profile-floor stage found 31/60 exact-profile hits.

The Racket authority, canonical row, and pinned `RULE_HASH = "7819ac1160c7"` were not modified. Python `rule_mirror` remains parity-checking/test support rather than output authority.

## D6 — Retain a source-bound census tool

`workspace/shortcut_probe.py` loads the selected generator by file path, verifies every declared canonical shortcut against every usable canonical pair, samples exactly 100 draws per difficulty, and records source/canonical hashes, sampler, marker-count histogram, unique inputs, disagreements, semantic witnesses, one exact input, and a domain limitation.

The final sampler was:

- bands: easy, medium, hard;
- sample indexes: 0–99;
- seeds: `91000 + 1000*band_index + sample_index`;
- denominator: 100 generated inputs per band, not overlapping lesson windows.

Every band produced 100 unique inputs, 50 two-marker draws, 50 three-marker draws, and 50 odd-rival disagreements. This is empirical evidence for the selected manifold, not a universal induction claim.

## D7 — Preserve failures and distinguish baseline, intermediate, and final evidence

The baseline 12-stage battery was green even though G1 existed. I retained that result to show the blind spot. The first RED proves the new semantic contract was absent. The second RED proves the initial repair was only partially effective. The final task-local suite, source-bound probe, dedicated lint, and final 12-stage battery are bound to generator SHA-256 `b11102ec70073d50cd748858e6f631d4be643c8c280a33feb6ef379ea2c61b38`.

Intermediate full-battery evidence was not used as the final claim because the observable-decoy repair changed the source afterward.

## Limitations

The generator continues to teach a three-frame scene with one empty, one target, and one multi-marker decoy. It does not attempt arbitrary frame counts, touching frames, mixed-color decoys, or all authority-valid geometries. The deterministic four-slot schedule is deliberate curriculum structure, not a claim that all future lesson assemblers will preserve consecutive sample indexes. Masked solve-query labels were not exposed during the reviewer solve.
