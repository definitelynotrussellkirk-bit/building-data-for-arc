# Working notes: 7f31c4f794b2

## Review identity

- Assignment: `review-02c41d03f07a1b47`
- Imported generator: version `2.0.1`, SHA-256 `dddd8697c66f8c212033cd2c28d8bac42806fa34c2240651133e79581f86068e`
- Repaired generator: version `3.0.0`, SHA-256 `4e3177bab6a537619394175d91588775cc0b9a60c7b520387fc27e4b53f9c87d`
- Canonical rule hash: `187a145d27eb`
- No prior return was used as a lead; current source was measured directly.

## Defect and repair

The imported code painted four distinct-color L triominoes at nearly fixed positions. Most declared axes and all helpful textures were inert, negative textures were mixed into the ordinary domain, the validator accepted minimal impostors, exact canonical-profile support was zero, and no semantic contract existed. Distinct colors also made the canonical/global-color shortcut viable: recolor every cell whose color appears on the border.

The replacement constructs 4–6 separated polyominoes with varied shapes, sides, positions, counts, and colors. It guarantees a top/bottom-only contact, a left/right-only contact, a border/interior same-color split, and mixed border/interior components. The public API now has four exact controls. `self_check`, `strict_canonical_like`, `rule_mirror`, witness/rival declarations, and `lesson_identifiable` are executable.

## Evidence

- Before battery: `checks/before/` — 7 green, 2 advisory, 3 failed.
- Completed after battery: `checks/after/` — 12/12 green after hash-verified resume.
- Portable selected tests: `checks/task-tests/` — 31 passed.
- Large census: `checks/lesson-census.json` — 300 lessons, 1,200 pairs and rotations, zero declared-rival ambiguity.
- Future-agent preflight: `workspace/component_contract_probe.py`; retained report `checks/component-contract-probe.json`.
- Repaired visible-only solve is bound to `4e3177bab6a537619394175d91588775cc0b9a60c7b520387fc27e4b53f9c87d` and passed all three visible demonstrations in one revision.

## Design limits

The generator intentionally covers only five shape families, component sizes 3–5, dimensions 8–14, and mixed scenes containing every witness type. It excludes identity-only/all-change lessons and does not prove uniqueness against undeclared rivals. Add future domain branches only with an explicit rival, disagreement witness, exact-control story, and source-bound Racket check.

Imported associated notes remain in `evidence/associated_notes.jsonl` with their original provenance.
## Current reviewer considerations

Source SHA-256: `4e3177bab6a537619394175d91588775cc0b9a60c7b520387fc27e4b53f9c87d`.

# Decisions for 7f31c4f794b2

Finding IDs refer to `REVIEW.md`. Each item records the chosen design, rationale, rejected alternatives, evidence, failure modes, and limits.

## D1 — Preserve the canonical Racket authority

**Choice.** Keep rule hash `187a145d27eb` and repair only the selected generator, tests, notes, and workspace.

**Rationale.** The baseline `rule_smoke` and authority synchronization passed, all five canonical labels were correct, and the observed failures were distribution/API/teaching defects rather than label defects. Changing the authority would create a new semantic decision without addressing R1.

**Alternatives.** Rewrite the Racket rule or replace it with the Python oracle; rejected because Racket is the label authority and no counterexample to it was found.

**Probe.** After `rule_smoke`, `racket_lint`, and `authority_sync` are green; authority-set SHA-256 is unchanged.

**Failure modes/limits.** The generated grammar covers a selected subdomain of inputs on which the authority is clear; it does not certify every possible grid the Racket program could execute.

## D2 — Replace the static sampler rather than patch its coordinates

**Choice.** Replace four fixed L-triomino placements with a constructive component sampler.

**Rationale.** Merely jittering the four coordinates would retain fixed count, size, shape, distinct-color assumptions, and the global-border-color shortcut. A constructive model makes intended invariants explicit and independently testable.

**Alternatives.** Add random offsets to the old four objects; rejected as cosmetic. Add many post-hoc mutations; rejected because they make exact controls and legality harder to reason about.

**Probe.** R2/R3; the focused distribution test observes at least eight dimension pairs, component totals 4/5/6, and object sizes 3/4/5.

**Failure modes/limits.** Backtracking is more code than fixed painting. A hard attempt cap (`250,000`) turns an unexpected packing regression into a loud `RuntimeError` rather than a hang.

## D3 — Expose only four exact, observable axes

**Choice.** Public axes are `grid_h`, `grid_w`, `n_border_components`, and `n_interior_components`, each with a truthful bounded domain.

**Rationale.** The baseline advertised palette, density, position, count, and texture controls that were ignored, unprobeable, or mixed lawful and negative fixtures. A smaller falsifiable API is preferable to broad metadata that does not control the draw.

**Alternatives.** Retain aliases or mark inert axes diagnostic; rejected because callers could still infer a semantic guarantee that was not present. Add `shape_kind` and `palette_kind`; deferred because exact joint support would add complexity without improving the core rule lesson.

