# Working notes: 51c5df6650a9

## Intended rule and authority

Read the distinct nonzero colors in row 0 from left to right. For each color, find its body-only 4-connected component, tightly crop that component, and paste the crops left-to-right into a fresh same-sized grid beginning at row 1, with one blank column between crops. The selected Racket authority was not changed; version 3.0.0 pins canonical `RULE_HASH = "4ec427a9d6d9"`.

## Baseline findings

Baseline generator SHA-256 `1df688bb1e6e3b03b9d1fe32fc6e7777b4f07d57fe90aad777f708641fd76b21` finished with 6 green, 2 advisory, and 4 failed battery stages. It lacked `RULE_HASH`, advertised dead or contradictory axes and degenerate “valid” textures, ignored or mismatched many overrides, and had no executable semantic rival contract.

The blocking rule crash was reproducible in 3 of the 120 rule-smoke inputs. At `seed=20, sample_index=20, difficulty=easy`, a color-3 body blob began directly below the row-0 color-3 legend cell. Those cells merged into one component spanning rows 0 and 1; the Racket rule deliberately filters to body-only objects and therefore found no color-3 object, ending in a `hash-ref ... given: #f ... 'bbox` error. The exact input and error are retained in `counterexamples/baseline-seed20-legend-body-merge.json` and `checks/root-cause-51c5df6650a9/easy-seed20-racket.json`.

## Reversed design decision

**Prior choice (v2.1.0):** retry random placements, including an outer reset loop, to avoid wedged blobs.

**New choice (v3.0.0):** use constructive, widely separated slots and reserve row 1 as an unconditional blank separator. Random retry could address spatial wedging but not the actual legend/body merge, because the old legality predicate started at row 1 and never checked row-0 adjacency. Constructive placement removes both failure classes and makes dropped or merged components impossible under the generator grammar.

## Distribution decisions

Only exact pixel-recoverable controls remain:

- `profile`: the five canonical dimensions `10x13`, `11x14`, `10x12`, `12x14`, and `11x13`;
- `n_legend`: 2, 3, or 4;
- `legend_layout`: `contiguous`, `shifted`, or `canonical`.

The `canonical` layout places colors in columns 0,2,4 (and 6 for four colors) and remains available as an exact override so all five canonical pairs are supported. Ordinary sampling uses only `contiguous` and `shifted`, because all five canonical demonstrations also admit the wrong shortcut “read only columns 0, 2, and 4.” Every ordinary input therefore refutes that shortcut. Colors are assigned to spatial slots by a derangement, so body scan order differs from legend order on every generated input and directly refutes the second plausible rival.

Motifs are connected triominoes through pentominoes. Easy draws use 3-cell components, medium uses 3–4, and hard uses 4–5. Four-color inputs restrict each crop to width at most two, guaranteeing that four crops plus three gaps fit even the narrowest 12-column profile.

## Validation and semantic contract

`self_check` now validates literal ARC cells, exact profiles, the blank separator, supported legend layouts, distinct colors, one 3–8-cell component per color, no cross-color cardinal contact, packed-width fit, and nontrivial legend/body order. It accepts all five canonical pairs. `observe_overrides` recovers every advertised control exactly. The Python mirror, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, witnesses, and `lesson_identifiable` are executable and tested.

Final generator SHA-256 is `3ac04fd993034c7bbad26c9243e5c81e908f23bd8580a62c0046bad566890ffa`. The final battery is 12/12 green. Task-local regressions are 207/207 green. A wider final-source census materialized 300 three-demo lessons (100 per band), 1,200 unique pair inputs, and every one of 1,200 query rotations; no declared rival survived and there were no materialization, hook, or scoring errors. A separate 900-draw self-review found 900/900 lawful unique inputs, zero Python-reference disagreements, and zero survivals for either named rival.

## Known limits

The strict teaching grammar is intentionally narrower than every input on which the broad Racket program might execute: it requires a blank row 1, exact canonical dimensions, separated components, and a body order that disagrees with legend order. The finite rival census establishes only that the two declared plausible rivals are refuted in the sampled lessons; it is not a proof of unique induction against every imaginable program. Canonical layout is override-only in ordinary sampling, so distribution consumers that require the exact historical 0,2,4 header must request it explicitly.

