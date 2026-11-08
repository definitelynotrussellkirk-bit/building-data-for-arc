# Working notes: 7a6e065e8273

## Prior lead and baseline

The retained audit `review-79984b22fb47d6c1:v0001` (baseline source SHA-256 `74c9f1b…39b47`) was used only as a lead. It predicted canonical validator rejection, missing canonical size support, dead controls, and the seed-color/fixed-cyan semantic mismatch. All claims were remeasured against this packet's pinned baseline.

The required before wrapper was interrupted while entering defect lint, so it is retained as `running`, not called a completed battery. Its completed receipts show lint failed (missing `RULE_HASH` and unprobeable axes), self-check rejected all three canonical pairs, and rule smoke passed. An independent test-first suite then produced 25 failures / 11 passes / 1 protected-runtime skip on the untouched source.

## Selected design

- **Authority:** pin canonical `RULE_HASH = "1724b71ea895"`; do not change the Racket rule.
- **Literal rule:** every nonzero cell is a seed; paint a fresh grid's four cardinal neighbors cyan 8; omit centers; union overlaps.
- **Domain:** dimensions 6–12, one to six interior seeds, no orthogonally adjacent centers. Checkerboard-parity sampling makes the non-adjacency constraint constructive rather than rejection-heavy.
- **Profiles:** `canonical` is all color 5; `monochrome` is one repeated non-5/non-8 color; `mixed` uses at least two source colors and therefore requires at least two seeds.
- **Overrides:** four exact observable axes; unknown keys, wrong types, out-of-domain values, and the declared `seed_count=1` + `mixed` incompatibility fail loudly.
- **Teaching contract:** executable rivals cover “only color 5 matters,” “preserve source colors,” and “keep cyan centers.” The color-5-only shortcut fits all three canonical pairs, so generated non-5 evidence is mandatory.

## Rotation repair

Version 3.0.0 passed the ordinary 300-lesson census, but a cyclic query audit found 2 ambiguous rotations among 1,200: easy lessons 14 and 25 each had only one non-5 pair, and making that pair the query left three all-5 demonstrations. Exact deterministic tests for seeds `1841668169`/start `14` and `672830305`/start `25` failed first. Version 3.1.0 makes default even sample indexes non-canonical; explicit `color_profile` overrides still have the full domain. The final three-band census and all 1,200 rotations are clean.

## Final measured evidence

- Protected task tests: 41/41 passed.
- Battery: 12/12 green, no advisory/failure/interruption, generator SHA-256 `5a4ff91d…733c755`.
- Independent probe: 2,000 deterministic draws, zero self-check errors or duplicate rerun mismatches; 67/67 selected-Racket parity checks.
- Lesson census: 100 lessons per band, 300/300 fixed-query lessons clean; 1,193 distinct inputs across 1,200 pairs.
- Cyclic query audit: 0/1,200 ambiguous rotations against all declared rivals.

## Limits

The curriculum intentionally excludes border seeds, orthogonally adjacent centers, source color 8, canvases outside 6–12, and more than six centers. These are generator-domain limits, not claims that the mathematical transform is undefined there. Declared-rival and finite-sample checks do not establish universal induction or cover every possible shortcut.
## Current reviewer considerations

Source SHA-256: `5a4ff91d7d12f1981c3b4cfeb408d38a807d940d5135faf81042b864d733c755`.

# Decisions for 7a6e065e8273

## D1 — Keep the selected Racket authority unchanged

- **Original state/rationale:** Unknown. The baseline generator prose said halos preserve source colors, but the pinned canonical authority painted every arm cyan (`8`).
- **Decision:** Treat the selected Racket program as authoritative and pin `RULE_HASH = "1724b71ea895"`.
- **Alternatives considered:** Change Racket to preserve colors; reinterpret the examples as palette-dependent; leave the conflict undocumented.
- **Why rejected:** Every canonical output and source-bound rule-smoke result supports fixed cyan. Changing the authority would be a task change, not a generator repair.
- **Probe:** Independent literal oracle plus 67 real-Racket applications in `checks/7a6e065e8273-independent-v31.json`.
- **Limit:** The Python oracle is supplementary; the Racket rule remains the label authority.

## D2 — Make the domain literal and canonical-compatible

- **Original state/rationale:** Baseline required 2–4 seeds with distinct colors; rationale was not retained.
- **Decision:** Accept 1–6 nonzero interior centers, repeated colors, and all source colors in `{1,2,3,4,5,6,7,9}`; reject cyan in inputs because it is output-only in this curriculum.
- **Alternatives considered:** Preserve the old 2–4/distinct restriction; admit arbitrary counts; include border centers.
- **Why rejected:** The old restriction excludes all three canonical inputs. Arbitrary counts complicate capacity and overrides without evidence. Border seeds introduce clipping behavior absent from canonical examples.
- **Probe:** Canonical 3/3 acceptance; destructive-mutation tests; final self-check and profile-floor gates.
- **Failure mode/limit:** The generator does not claim coverage for border clipping, source color 8, or more than six centers.

