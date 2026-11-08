# Working notes: dfc7297269cc

## Selected repair

Baseline `1.2.1` had a correct selected Racket rule but an inconsistent generator contract: no pinned rule hash, canonical inputs rejected by `self_check`, nominal axes that were aliases/constants/dead, degenerate textures that bypassed exact overrides, and no executable semantic rival contract.

Version `2.0.0` keeps the Racket authority unchanged and uses one constructively valid 5x7 tile, mirrored and translated inside an exact requested canvas. The tile contains the requested active motif count plus a wide same-color gap, unequal endpoints, and a vertical sandwich. Only four pixel-observable axes remain public.

## Failed iterations retained as evidence

1. Four-color defaults were initially too rare; a 512-draw test saw no `n_colors=4` case. Axis weighting was loosened while retaining canonical anchors.
2. The first after battery failed `defect_lint` because generated same-color components never reached the canonical singleton scale. Redundant palette markers were removed.
3. The next battery still failed because object counts stayed above canonical scale. Witness color placement was simplified so generated counts overlap the canonical range.

The final generator hash is `92519a1fabdd7fbfb96fccf57d53788ad232a954d6a463c44ff78c462f3a0988`; final battery 12/12 green, task tests 46/46, and the 300-lesson/1,200-rotation declared-rival census has zero ambiguities.

## Limitations

All foreground pixels occupy a compact 5x7 region, which is a real distribution regularity. Mirroring, translation, palette variation, full dimension support, and per-input semantic negatives reduce simple coordinate/template shortcuts, but finite declared-rival checks do not establish universal identifiability.

Imported associated notes and review indexes were empty, so no prior return was used as a lead.
## Current reviewer considerations

Source SHA-256: `92519a1fabdd7fbfb96fccf57d53788ad232a954d6a463c44ff78c462f3a0988`.

# Decisions for dfc7297269cc

## D1 — Preserve the selected Racket authority

**Choice.** Leave the canonical Racket program unchanged and pin its selected normalized hash as `RULE_HASH = "80ec61287499"`.

**Rationale.** The before `rule_smoke` and `authority_sync` stages were already green, and the rule matched all labeled canonical pairs. The defects were in the generator contract and teaching distribution, not label authority.

**Alternatives considered.** Rewriting the Racket rule or synchronizing the archival raw-code copy would add unrelated risk. Neither was justified by a semantic disagreement.

**Probe and failure mode.** Canonical pairs and 36 generated scenes are compared with an independent Python oracle and the real selected Racket rule in the task-local suite. Any rule drift, sequential-update bug, or authority mismatch fails `test_pins_selected_canonical_rule_hash` or the Racket parity test.

## D2 — Replace ten nominal controls with four exact controls

**Choice.** Advertise only:

- `grid_h` in 5–14,
- `grid_w` in 7–16,
- `motifs` in 1–4,
- `n_colors` in 2–4.

Every value is observable from the returned grid and accepted exactly in every difficulty band.

**Original rationale.** The baseline comments described palette, density, position, and texture axes, but most were constants, aliases, unused, or bypassed the ordinary contract. The original rationale beyond those comments is unknown; no retained prior notes existed.

**Rejected alternatives.** Keeping compatibility aliases would preserve a misleading public API. Advertising degenerate textures as ordinary controls would continue to produce rule-no-op or self-check-invalid examples. Expanding motif count to 8 was also rejected because the canonical task uses only 2–4 motifs and exact placement became needlessly coupled to grid size.

**Probe and failure mode.** Boundary overrides are tested in all four band settings. Unknown, wrong-type, and out-of-range values must raise. `observe_overrides()` independently recovers the requested values.

## D3 — Use one transformed 5x7 semantic microtemplate

**Choice.** Construct a 5x7 tile with exactly the requested active motif count and three negative witnesses, then independently mirror vertically/horizontally and translate it inside the requested canvas.

**Rationale.** A constructive tile makes exact controls and witness guarantees provable without rejection sampling. It also keeps the rule-local evidence visible while allowing dimensions, position, palette, and motif topology to vary.

**Alternatives considered.** Repairing the original random placement loop was rejected because it could not guarantee simultaneous support for exact motif counts, canonical-like scale, and all three semantic witnesses. Rejection sampling was rejected because it would make overrides and distribution support fragile and obscure failure causes.

**Known limitation.** All foreground pixels lie inside a compact 5x7 region. This is a layout regularity and could support undeclared template-specific hypotheses. The tile is mirrored/translated, and the actual rule remains necessary against all declared rivals, but the census is not universal.

## D4 — Guarantee three canonical-fitting shortcut witnesses

**Choice.** Every ordinary draw contains:

1. a same-color pair separated by two zeros (`span_fill` counterexample),
2. a one-zero gap with unequal nonzero endpoints (`any_nonzero_endpoints` counterexample),
3. a vertical same-color sandwich (`horizontal_or_vertical` counterexample).

**Rationale.** All three rivals fit every canonical pair. A lesson made only of positive horizontal sandwiches cannot distinguish immediate adjacency, endpoint equality, or horizontal-only orientation.

**Alternatives considered.** Scheduling one witness per example was rejected because arbitrary query rotation could hold out the only counterexample, as independently demonstrated in audit A2. Placing all witnesses in every input makes every demonstration individually refute all three shortcuts.

