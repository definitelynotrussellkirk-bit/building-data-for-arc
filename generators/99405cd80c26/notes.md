# Working notes: 99405cd80c26

## Incoming state

The imported `2.0.0` generator did not match the canonical task closely enough
to teach the selected rule. It used color-9 separators instead of canonical
color 8, generated variable/multicolor panel textures with roughly 11–21
objects instead of the canonical object regime, had no `RULE_HASH`, accepted
all sampled destructive mutations, declared axes that were inert or
unobservable, and supplied no semantic contract. The immutable before battery
recorded 6 green, 2 advisory, and 4 failed stages.

The selected Racket rule itself was healthy: baseline Racket smoke and
execution parity passed, and it reproduced all canonical labels. No Racket or
canonical-data edit was justified.

## Selected design

- Keep the exact canonical 4×14 geometry with two full color-8 dividers.
- Use three 4×4 monochrome panels: A and B share a color; C uses another.
- Draw connected 3–6-cell motifs. Ordinary A and C have full eight-image D4
  orbits, so A→B is unique and C separates transform outputs.
- Schedule all eight transforms with `(seed + sample_index) mod 8`.
- Keep `self_check` authority-compatible, including the ambiguous canonical
  test; apply stronger uniqueness/orbit constraints only to generated teaching
  examples.
- Use five demonstrations, the worker-serializable maximum needed here. Five
  consecutive scheduled examples use five distinct transforms and eliminate
  every declared competitor.
- Expose only three exact, observable override axes: `transform`,
  `exemplar_cells`, and `query_cells`. Reject unknown or out-of-range keys.
- Pin the rule with `RULE_HASH = "20020b17585c"`.

## Semantic review

The strongest canonical-fitting shortcut is
`observed_transform_family_only`: recognize only identity, clockwise 90°
rotation, and horizontal reflection—the branches visible in the canonical
pairs—and otherwise copy panel C unchanged. The exact `rot180` replay
`seed=73, sample_index=11, difficulty=medium, exemplar_cells=4,
query_cells=5` separates it. Racket and the Python mirror agree on the rotated
answer; the shortcut returns unrotated C. See
`checks/selected-probe/report.json` and `QUESTION_ANSWER.md`.

## Verification history

1. Before battery: 6 green, 2 advisory, 4 failed.
2. First repaired after battery: lint/self-check/rule/profile stages passed,
   but strict semantics rejected `EXAMPLES_NEEDED=8` because worker lessons
   serialize only 2–5 demonstrations.
3. A failing regression test was added, the lesson size was reduced to 5, and
   lesson identification was rechecked against every declared competitor.
4. Final focused tests: 9 passed.
5. Final source-bound after battery: 12/12 green. A fresh completion
   rerun is retained in `checks/after-fresh/` with the same generator and
   authority hashes.

Final measured highlights: exact canonical profile 60/60; strict semantic
examples 600/600; canonical acceptance 3/3; witnesses 8/8; rival claims 8/8;
lessons 12/12; override contract 8,730/8,730 accepted; diversity 100% unique
inputs and 92% unique outputs over 300 pairs; Racket smoke 120/120 with no
crash; authority execution parity passed.

## Known limitations

Difficulty changes motif-cell ranges, not the underlying logical depth. The
fixed geometry is intentionally narrow because it matches every canonical
input. The canonical test is transform-ambiguous; the authority resolves it by
its documented transform priority, while ordinary generated teaching examples
avoid that ambiguity. The canonical Racket source still has a nonblocking
`dummy-let-binding` style finding; changing it would not improve semantics.
## Current reviewer considerations

Source SHA-256: `594440b02d4f73e7766ae71d9c352d12c15d1ff248e0eee21f87c6a1877edbfb`.

# Decisions: generator 99405cd80c26

The incoming notes contained no design rationale beyond a one-line summary, so
original rationales below are marked **unknown** unless directly encoded by the
canonical data or selected Racket rule.

