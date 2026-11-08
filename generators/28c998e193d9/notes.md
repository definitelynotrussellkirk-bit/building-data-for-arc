# Working notes: 28c998e193d9

## Evidence read

- Canonical task: **Component-Wise Horizontal Closure**, rule hash `b18cc934f1d8`.
- Canonical corpus: two training pairs plus one test pair, at `8x14` and `9x15`, colors `{0,2}`.
- Retained associated notes: empty.
- Imported generator `2.0.1`: disjoint open rectangular frames only; prose and implementation claimed whole-bbox fill; nine mostly inert or contradictory axes; weak self-check; unknown overrides accepted.

## Baseline diagnosis

The strongest canonical-fitting shortcut is **frame-by-frame fill**: treat every horizontal red top bar with matching side rails as an independent open frame and fill that frame's rectangle. It matches all three canonical input/output pairs, including the first training input where two nominal frames touch and become one connected component. The imported generator generated only this shortcut-equivalent morphology, so more samples did not teach component-wise row closure.

Before battery:

- `5` green, `2` advisory, `5` failed stages.
- Canonical profile support: `2/60` exact, `12/60` envelope; easy had zero support.
- Override audit: `5,359` findings over `45,090` draws; unknown keys were accepted.
- Missing `RULE_HASH`; lint also stopped because Racket was unavailable.
- No semantic contract was declared.

## Selected design

1. Keep the canonical dimensions and palette exactly: `8x14`/`9x15`, background `0`, foreground `2`.
2. Keep two or three 4-connected components, matching the canonical object count.
3. Retain open frames as controls, but require at least one connected bent outline whose per-row closure is strictly smaller than its whole bounding box.
4. Put components on shared rows while maintaining a zero gap, so global row closure visibly over-bridges them.
5. Use four observable profiles combining component count and bent-component count; cycle every profile in every difficulty band.
6. Replace the legacy axes with one truthful axis, `scene_profile`; reject unknown or invalid overrides.
7. Add a pure Python diagnostic mirror of the canonical rule, semantic rivals, witness-to-rival claims, lesson identifiability, strict canonical-profile checks, and malformed-input mutation fixtures.
8. Leave the canonical Racket rule and canonical examples unchanged because their stated semantics are already correct.

## Alternatives rejected

- **Keep random rectangles and only fix metadata:** rejected because it leaves the strongest shortcut unchallenged.
- **Use arbitrary random polyominoes:** rejected because it would move too far from the tiny canonical vocabulary and make generation/validation harder to audit.
- **Use whole-bbox fill as the rule:** rejected because it conflicts with the canonical written solution and connected-component semantics.
- **Preserve the nine imported axes:** rejected because several were inert, singleton, aliases, or bypassed by degenerates, producing thousands of override-contract failures.
- **Retain blank/single-cell/solid-rectangle degenerates:** rejected because they collapse the task to identity/recolor behavior and teach no closure distinction.
- **Edit the canonical Racket rule:** rejected; no semantic defect was found in the canonical program or written solution.

## Test-first record

A focused regression suite was written before the rewrite. The red run had `7 failed, 1 passed`; failures covered missing rule identity/mirror, absent profile observation/schedule, shortcut-equivalent generation, mutation fixtures, and unknown override acceptance. After the implementation, the same suite passed `8/8`.

## Verification record

After battery:

- `7` green, `0` advisory, `5` failed stages.
- Canonical profile support: `60/60` exact and `60/60` envelope, all bands supported.
- Override audit: `450` accepted draws, `0` findings, unknown keys rejected.
- Semantic witnesses fired `600/600` for all six witnesses. Authoritative rival/lesson comparison could not run because Racket is absent.
- Independent Python stress: `1,200` draws, all profiles and bands, `258` distinct inputs; every draw refuted all six declared rivals and passed all local contracts.
- Python mirror matched all three canonical outputs; frame-by-frame shortcut also matched all three canonical outputs and was refuted by all `1,200` generated stress cases.
- Repository pytest suite: `96 passed, 28 skipped`; every skip explicitly required the absent Racket runtime.

