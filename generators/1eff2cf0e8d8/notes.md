# Working notes: 1eff2cf0e8d8

## Review finding

The imported `2.0.1` generator produced generally valid-looking grids, but its public contract did not describe its behavior. Four palette/texture names were dead, grid dimensions and several other controls were not honored, negative fixtures were advertised as normal textures, unknown keys were accepted, `RULE_HASH` was absent, and there was no semantic lesson contract. The before battery recorded six green stages, two advisories, and four blocking stages; the override checker alone found 43,666 issues across 52,650 draws. See `checks/before/` in the review return.

The canonical examples also leave two wrong rules unfalsified:

1. **Keep marker holes:** begin with the input instead of a blank output and stamp over it. This matches all five canonical pairs because every canonical template fills its top-left cell, covering each 9.
2. **Force source origin:** always place the source copy at `(0,0)`. This matches all five canonical pairs because every canonical source begins there.

## Selected repair

Version `3.0.0` replaces the unobservable metadata with seven exact axes recoverable from the grid: `grid_h`, `grid_w`, `template_h`, `template_w`, `n_template_colors`, `n_markers`, and `top_left_filled`. Every advertised boundary combination is constructively supported, invalid types/ranges and unknown keys raise `ValueError`, and `observe_overrides` recovers all seven values.

Generation constructs a sparse bounding-box-spanning template, assigns exactly the requested number of colors, and backtracks over shuffled marker footprints so the source and all implied stamp rectangles are disjoint. The complete validator accepts all canonical inputs and rejects malformed colors, dimensions, missing/invalid markers, impossible stamps, dense templates, and overlaps. The Python mirror is non-mutating and matches the selected Racket rule.

The default four-slot schedule is periodic in `sample_index`:

- `canonical_anchor`: exact canonical dimension/palette support with source at `(0,0)`;
- `marker_erasure`: a blank template top-left, which exposes the need to erase uncovered 9s;
- `offset_source`: a source bounding box away from `(0,0)`;
- `multicolor_multiple`: three template colors and three markers.

Every four consecutive sample indices therefore contain all four profiles, even when the lesson begins at a different residue. Named rivals and witnesses are executable. `lesson_identifiable` fails when any declared competitor survives all demonstrations.

## Rejected alternatives

- **Keep palette-kind/texture aliases and make them cosmetic.** Rejected because a named exact control must be observable; cosmetic labels would preserve the original contract defect.
- **Retain `no_template`, `no_anchors`, and `full_grid` in normal sampling.** Rejected because the selected rule is undefined or uninformative there and these cases were already failing `self_check`.
- **Use only random aggregate support.** Rejected because witness frequency does not guarantee that a four-demo lesson contains the needed counterexamples. A cyclic schedule gives a local lesson guarantee.
- **Require 4-connected templates.** Rejected after the regression test showed a canonical diagonal template; connectivity is not part of the authority. Generated masks remain connected for readability, but validation does not invent that constraint.
- **Change the Racket behavior.** Rejected. The authority is correct on canonical and generated inputs. Only the selected authority text was synchronized byte-for-byte with its existing raw/canonical form, removing comment-only source divergence.

## Evidence and limitations