## D3 — Use 6–12 dimensions with canonical weighting

- **Original state/rationale:** Baseline sampled roughly 6–8 and missed canonical 9×9 support.
- **Decision:** Exact dimensions 6–12 in both axes, with strong default weight on 8 and 9.
- **Alternatives considered:** Only canonical 8×8/9×9; uniform 6–12; unrestricted dimensions.
- **Why selected:** It guarantees canonical support while preserving modest shape diversity and inexpensive generation. Exact overrides retain every declared value.
- **Probe:** 2,000-draw independent audit saw all 29 sampled shapes and 492 canonical-shape/palette hits across the four bands.
- **Limit:** Weighting is curriculum policy, not an inferred task law.

## D4 — Construct positions on one checkerboard parity

- **Original state/rationale:** Baseline placement logic and its intended overlap policy were not retained clearly.
- **Decision:** Choose interior positions from one checkerboard parity, guaranteeing no orthogonal adjacency, then sample exactly the requested count.
- **Alternatives considered:** Rejection sampling arbitrary positions; forbid all adjacency including diagonals; fixed templates.
- **Why selected:** Constructive support is deterministic, fast, and allows diagonal proximity and halo overlap without accidentally placing adjacent centers.
- **Probe:** Exact count overrides through six centers in every difficulty band; self-check and distribution gates.
- **Limit:** Orthogonally adjacent centers are outside the reviewed input manifold even though the authority could process them.

## D5 — Expose three observable color profiles

- **Decision:** `canonical` = all 5; `monochrome` = one repeated non-5/non-8 color; `mixed` = at least two colors and therefore at least two seeds.
- **Alternatives considered:** Distinct color per seed; arbitrary unobservable palette controls; only color 5.
- **Why selected:** Repeated colors and one seed match canonical data. Non-5 profiles are essential to refute the canonical-fitting “only color 5 matters” shortcut. Each axis is directly observable from pixels.
- **Probe:** `observe_overrides`, exact override tests, semantic witnesses, and all three final lesson censuses.
- **Failure mode:** `seed_count=1, color_profile="mixed"` is impossible and is explicitly declared/rejected rather than silently altered.

## D6 — Fail bad overrides loudly

- **Decision:** Reject unknown names, booleans masquerading as integers, wrong types, out-of-domain values, and the one incompatible joint request.
- **Alternatives considered:** Ignore unknown keys; clamp values; redraw around incompatible requests.
- **Why selected:** Silent changes make source-bound experiments irreproducible and allowed the baseline controls to look supported when they were not.
- **Probe:** Protected tests cover 13 invalid combinations and exact observability in all four bands; final override gate is green.

## D7 — Declare executable rivals and witnesses

- **Decision:** Retain three plausible competitors: use only color-5 centers, preserve source colors in halos, and keep cyan centers. Bind witnesses to each rival and declare the color-5-only rule as a canonical shortcut.
- **Alternatives considered:** Narrative-only semantics; a large speculative rival set; no shortcut declaration because shape checks pass.
- **Why selected:** These are the shortest rules that explain common misreadings, and one genuinely fits all canonical pairs.
- **Probe:** Canonical shortcut fit is 3/3; every final lesson refutes it and the other competitors.
- **Limit:** This finite set cannot cover every possible learned shortcut.

## D8 — Add a rotation-safe default schedule

- **Initial implementation:** Version 3.0.0 drew all profiles independently. The ordinary 300-lesson census was green.
- **Failed probe:** Rotating all four pairs exposed 2/1,200 ambiguous cases. In easy lessons 14 and 25, the single non-5 witness became the query and the remaining three demos were all color 5.
- **Test-first repair:** Exact official seeds/starts were captured in failing tests before production code changed. A first generic test schedule did not reproduce the defect and was replaced rather than used as evidence.
- **Decision:** When no profile override is supplied, even sample indexes choose only non-canonical profiles; odd indexes retain full support. Explicit overrides bypass the schedule.
- **Alternatives considered:** Force every sample non-5; require two witnesses by rejection at lesson assembly; hard-code four-position lesson templates.
- **Why selected:** It is local, deterministic, cheap, preserves canonical support, and guarantees two non-5 pairs in every four consecutive defaults.
- **Probe:** 0/1,200 final ambiguous rotations; canonical profile remains present in every band; exact canonical overrides pass at arbitrary indexes.
- **Limit:** The guarantee is specifically for four consecutive production pairs and the declared color shortcut.

## D9 — Build reusable reviewer tooling

- **Decision:** Keep `reference_probe.py` as an independent oracle/parity audit and add `lesson_rotation_probe.py` for hash-bound cyclic query checks.
- **Alternatives considered:** Ad hoc notebook analysis; copy rival names into a one-off script.
- **Why selected:** Future agents can rerun exact checks, and the rotation tool reads the live rival dictionaries so declarations cannot silently drift from the probe.
- **Tests:** Tool tests first reproduced a one-witness query hole and then a clean two-witness lesson.