## Failed attempts and environment limits

- Creating an isolated environment succeeded, but installing `requirements.txt` failed because DNS/network access was unavailable. The system Python already contained the required Python packages.
- Racket is not installed, no vendored minimal Racket archive is included, and network installation is unavailable.
- The first noninteractive after-check invocation timed out without stage output; rerunning in a background process with persisted logs completed normally.
- The first `package_return.py` attempt rejected task-local `__pycache__` files as changed source. Generated caches were removed and the packager was rerun without changing source.

## Remaining issues

Five battery stages remain non-green solely because the protected Racket runtime is unavailable: `lint`, `rule_smoke`, `defect_lint`, `semantic_gate`, and `authority_sync`. Their after logs contain no additional generator-specific defect. The diversity stage is reported green by the battery, but its own log says it produced no input/output pairs because Racket was unavailable; this is retained as evidence rather than treated as semantic verification.
## Current reviewer considerations

Source SHA-256: `4a7d0e96d04961bdc49f19ad190baf46222b14619c8133114403b14b280e4b11`.

# Decisions for `28c998e193d9`

## Design objective

Teach the canonical operation—4-connected component decomposition followed by per-component, per-row horizontal closure—without allowing the canonical-fitting “recognize each open frame and fill its rectangle” shortcut to survive.

## Input choices

| Choice | Original rationale | Selected rationale | Alternatives considered | Probe / evidence | Failure modes and limits |
|---|---|---|---|---|---|
| Dimensions exactly `8x14` or `9x15` | Imported code sampled roughly similar sizes (`7..10` by `11..14`), apparently to add variety; no retained rationale exists. | These are the two exact canonical profiles. Staying exact removes irrelevant size drift and lets all difficulty bands remain demonstrably on-manifold. | Keep broad size ranges; scale shapes proportionally. | Profile floor improved from `2/60` exact and `12/60` envelope to `60/60` for both. | Exact sizes reduce dimension diversity, intentionally; semantics rather than scale is the curriculum target. |
| Palette exactly `{0,2}` | Imported prose said red frames on black, but also declared unused palette axes. | Canonical inputs use black background and red markers only. | Recolor foregrounds or add distractor colors. | `self_check`, canonical acceptance, profile floor, and grammar battery. | Does not test color invariance; adding colors would create an unsupported task variant. |
| Two or three 4-connected components | Imported code aimed for two or three frames, but degenerates could violate that. | Matches canonical object count and forces transformation of multiple objects. | One component; four or more components. | `self_check`; `first_component_only` rival refuted on all 1,200 stress draws. | Component count is not itself a difficulty lever. |
| Open rectangular frames retained as controls | They were the entire imported distribution, likely chosen because canonical examples visibly resemble open frames. | They preserve visual continuity and provide simple controls alongside the decisive bent components. | Remove frames entirely; use only arbitrary shapes. | All four profiles include frame/bent combinations; canonical shortcut remains explicit. | Frames alone remain ambiguous, so no profile is allowed to contain only frames. |
| At least one bent connected outline | Not present before. | A connected outline whose row span changes with height makes row-wise closure differ from whole-bbox and frame-by-frame fill. | Random polyominoes; notched solid blocks; detached frame fragments. | Exact regression fixture; six semantic witnesses; 1,200/1,200 stress draws refute frame and bbox rivals. | The current bank uses one base bent topology plus reflections; future work could add more lawful topologies after authoritative Racket testing. |
| Components share rows but retain a zero gap | Imported placement required padding but did not deliberately exercise shared rows. | Makes global row closure over-bridge components while the intended rule preserves the gap. | Vertically disjoint components; touching components only. | `component_gap_refutes_global_row_close` fires on 600/600 battery draws and 1,200/1,200 stress draws. | Shared-row placement is deliberately frequent rather than naturalistic; this is a teaching distribution. |
| Horizontal/vertical reflections only | No explicit morphology transforms before. | Adds orientation variation while preserving exact dimensions, connectivity, and interpretable row spans. | Rotations/transposition; free random deformation. | Stress test over 1,200 draws and 258 unique input hashes. | No 90-degree rotation because it would swap the task's horizontal-vs-vertical emphasis and alter template dimensions. |
| Four `scene_profile` values | Imported generator declared nine axes, many inert or contradictory. | The profile is observable from component count and bent count, is fully honored, and directly expresses curriculum coverage. | Keep individual `grid_h`, `grid_w`, `n_frames`, palette, density, and texture axes. | Override checker: `0` findings over `450` draws; unknown key rejected. | One coarse axis provides less combinatorial control, intentionally avoiding false precision. |
| Every difficulty band cycles through every profile | Before, bands clamped dimensions and frame counts, making valid declared overrides fail and easy drift off-manifold. | Difficulty should not hide semantic cases; ordering changes by band, but coverage remains complete. | Reserve one/two-bent profiles for hard only. | Schedule regression test; profile coverage in semantic gate; `60/60` profile-floor pass. | Difficulty currently changes ordering rather than intrinsic complexity. This is honest but modest. |
| No degenerate textures | Imported blank/single-cell/solid-rectangle cases collapsed the rule to identity or recolor behavior. | Every training grid should require component-wise closure and distinguish at least one shortcut. | Keep degenerates as rare robustness cases. | All semantic witnesses fire on every generated grid; mutation fixtures retain malformed examples for validation instead of curriculum. | Excludes edge-case behavior from normal generation; that is appropriate until the core rule is authoritative-tested. |
| Strict self-check and mutation fixtures | Imported self-check only required a red cell and explicitly exempted degenerates. | Reject malformed, off-palette, off-scale, no-op, one-component, and non-overlapping-row cases. | Minimal structural checks only. | Eight focused tests; six mutation fixtures; battery selfcheck green. | Self-check validates the intended input grammar, not the Racket output itself. |
| Python `rule_mirror` and semantic rivals | Absent before. | Enable deterministic local diagnostics and explicit shortcut reasoning when the protected runtime is unavailable. | Depend only on Racket; compare only morphology. | Mirror matches 3/3 canonical outputs; all six rivals disagree on all 1,200 stress grids. | The mirror is not authority and must not replace Racket verification. |
| Canonical Racket program unchanged | Imported generator did not declare its hash; no evidence of a rule-source defect. | Written solution and canonical examples consistently specify component-wise row closure. | Rewrite Racket to bbox fill; change canonical examples. | Canonical Python mirror 3/3; declared hash; Racket source lint green. | Runtime equivalence remains unexecuted in this container because Racket is missing. |