No unresolved blocker remains for this repair.
## Current reviewer considerations

Source SHA-256: `3ac04fd993034c7bbad26c9243e5c81e908f23bd8580a62c0046bad566890ffa`.

# Decisions for 51c5df6650a9 v3.0.0

Final generator SHA-256: `3ac04fd993034c7bbad26c9243e5c81e908f23bd8580a62c0046bad566890ffa`
Selected authority: task `51c5df6650a9`, rule hash `4ec427a9d6d9` (unchanged)

## D1 — Replace retry placement with constructive separated slots

- **Prior choice:** v2.1.0 used random placement retries, including an outer reset, apparently to avoid wedged or overlapping blobs.
- **Observed failure:** retry legality did not inspect adjacency to row 0. At easy seed/sample 20, a same-color body cell in row 1 joined its legend cell; the Racket rule filtered that header-touching object and later crashed on a missing bounding box.
- **New choice:** row 1 is always blank, and rows 2+ use fixed spatial slots selected by component count: opposite corners for two, two top corners plus bottom center for three, and four corners for four.
- **Why:** the invalid state is removed by construction rather than made less likely. Every slot remains inside the grid and slots are mutually separated for the supported 3×3-or-smaller motifs.
- **Rejected alternative:** retain retry sampling but add a row-0 adjacency predicate. That would address the known merge yet retain unnecessary stochastic failure modes and harder-to-audit drop/retry behavior.
- **Probe/evidence:** `checks/root-cause-51c5df6650a9/easy-seed20-*`; regression `test_seed20_rule_crash_reproducer_has_a_blank_separator_row`.
- **Cost if wrong:** the constructive geometry could under-cover legal Racket inputs; this is accepted because this generator is a strict teaching manifold, not an enumerator of every executable input.

## D2 — Keep the Racket authority unchanged and pin it

- **Choice:** no canonical or bank rule bytes changed; add `RULE_HASH = "4ec427a9d6d9"` to the generator.
- **Rationale:** canonical outputs were correct and the crash arose from an unlawful generated input, not from the intended transformation.
- **Rejected alternative:** make the rule recover header-touching objects. That would broaden or change task semantics to compensate for a generator defect.
- **Verification:** final authority-sync and execution-parity stages passed; all five canonical pairs match an independent Python mirror.

## D3 — Expose only pixel-recoverable exact controls

The public axes are:

1. `profile`: `h10_w13`, `h11_w14`, `h10_w12`, `h12_w14`, or `h11_w13`;
2. `n_legend`: literal integer 2, 3, or 4;
3. `legend_layout`: `contiguous`, `shifted`, or `canonical`.

- **Prior state:** the baseline advertised controls whose values were dead, contradictory, or not recoverable; it also admitted degenerate “valid” textures. The original rationale for several old axes is unknown.
- **Why these controls:** each is observable exactly from returned pixels and materially changes task structure while preserving the rule.
- **Validation policy:** unknown controls, booleans/floats/strings for the integer axis, unsupported values, and invalid difficulty names raise before sampling. `observe_overrides` reconstructs all three values from the grid.
- **Rejected alternative:** retain hidden construction knobs. Exact override claims require output-observable provenance; hidden knobs would make the contract unverifiable.
- **Probe/evidence:** full legal cross-product and negative scalar cases in `tests/test_generator.py`; final override report under `checks/after/`.

## D4 — Preserve exactly the five canonical size profiles

- **Choice:** sample uniformly across the five `(height,width)` pairs already represented by canonical examples.
- **Rationale:** this guarantees strict canonical-profile support in every difficulty band without inventing unrelated geometry.
- **Alternative rejected:** free rectangular dimensions. The Racket program may run more broadly, but arbitrary sizes add distribution variation without adding transformation insight and complicate packing guarantees.
- **Limitation:** the strict generator does not cover every size accepted by the broad rule.

## D5 — Ordinary legend layouts must refute the fixed-column shortcut

