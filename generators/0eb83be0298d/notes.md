# Current notes: 0eb83be0298d

## Intended rule

The left three-column panel contains a cropped monochrome template. Color 9 is
the full-height divider. In the board to its right, template nonzero cells are
required and template zero cells are wildcards. For every match in the original
orientation, mark the matched window's bottom-right corner with color 8 on an
otherwise zero output. The selected Racket authority is unchanged; rule hash:
`4be3f14f70ed`.

## Repaired distribution (review-44a14bf0056d7e03)

The baseline generator (`ef310153…`) emitted isolated exact components and did
not pin `RULE_HASH`. A template-free component-bounding-box rule solved its
samples, while the canonical pairs also admitted the wrong interpretation that
template zeroes must be blank.

Version 2.0.0 introduced one to three exact original-orientation matches, a
same-color transformed decoy, and nonzero clutter in a wildcard slot of a true
match. It also replaced singleton/fake controls with exact observable axes and
rejected unknown difficulty/override names.

That first repair was reversed in one curriculum detail after self-review:
`checks/board-only-red.txt` showed a board-only known-family/frequency rival
surviving a complete four-pair window. Version 2.1.0 makes schedule residues 0
and 2 constructive refutation slots. Every tested four-pair window therefore has
at least two refuting pairs, leaving one visible witness whichever pair becomes
the query. Exact overrides bypass this curriculum-only constraint rather than
silently changing the requested values.

## Final evidence

Final generator SHA-256:
`697b1889cd42b9641e950211469c93d9c6296fe501f94148a527203a056c0c62`.
The required-rotation battery is 12/12 green. Portable focused tests are 562/562
passed. A 300-lesson census materialized 1,200 pair slots and 1,200 query
rotations (1,128 unique inputs) with zero ambiguity against the live declared
rivals. All 12 fixed-seed cyclic starts and 48 query rotations also passed.

The separate board-only stress probe tested 300 draws and 2,160 query rotations:
the rival solved 142/300 isolated grids but produced zero lesson teaching defects,
with at least two refuting pairs per four-pair window. The exact literal-zero
witness is `counterexamples/review-44a14bf0056d7e03/literal-zero-shortcut.json`.

## Limits and open scope

The semantic contract covers concrete declared rivals, not every conceivable
hypothesis. The fixed schedule census exhausts residues only at seed 0; the
larger census samples 100 lessons per band. Shapes are limited to five connected
five-cell 3×3 morphologies. Curriculum robustness is established for four
consecutive pairs with any one held out as query, not arbitrary skipped-index
assembly. Generated labels remain governed by the selected Racket rule; the
Python mirror is diagnostic and is bound to every usable canonical pair in tests.
## Current reviewer considerations

Source SHA-256: `697b1889cd42b9641e950211469c93d9c6296fe501f94148a527203a056c0c62`.

# Decisions for `0eb83be0298d`

## D1 — Keep the selected Racket rule authoritative

**Choice.** Pin `RULE_HASH = "4be3f14f70ed"`, leave the Racket authority and canonical rows unchanged, and use the Python mirror only for diagnostics and construction checks.

**Rationale.** The assignment is a distribution repair, not a rule rewrite. All usable canonical labels agree with the intended wildcard-template rule.

**Alternatives rejected.** Changing canonical outputs to literal-zero matching would make the examples less ambiguous by changing the task itself. Generating labels solely from the Python mirror would weaken source binding.

**Probe and failure mode.** Focused tests compare an independent oracle against every usable canonical label, while rule-smoke and authority-sync execute the selected Racket authority. A later authority change must update the pin and rerun all source-bound evidence.

## D2 — Replace isolated positives with exact matches plus same-color orientation decoys

**Choice.** Construct one to three nonoverlapping true matches and one transformed same-color decoy, then accept only scenes whose exact match set equals the requested anchors.

**Rationale.** The prior sampler made each relevant component look like an isolated copy, allowing a solver to ignore the template and mark component bounding-box corners. A same-color transformed decoy makes template shape and original orientation causally necessary.

**Alternatives rejected.** Adding only different-color noise does not defeat the component shortcut. Randomly sprinkling same-color cells without exact-set validation can create accidental extra matches or unsatisfiable overrides.

**Probe and failure mode.** `SEMANTIC_RIVALS` contains the component-corner and dihedral rules; focused tests require disagreement on every checked default draw. Construction is bounded and raises a descriptive error rather than returning a semantically weak scene.

## D3 — Put nonzero clutter inside a true match's wildcard slot

**Choice.** Every generated scene contains a nonzero board cell in a template-zero position of a true match.

**Rationale.** All three labeled canonical pairs also fit the wrong interpretation that template zeroes must align to blank board cells. The clutter is a direct causal counterexample while remaining lawful under the selected rule.

**Alternatives rejected.** Merely declaring the rival without emitting counterexamples leaves the lesson ambiguous. Color permutation alone does not distinguish wildcard semantics.

**Probe and failure mode.** The retained source-bound fixture and Racket receipt show a mark at `(5,6)` where literal-zero matching produces no mark. The generator rejects any candidate on which the rival still equals truth. Future changes must preserve this invariant under exact overrides.