## Strongest shortcut decision

The selected strongest rival is **frame-by-frame fill**, not merely whole-component bbox fill. It identifies each apparent open frame from a horizontal top bar and matching side rails, then fills each frame rectangle independently. This fits all three canonical pairs—even when two apparent frames are 4-connected—and exactly matches the imported generator's output semantics. The new bent outline breaks the frame detector below the first rail segment while the intended component closure continues row by row.

## Rejected implementation approaches

1. **Patch only the summary and rule hash.** Rejected because the distribution would still teach the wrong hypothesis.
2. **Add one rare bent case behind a texture override.** Rejected because default lessons could remain shortcut-equivalent and the override could be ignored.
3. **Generate arbitrary connected random shapes.** Rejected because it complicates validation and risks leaving the canonical manifold without adding targeted information.
4. **Use a large collection of independent axes.** Rejected after the baseline override audit showed that declarative breadth without observability creates false contracts.
5. **Treat missing Racket as a pass.** Rejected. Python evidence is reported separately and final completion remains blocked.

## Known limitations

- The bent-shape bank has one topology plus reflections; it is targeted rather than exhaustive.
- The profile axis exposes component/bent counts but not orientation or frame dimensions.
- Difficulty bands reorder profiles instead of defining distinct complexity levels.
- The protected Racket runtime was unavailable, so `rule_smoke`, authoritative semantic comparison, strict rule-dependent defect lint, and authority sync remain unverified.
- The battery labels files inside the requested `after` output as phase `before`; evidence is separated by outer directory, but the inner label is misleading.