`workspace/lesson_probe.py` uses the real `puzzle_generators.runner.run_one` path with an explicit canonical bundle and the selected Racket authority. It dynamically reads `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and witnesses from the source. The final source-bound run (`generator.py` SHA-256 `44ee3ba40b5e3f5b0fa7326e0931208e8f2e205c7150ea507f220f151fe081bb`) tested 100 lessons per band, all four cyclic starts equally, and 1,500 unique inputs. All 300 lessons were identifiable, every named rival was refuted in every lesson, and all 1,500 Python/Racket outputs agreed. See `checks/1eff2cf0e8d8_lesson_probe.json`.

This is evidence against the four declared competitors over the documented sampler, not a proof of universal induction. The generator intentionally limits templates to 2x2..3x3, one to three colors, and one to three markers; larger templates, overlapping copies, marker clipping, and unrelated non-9 distractors are outside the documented domain. The default schedule uses at least two markers, while the exact override contract still supports the one-marker boundary.
## Current reviewer considerations

Source SHA-256: `44ee3ba40b5e3f5b0fa7326e0931208e8f2e205c7150ea507f220f151fe081bb`.

# Decisions — 1eff2cf0e8d8

## D1 — Preserve the selected rule; repair the data contract

**Observation.** The canonical Racket program reproduces every public pair and the Python mirror agrees on all generated probes. The defects were distributional and contractual, not algorithmic.

**Decision.** Keep canonical behavior and rule hash `ede1d75f92cd`. Synchronize the selected solution JSON's comment-only `target_code` to the already-identical executable `raw_code` so source authority is unambiguous.

**Alternatives rejected.** Rewriting the rule for stricter source placement or marker validity would redefine the task and could reject canonical inputs. Leaving text divergence in place would keep defect/authority checks noisy for no behavioral benefit.

**Failure mode monitored.** Any future source edit must preserve the normalized rule hash and pass canonical plus generated Racket parity.

## D2 — Replace aliases with exact observable axes

**Observation.** `palette_kind`, `anchor_corner`, `asymmetry_force`, `palette_size`, `position_bias`, `n_distinct_colors`, and `texture` did not form a truthful API. Multiple names overlapped, and some were never consumed.

**Decision.** Declare only seven properties that `observe_overrides` can recover exactly from the finished input: dimensions, template bbox dimensions, template color count, marker count, and top-left occupancy.

**Alternatives rejected.** Keeping “helpful” aliases as metadata would still let callers believe they control scene semantics. Adding a generic `scene_profile` control would be observable but less useful for controlled ablations than independent exact axes.

**Probe.** The repository override matrix tested 302 cases, 30 seeds, three bands, and 27,180 total draws with no findings or warnings.

**Failure mode monitored.** A new axis is not accepted unless its requested value can be recovered from the grid or is explicitly declared incompatible with a structured reason.

## D3 — Construct rather than retry

**Observation.** Blind random retries make boundary combinations flaky and hide incompatible control combinations.

**Decision.** Enumerate lawful sparse template masks and use deterministic backtracking over shuffled stamp footprints. This supports all 128 min/max cross-products in the focused test.

**Alternatives rejected.** Repeated random placement with a high attempt cap is shorter but cannot prove advertised boundary combinations are constructive. Declaring incompatibilities was unnecessary because the whole product is feasible.

**Failure mode monitored.** Every generated source and marker rectangle must fit and be pairwise disjoint; `self_check` independently revalidates this.

## D4 — Treat lesson composition as the semantic unit

**Observation.** Aggregate witness frequencies can be high while individual four-demo lessons still omit a decisive branch. Canonical examples alone leave two wrong programs fully consistent.

**Decision.** Use a deterministic four-slot schedule keyed by `sample_index % 4`. Any four consecutive accepted samples contain a canonical anchor, marker-erasure case, offset-source case, and multicolor/multiple-marker case.

**Alternatives rejected.** Independent random profile draws could occasionally assemble ambiguous lessons. A larger lesson would add cost without needing more than the four identified discriminators. A single monolithic “hard” example would refute rivals but provide poorer factorized teaching evidence.

**Probe.** The retained tool tests 100 lessons per band and every cyclic start equally. All 300 lessons refute all four declared competitors.

**Failure mode monitored.** A schedule change must run the probe, record sampler shifts, and show each named competitor is refuted in every materialized lesson—not merely somewhere in a pooled census.

## D5 — Explicitly model canonical ambiguity

**Observation.** `keep_marker_holes` and `force_source_origin` each fit all 5/5 canonical pairs. `monochrome_template` and `single_marker_only` are additional plausible simplifications but do not fit every canonical pair.

**Decision.** Put the first two in `CANONICAL_SHORTCUTS`, all four in `LESSON_COMPETITORS`, and connect each semantic witness to a rival through `WITNESS_RIVALS`.

**Alternatives rejected.** Describing ambiguity only in prose would not let the gate verify that a purported counterexample actually changes the wrong program's output. Treating generic transforms as the only competitors would miss task-specific shortcuts.

**Failure mode monitored.** Shortcut functions must remain non-mutating, fit every usable canonical pair when claimed, and disagree on generated witness instances.

## D6 — Do not invent template connectivity

**Observation.** The first validator revision required 4-connectivity. A canonical example contains a diagonal continuation and failed that test.

**Decision.** Validation permits disconnected sparse templates because the authority operates on the full non-9 bounding box. Default generation still chooses connected masks for visual clarity.

**Alternatives rejected.** Changing canonical or weakening the regression test would encode a false rule. Generating arbitrary disconnected masks by default was unnecessary for the identified lesson ambiguities.

**Failure mode monitored.** Sampling preferences must not silently become validator requirements unless canonical and authority semantics establish them.

## D7 — Keep normal data lawful; remove negative textures

**Observation.** `no_template`, `no_anchors`, and `full_grid` were listed as valid textures but fail the task grammar or make the selected rule undefined/uninformative.

**Decision.** Remove them from normal generation and declare no lawful degenerate textures.

**Alternatives rejected.** Keeping them as rare robustness cases would poison standard supervised examples. A separate explicit negative-testing harness is more honest than overloading an input axis.

## D8 — Build a source-bound Racket-backed evidence tool

**Observation.** The built-in semantic battery intentionally materializes only 12 lessons. The duties require at least 100 per band when canonical-fitting rivals exist.

**Decision.** Add `workspace/lesson_probe.py`, dynamically reading source declarations and binding results to a SHA-256. It uses `runner.run_one` with an explicit canonical bundle, checks actual accepted indices, uniqueness, validators, competitors, witnesses, and Python/Racket parity.

**Rejected shortcut.** A mirror-only probe would be faster but could jointly agree with a wrong Python mirror. The final tool executes the selected Racket authority for all 1,500 pairs.

**Known scope.** The probe proves only its finite deterministic sample and declared rival set. Its JSON states this limitation explicitly.