| Input or contract choice | Original rationale | Decision and evidence | Alternatives/probes considered | Failure modes and limitations |
|---|---|---|---|---|
| Rule authority | Unknown; imported generator had no pin | Keep the selected Racket rule unchanged and pin `RULE_HASH=20020b17585c`. It reproduced all three canonical pairs, baseline/final smoke passed, and authority execution parity passed. | Rewrite rule or canonical row. Rejected because no semantic mismatch was found. | Canonical test has multiple matching transforms; behavior depends on the authority’s ordered first match. |
| Overall geometry | Incoming code varied panel dimensions; rationale unknown | Fix every ordinary input at 4×14: three 4×4 panels plus two one-column separators. Canonical profile gate moved from 0/60 exact to 60/60. | Continue dimension variation; allow larger square panels. Rejected because it caused profile drift without teaching a new rule. | Deliberately narrow; does not train size generalization unsupported by canonical evidence. |
| Divider color | Incoming summary/code used 9; rationale unknown and contradicted every canonical input | Use full-height color 8 in columns 4 and 9. | Random divider color or color 9. Rejected because separator color is stable in all canonical pairs. | Treats 8 as reserved inside panels. |
| Panel palette roles | Incoming generator used multicolor panels; rationale unknown | A and B are monochrome in one shared color from 1–7; C is monochrome in a different color; background 0, dividers 8. This yields exactly four colors like every canonical input. | Multicolor motifs; same color for C; color 9 motifs. Rejected because they change object/palette semantics and can add shortcut cues. | Color 9 is never used ordinarily, although ARC permits it. |
| Motif topology | Incoming random cells produced many disconnected components | Use 4-connected masks only. Canonical inputs use compact connected motifs, and defect lint’s object-count drift disappeared. | Arbitrary sparse cells; rectangular templates only. Arbitrary cells recreate object explosion; rectangles add a shape-family shortcut. | Connected masks with 3–6 cells do not exhaust all possible canonical-like shapes. |
| Motif symmetry | Incoming code did not guarantee transform identifiability | Ordinary A and C must have all eight distinct D4 images. A→B is then unique; C produces distinct outputs for every transform. | Permit symmetric A/C and rely on rule priority. Kept only for authority-compatible canonical acceptance, not teaching draws. | Excludes symmetric motifs from generated lessons even though the canonical test includes one ambiguous A. |
| Transform domain | Incoming generator’s exact coverage was unclear | Implement all eight D4 branches in the same order as Racket. | Only canonical-observed transforms; rotations only; reflections only. These are plausible shortcuts and therefore inadequate. | Extends beyond directly observed demonstrations based on the selected program authority. |
| Scheduling | No prior rationale | `ALL_TRANSFORMS[(seed + sample_index) % 8]`, so every consecutive eight-example window contains all branches exactly once. | Independent random choice; weighted choice. Rejected because finite lessons can miss rare branches and leave rivals alive. | Consecutive windows are intentionally regular; users can override the branch exactly. |
| Demonstration count | No prior semantic lesson contract | Set `EXAMPLES_NEEDED=5`. This is within the worker 2–5 contract and five consecutive branches refute every declared competitor. | Eight demos initially implemented to show every branch; strict semantic gate rejected serialization. Two to four demos can work in some windows but provide weaker guaranteed rival elimination. | Five demos cannot display all eight transforms in one lesson; branch coverage is across scheduled lessons. |
| Difficulty | Incoming axes mixed dimensions, palette, texture, and degenerate fixtures | Difficulty only adjusts cell count: easy 3–4, medium/default 3–5, hard 4–6. Rule and geometry remain stable. | Vary transform set, colors, geometry, or ambiguity by difficulty. Rejected because those alter semantics or canonical profile. | Difficulty is morphological density, not deeper reasoning complexity. |
| Override surface | Incoming contract declared many inert, aliased, unobservable, or illegal axes | Keep exactly `transform`, `exemplar_cells`, and `query_cells`; all are exact and observable through `observe_overrides`. Unknown and out-of-range values raise `ValueError`. Final override gate accepted 8,730/8,730 draws. | Preserve legacy axes for compatibility. Rejected because baseline had 648 findings, including missing provenance and inert combinations. | No explicit incompatible combinations exist; every legal cross-product is supported. |
| Validation boundary | Incoming `self_check` accepted every destructive mutation | `self_check` validates rectangular ARC colors, n×(3n+2) layout, full separators, nonempty monochrome panels, palette roles, and existence of an A→B transform. `strict_canonical_like` adds exact profile/topology; `_teaching_reasons` adds uniqueness/full orbits. | Put all constraints in `self_check`. Rejected because it would reject the genuine ambiguous canonical test. | Some destructive row duplication remains legal, explaining 51/60 rather than 60/60 mutation rejection. |
| Python rule mirror | None | Add `_apply_rule` solely for fast semantic contracts/tests while retaining Racket as authority. The exact counterexample probe confirms mirror/Racket equality. | Call Racket for every Python semantic check. Rejected as unnecessarily slow for thousands of local checks. | Mirror must stay synchronized; Racket smoke and selected probe guard this. |
| Rival set | No semantic contract | Declare fixed-transform rivals, copy-panel-B, and the strongest canonical-fitting observed-family shortcut. Supply one witness per D4 branch and exact rival claims. | Declare only trivial fixed rules. Rejected because it would miss the main canonical ambiguity. | Rival set is explicit, not exhaustive over every imaginable program. |
| Canonical shortcut | None | `observed_transform_family_only`: recognize identity, rot90, and flip-h; otherwise copy C. It fits every canonical pair and fails generated unseen branches. | “Always rot90,” “always copy C,” or “copy B.” These are weaker because they fail canonical pairs. | This is strongest among concise branch-family shortcuts tested, not a proof of unique strongest program under every complexity prior. |
| Canonical test ambiguity | Unmentioned in imported notes | Preserve exact Racket priority. `self_check` accepts it; ordinary generation avoids it. A unit test asserts both facts. | Reject ambiguous canonical input or alter output/rule. Rejected as incompatible with frozen canonical evidence. | Learners could infer identity rather than transpose on that pair; other generated branches disambiguate the intended D4 mechanism. |
| Determinism/RNG | No explicit rationale | Use keyed `gen_ctx` draws, return fresh grids, and leave Python’s global RNG untouched. | Global `random` or mutable caches. Rejected for reproducibility and worker isolation. | Cached mask catalogs are immutable tuples, but first construction has finite combinatorial startup cost. |

## Repair decision triggered by a failed gate

The first implementation used eight demos so one lesson showed all D4
branches. The strict semantic gate recorded otherwise excellent semantic
coverage but failed `EXAMPLES_NEEDED=8` against the worker’s 2–5 serialization
range. I added a regression test requiring 2–5 demos and guaranteed rival
elimination, observed it fail, changed the design to five consecutive branches,
and reran the isolated semantic gate before the full battery. The failure is
retained in `checks/after/`; the repaired isolated result is in
`checks/semantic-v2/`.

## Explicit non-decisions

- No canonical JSONL edit.
- No Racket rule edit.
- No unrelated shared-tool changes.
- No fixes to the two audit targets.
- No catalog approval claim; approval is external to this return.