## D4 — Repair the curriculum, not just individual draws

**Prior choice.** Version 2.0 required all per-draw declared rivals to disagree and used a four-profile cycle. That appeared sufficient under the shared semantic gate.

**New choice.** Version 2.1 adds a board-only known-family/frequency competitor at lesson level. Default schedule residues 0 and 2 use shape 1 and resample until that rival disagrees, guaranteeing two such refutations in every four consecutive slots.

**Reason for reversal.** Self-review found that a solver could often infer the repeated motif from the board without reading the template. The test-first witness `checks/board-only-red.txt` showed the first four-pair window had zero refutations.

**Alternatives rejected.** Requiring every grid to refute the rival was unnecessarily restrictive and made exact override support brittle. One refutation per four slots is insufficient when that pair is held out as the query. Two refutations preserve at least one demonstration witness under every query rotation.

**Probe and failure mode.** `checks/self-review/result.json` reports zero defects across 2,160 rotations and a minimum of two refuting pairs per tested window. This is a finite guarantee for the encoded rival and consecutive-window lesson assembly, not a proof against arbitrary board-only inference.

## D5 — Expose only exact, observable axes

**Choice.** Keep `grid_h`, `board_w`, `shape_id`, `match_count`, and `template_color`; reject unknown axes and unknown difficulty values; never clip a requested value.

**Rationale.** The baseline declared singleton or non-observable controls. Exact overrides should be falsifiable by reading the generated grid.

**Alternatives rejected.** Keeping compatibility aliases would preserve typo swallowing. Declaring internal schedule modes as public axes would expose implementation details rather than semantic controls.

**Probe and failure mode.** `observe_overrides()` reconstructs all five values, joint boundary tests exercise every advertised combination, and the final override stage is green. A future axis must have a nondegenerate domain and an independent observation method.

## D6 — Preserve canonical profiles while broadening support conservatively

**Choice.** Cycle the three observed canonical dimension/palette profiles and one broader profile; use five connected five-cell 3×3 shapes.

**Rationale.** Canonical anchoring protects task identity, while the broad slot avoids teaching one fixed geometry or color. Five related morphologies provide variation without changing the grammar.

**Alternatives rejected.** Arbitrary shapes would enlarge the rule family beyond the evidence and make constructive decoys less reliable. Using only the official shape would make family memorization easier.

**Probe and failure mode.** Schedule tests verify all profile residues. The limitation is explicit: this generator does not claim support for every possible template morphology.

## D7 — Treat shared gates as necessary but not sufficient

**Choice.** Retain the full battery, task-local TDD tests, random and cyclic lesson censuses, exact Racket witnesses, and a separate adversarial self-review probe.

**Rationale.** Audit target `31b8bedd699a` and the intermediate selected generator both demonstrate that an all-green battery can miss undeclared low-complexity shortcuts.

**Alternatives rejected.** Relying only on the 12-stage battery would miss the board-only lesson defect. Relying only on Python mirrors would not establish selected-rule behavior.

**Probe and failure mode.** Final evidence is bound to generator SHA `697b...c62`; changing generator bytes invalidates the solve and all source-bound reports.

## D8 — Do not modify audit targets

**Choice.** Reproduce and document defects in `05cfa1aabb8a` and `31b8bedd699a` without patching their sources.

**Rationale.** The assignment explicitly requests adversarial audits, not repairs, for those targets. Editing them would also violate the selected-task delta boundary.

**Probe and failure mode.** Both findings have machine-readable inputs, Racket receipts, rival outputs, generator/rule hashes, and domain status under `checks/audit/`. Their maintainers must decide any repair.

## 2026-10-25 native parametric build (`match_count_relay`)

The production generator and canonical authority remain unchanged. The task-local native adapter keeps `mode=canonical` as an exact byte-for-byte canonical default and adds an opt-in matched-input `mode=match_count_relay`. Step A crops the template and finds original-orientation board matches while treating template zeros as wildcards. The number of wildcard matches is the intermediate `k in {1,2,3}`; Step B uses `k` as a one-based selector among exactly three row-major color-6 anchors and marks that anchor in addition to the canonical match-corner marks. The protected counterfactual treats template zeros literally; authored wildcard clutter drives it to a different selector.

The first bounded audit exposed a genuine minimum-lesson shortcut: in 10 of 32 seeds, counting template-color connected components fit both demonstrations but changed a query. A regression was written first, then the first demonstration profile was enlarged so the true matches and decoy components separate; the final minimum lesson rejects that rival. The adapter supports 2–6 demonstrations and 1–4 prefix-stable queries, with a substantive 30x30 fourth query and identical inputs across modes. Final evidence: 589 focused tests passed; a 32-seed audit over demo counts 2/3/6 covered 192 episodes and 1,152 named-rival checks with no retained failures; native qualification passed four jobs, 32 protected-Racket evaluations, and four queries per job; 16 public one-query views passed exact identity/structure checks. The retained 30x30 witness has correct intermediate 2; the literal-zero counterfactual changes two output cells and replays as `reviewer_replayed`.

Limits: the rival audit is finite, the relay is an opt-in proposal rather than a production-rule change, and exact integrated-source owner acceptance plus any training admission remain pending.