**Probe.** 130 override cases, 11,700 accepted draws, zero findings/warnings; independent `observe_overrides` tests recover requested values.

**Failure modes/limits.** Removing undocumented old keys is a compatibility break for unknown external callers. The packet showed no dependent caller, and unknown keys now fail loudly.

## D4 — Use 8–14 dimensions and 2–3 components in each class

**Choice.** Grids are 8–14 in both dimensions, with 2–3 border components and 2–3 interior components.

**Rationale.** These ranges cover both canonical 8x8 and 10x10 sizes, leave enough room for separated size-5 shapes, and produce 4–6 objects without making scenes crowded.

**Alternatives.** Preserve old declared 4–22/4–24 ranges; rejected because many combinations cannot support the semantic witnesses and were never sampled. Use a fixed four objects; rejected because it creates a count shortcut.

**Probe.** Exact override tests cover minima/maxima and counts; profile floor records exact support in all bands.

**Failure modes/limits.** Very small, very large, and dense scenes are excluded. Difficulty mostly affects shape weighting rather than a calibrated reasoning scale.

## D5 — Bound the shape grammar to L3, S4, T4, V5, and W5 variants

**Choice.** Sample rotations/reflections of five connected polyomino families, spanning sizes 3, 4, and 5.

**Rationale.** The canonical task includes size-5 objects, while the baseline generated only size 3. These families add meaningful morphology without requiring arbitrary polyomino enumeration or uncertain noise semantics.

**Alternatives.** Arbitrary connected random walks; rejected because thin self-near shapes complicate same-color separation and validation. Rectangles only; rejected because they add a new regular-shape shortcut. All free polyominoes through size 5; deferred as unnecessary breadth.

**Probe.** Canonical inputs pass `strict_canonical_like`; tests observe all three sizes; defect lint no longer flags canonical object-size mismatch.

**Failure modes/limits.** Models are not trained on every connected shape. The validator intentionally rejects lawful-but-out-of-grammar components so distribution checks remain honest.

## D6 — Guarantee horizontal-only and vertical-only border contacts

**Choice.** Each draw has at least one border component whose touched sides are a subset of `{top,bottom}` and one whose sides are a subset of `{left,right}`.

**Rationale.** This makes top/bottom-only and left/right-only rule rivals fail inside every example rather than hoping a random lesson contains the needed orientation.

**Alternatives.** Let side orientation be independent random chance; rejected after the audit of `b7e4aaffabac` demonstrated that an orientation-only rival can survive all three demos in 8/128 real lessons. Schedule one witness per lesson instead of every draw; viable but more fragile under query rotation.

**Probe.** Both witnesses fire 600/600 in the semantic gate and 300/300 in the workspace probe.

**Failure modes/limits.** This overrepresents orientation contrast and may underrepresent lessons in which only one border orientation appears. It is an intentional teaching scaffold, not a claim about the full domain.

## D7 — Reuse one color across a border and an interior component

**Choice.** Force one color to label two disconnected components with different border status.

**Rationale.** R1 showed that all canonical pairs and the old generator permit “recolor every cell of any border color.” Split color identity is the smallest direct counterexample and also teaches that components are defined by 4-connectivity, not global color.

**Alternatives.** Use all distinct colors and declare the shortcut only; rejected because documentation does not teach the distinction. Reuse a color only probabilistically; rejected because finite lessons could miss it.

**Probe.** `global_border_colors` fits all canonical pairs but differs on every generated draw; `shared_color_split` fires 600/600 and its rival claim holds on all checked witnesses.

**Failure modes/limits.** Mandatory color reuse is another regularity. Other color-sharing patterns, including multiple border components sharing a color, are not systematically covered.

## D8 — Use bounded backtracking and keep same-color components nonadjacent

**Choice.** Enumerate legal placements for each role, randomize their order with the local generator RNG, and backtrack while prohibiting overlap and 4-neighbor contact between separately intended same-color objects.

**Rationale.** Constructing legal components directly is more reliable than painting then rejecting. Preventing same-color adjacency preserves the requested component counts and the split-color witness.

**Alternatives.** Rejection-sample entire grids; rejected because extreme overrides could become slow/non-deterministic. Permit same-color touching; rejected because two intended objects would merge under the actual rule.

**Probe.** Generation is deterministic, does not mutate process-global random state, honors all exact controls, and passes 11,700 override draws.

**Failure modes/limits.** The search cost grows with future shape/count expansions. New axes must be checked against candidate availability and the attempt bound.

## D9 — Weight canonical profiles without collapsing to them

**Choice.** Weight dimensions toward 8 and 10 and make grid width often equal height, while retaining 8–14 variation.

**Rationale.** The baseline had 0/60 exact canonical-profile support even though it sometimes fell within the envelope. Exact anchors improve transfer to the source task, but making every draw canonical-sized would reduce diversity.

**Alternatives.** Add a separate `canonical` mode; rejected because it would create another axis and schedule obligation. Use uniform dimensions; rejected because the 20-draw per-band floor could miss exact profiles.