- **Canonical shortcut:** every historical demonstration puts legend colors in columns 0, 2, and 4, so “inspect only columns 0,2,4” fits all five canonical pairs.
- **Choice:** ordinary draws use `contiguous` or `shifted`; `canonical` is exact-override-only.
- **Why:** either ordinary layout forces the solver to read nonzero legend cells left-to-right rather than memorizing fixed positions.
- **Alternative rejected:** sample all three layouts uniformly. That would allow individual lessons to overrepresent the shortcut-fitting layout and weaken teaching evidence.
- **Compatibility:** explicit `legend_layout="canonical"` retains canonical support; for four colors it uses columns 0,2,4,6.
- **Witness:** `checks/shortcut-witness/witness.json` (`seed=0`, `sample_index=0`, easy) uses four contiguous legend colors and makes the rival omit colors at columns 1 and 3.

## D6 — Derange body order relative to legend order

- **Choice:** assign legend colors to physical body slots with a permutation having no fixed points.
- **Rationale:** a body-scan-order solver is a plausible wrong rule. If body and legend order occasionally coincide, examples can label that rival accidentally; a derangement ensures every generated input directly distinguishes it.
- **Rejected alternative:** random unrestricted permutation. It has useful diversity but can equal the legend order, especially with two or three colors.
- **Failure mode guarded:** `self_check` rejects any input whose body reading order equals the legend order.

## D7 — Use small connected motifs with difficulty-dependent size

- **Choice:** connected rotations/reflections of triominoes through pentominoes; easy uses 3 cells, medium 3–4, hard 4–5. Components have height at most 3; four-color cases have crop width at most 2.
- **Rationale:** shape variation exercises cropping without letting local visual complexity dominate the ordering rule. The width bound guarantees four crops plus three separator columns fit the narrowest 12-column profile.
- **Rejected alternative:** arbitrary random walks/textures. The baseline showed that “texture” knobs could be degenerate or hard to validate, and larger crops complicate guaranteed packing.
- **Known limit:** difficulty changes local crop complexity, not the conceptual rule.

## D8 — Make the strict grammar explicit

`self_check` verifies rectangular literal ARC cells, exact profiles, a blank row 1, supported distinct legend entries, body colors drawn only from the legend, no cross-color cardinal contact, exactly one 3–8-cell body component per legend color, packed-width fit, and nontrivial body/legend order.

- **Choice:** malformed grids return diagnostics rather than raising.
- **Rationale:** the battery and future agents need a stable boundary between lawful teaching inputs and broad rule-executable inputs.
- **Alternative rejected:** merely call the Racket rule and accept anything that does not crash. Runtime acceptance is not a semantic or teaching contract.
- **Mutation coverage:** separator contact, duplicate legend color, missing body, unsupported layout, foreign color, ragged row, and Boolean cell are all rejected.

## D9 — Add executable rivals, witnesses, and lesson checking

- **Canonical shortcut:** `fixed_columns_0_2_4` is declared in `CANONICAL_SHORTCUTS` because it actually fits all canonical pairs.
- **Lesson competitor:** `body_scan_order` plus the canonical shortcut are declared in `LESSON_COMPETITORS`.
- **Witnesses:** compare each rival's concrete output with the independent Python mirror; `lesson_identifiable` requires at least three correctly labeled demonstrations and rejects a rival that fits all demonstrations but changes the query.
- **Lesson assembly measured:** ordinary production uses three demonstrations and one query. The retained census materialized 100 lessons per band and held out each of all four pairs in turn, producing 1,200 query rotations.
- **Result:** zero ambiguity for the declared rivals in both production ordering and every measured rotation.
- **Limitation:** this is finite hypothesis testing, not proof against undeclared programs or all possible random seeds.

## D10 — Keep the Python mirror independent and the Racket rule authoritative

- **Choice:** `reference_output` and `workspace/reference_probe.py` independently implement crop-and-pack for tests and rival construction. Generated labels continue to come from the selected Racket authority in the official runtime.
- **Rationale:** a readable mirror supports deterministic local regressions without replacing authority.
- **Rejected alternative:** import private runner internals or treat the mirror as proof of authority. Final evidence instead includes public `arcpuzzles apply`, rule smoke, and authority parity.

## D11 — Audit targets remain unchanged

The two adversarial targets were read and exercised only after assignment. No source under `aa14c6a9f111` or `3eff273eeb83` was edited. Their findings and exact source hashes are in `AUDIT.md`; they are reports, not approvals or repairs.