**Probe and failure mode.** The independent `reference_probe.py` defines each rival separately, supplies compact lawful counterexamples, and checks every one of 512 sampled draws per band/default setting. The 300-lesson census then checks the production sampler and every query rotation.

## D5 — Keep the validator broad enough for canonical inputs

**Choice.** `self_check` validates rectangular ARC grids, canonical-supported dimensions, at least two nonzero colors, and at least one active horizontal motif. `strict_canonical_like` delegates to that lawful domain.

**Rationale.** The baseline validator incorrectly demanded that every nonzero cell be an endpoint and imposed a guard-band topology not present in canonical inputs. A validator should reject structure-destroying impostors without silently redefining the task.

**Rejected alternatives.** Encoding the exact generated microtemplate in `self_check` would make the generator look healthy while rejecting lawful task inputs. Requiring every semantic witness in arbitrary external inputs would likewise conflate the training distribution with the rule domain.

**Probe and failure mode.** All canonical pairs must pass. All-background, one-color, singleton, solid block, short line, malformed, and out-of-range fixtures must fail diagnostically.

## D6 — Weight defaults toward canonical profiles without losing support

**Choice.** Use the three canonical tuples `(5,7,2,2)`, `(5,8,3,3)`, and `(6,9,3,4)` as weighted anchors; each public axis still includes its full legal domain in every band.

**Rationale.** This satisfies profile-floor requirements while avoiding a narrow canonical-copy distribution. Easy and hard adjust weights, not legal support.

**Failed iteration.** The first implementation made four-color draws too rare; a 512-draw regression observed none. The weighting was loosened so `{2,3,4}` is reached while profile support remains strong.

**Probe and failure mode.** Distribution tests require all motif/color counts and at least three shapes in 128 draws per band. The battery's profile floor must hit a canonical-size/palette profile in every band.

## D7 — Match canonical component/object topology

**Choice.** Avoid redundant palette marker cells except when a fourth color needs representation, and choose witness colors to keep same-color components small.

**Rationale.** The first two green-looking repairs still failed `defect_lint`: generated scenes lacked canonical singleton component scale, then produced too many separate objects. These were genuine profile restrictions, not linter false positives.

**Alternatives considered.** Weakening the validator or suppressing the linter was rejected. The generator was simplified instead.

**Probe and failure mode.** `test_generated_component_scale_includes_the_canonical_singletons` requires component size 1 to occur and maximum size ≤2. `test_generated_object_count_reaches_canonical_scale` requires generated object counts to overlap canonical scale. Intermediate failures are retained under `checks/after-2/` and `checks/after-3/`.

## D8 — Three demonstrations, arbitrary query position

**Choice.** Keep `EXAMPLES_NEEDED = 3` and require every input to contain all three shortcut witnesses, so any three demonstrations—and even one demonstration—refute the declared rivals.

**Rationale.** Three examples match the packet's default lesson shape and provide variety without relying on an ordered curriculum.

**Probe and failure mode.** The source-bound census materialized 100 lessons per band and held out each of four pairs once: 0/300 production and 0/1,200 rotation ambiguities. This only covers the three declared rivals.

## D9 — Build reusable independent tooling

**Choice.** Add `workspace/reference_probe.py` rather than embedding all helper logic in tests.

**Rationale.** Future reviewers can load any candidate generator path, inspect exact axes, run independent intended/rival outputs, build minimal counterexamples, and execute the selected Racket authority. It avoids circular tests that merely call production helpers.

**Limitations.** The Racket parity helper uses the packet runtime and is skipped only when Racket is genuinely unavailable. It is test tooling, not a second source of training labels.


## 2026-10-25 native parametric admission proposal

The selected production generator and canonical Racket authority remain unchanged. A task-local native sidecar now exposes one private parameter, `completion`, with two matched-input settings:

- `horizontal_all` is the byte-exact canonical rule: fill every zero between equal nonzero horizontal neighbours.
- `ranked_vertical` first finds and completes those canonical horizontal sandwiches, counts them, then fills the vertical sandwich at the same one-based row-major rank.

This was chosen because it preserves the canonical default while creating a genuine sequential dependency: the vertical output cell cannot be selected until the input-dependent horizontal count is known. The protected-Racket counterfactual fixes the rank to one on the same qualified input; the selected vertical cell changes, so the final grid changes.

The sidecar supports 2–6 demonstrations and 1–4 independently requested, prefix-stable queries. The first two demonstrations use ranks two and four. A bounded executable rival audit covers canonical-only, all-vertical, first/last/fixed-rank, row-count, colour-count, reverse-rank, and candidate-colour-extreme hypotheses. Across 64 seeds, both settings, and demonstration counts 2, 3, and 6, the audit checked 768 episodes and 4,736 labelled pairs, including 384 exact 30×30 stress pairs, with no declared-rival survivor or construction failure. This is finite evidence, not a universal identifiability proof.

Native qualification executed both settings at seeds 0 and 17 with three demonstrations and four queries: four jobs, 40 protected-Racket evaluations, and source-bound program hashes. Sixteen sequential one-query public projections passed masking and file-identity checks. The reusable audit is `workspace/parametric/audit_lessons.py`; the promotion adapter, exact default program, alternative program, manifest, and promotion contract all live under `workspace/parametric/`.

Owner-side exact-byte integration, native requalification, witness replay, fresh acceptance, and explicit training admission remain required.