**Probe.** After profile census: 19/60 exact, 29/60 envelope, with exact support in easy/medium/hard.

**Failure modes/limits.** The weighting is hand-tuned to current gate sample sizes rather than derived from a downstream mixture target.

## D10 — Declare four executable rivals and use three demonstrations

**Choice.** Declare `global_border_colors`, `top_bottom_only`, `left_right_only`, and `all_nonzero`; set `EXAMPLES_NEEDED = 3`; evaluate `lesson_identifiable` against them.

**Rationale.** These are simple, canonical-plausible or distribution-plausible shortcuts directly targeted by the chosen witnesses. Three demos match the generated lesson contract and remain sufficient because every individual draw already contains every witness class.

**Alternatives.** Rely only on generic diversity metrics; rejected because the baseline was morphologically valid while semantically ambiguous. Enumerate a large DSL of rivals; deferred to shared tooling because task-local exhaustive program search would be brittle.

**Probe.** Semantic gate: 12/12 lessons identifiable and 0/48 rotations ambiguous. Large census: 300/300 lessons and 1,200/1,200 rotations unambiguous against declared rivals.

**Failure modes/limits.** The rival list is finite. A new plausible shortcut should be added only with a concrete disagreement witness and independent expected output.

## D11 — Separate law checking, grammar validation, and canonical likeness

**Choice.** Implement an independent component oracle (`rule_mirror`), a grammar validator (`self_check`), and a stricter canonical-profile recognizer (`strict_canonical_like`).

**Rationale.** One weak predicate cannot truthfully serve all three roles. The baseline validator accepted destructive impostors; treating broad lawful grammar as canonical-like would inflate profile metrics.

**Alternatives.** Have `self_check` merely call the rule; rejected because label execution does not validate training distribution. Make `strict_canonical_like` identical to `self_check`; rejected because dimensions/palette profiles differ.

**Probe.** All canonical pairs match both the mirror and an independent test oracle; 50/60 destructive mutations are rejected; strict rate is measured separately at 33.5%.

**Failure modes/limits.** `self_check` still accepts some row-removal/minority-color mutations when the result happens to remain in grammar; mutation sensitivity is evidence, not proof of validator completeness.

## D12 — Add portable regression tests before implementation

**Choice.** Add `tests/test_generator.py` using `reviewer_support.find_root` and `canonical_pairs`, with independent component extraction and output calculation.

**Rationale.** The tests encode the failure modes that motivated the repair, not just implementation details: canonical parity, exact controls, invalid-key rejection, diversity, shortcut refutation, lesson identifiability, validator power, and RNG isolation.

**Alternatives.** Depend only on the full battery; rejected because iteration would be slower and root causes less localized. Reuse generator helpers in every assertion; rejected because correlated bugs could pass.

**Probe.** Portable task-test stage reports 31/31 passing and binds source SHA-256 `4e3177bab6a537619394175d91588775cc0b9a60c7b520387fc27e4b53f9c87d`; test file SHA-256 `80a58b8ea69c66653250eacc7954f104819321066fbe12b32af8dbadf935f476`.

**Failure modes/limits.** Tests sample bounded seeds and declared rivals. They do not replace Racket-backed rule smoke or large lesson census.

## D13 — Build a cyclic lesson probe for future agents

**Choice.** Add `workspace/component_contract_probe.py` to independently score the rule, every declared rival, witnesses, and all cyclic lesson starts in a deterministic schedule.

**Rationale.** The shared census is authoritative but heavier and does not enumerate every possible schedule start. A small Racket-free preflight makes accidental witness/schedule regressions visible before a full battery.

**Alternatives.** Leave a prose checklist; rejected because it cannot fail automatically. Modify shared tooling; outside the allowed task delta.

**Probe.** `checks/component-contract-probe.json`: 300 draws, 300 cyclic lessons, zero errors/ambiguities, all rival refutations and witness counts 300. Probe SHA-256 `da43f54169f9582192b599f978bc9cfbced7dc95ae219e2ff8c6c56215e3899e`.

**Failure modes/limits.** It uses the Python mirror and selected finite schedule. The source-bound Racket battery and census remain authoritative.

## D14 — Exclude degenerate identity/all-change textures in this revision

**Choice.** Remove baseline `all_interior`, `all_border_touching`, and `no_components` texture controls from the ordinary axis domain and generate mixed positive/negative components in every draw.

**Rationale.** Those fixtures were mislabeled as ordinary textures, violated baseline self-check assumptions, and weakened lesson identification. The immediate goal was to teach the component predicate robustly.

**Alternatives.** Preserve them as explicit lawful modes; possible later, but each would require scheduling guarantees so identity-only or all-change lessons cannot stand alone. Keep them as hidden branches; rejected because hidden negative distributions are not auditable.

**Probe.** Defect lint and override stages are green; the mixed-border/interior witness fires on every measured draw.

**Failure modes/limits.** The repair does not train legitimate all-interior/no-op or all-border cases. A future curriculum may add them as query/examples only when accompanied by contrastive demonstrations.
