# Official adversarial audit draft

Scope: findings only on the two officially drawn current sources. No audited source, canonical authority, weight or approval was changed. Both reproducers use `reviewer_support.load_selected_generator` with an explicit local root. They stream/read only the matching canonical rows through portable helpers. The completed blind solve is unrelated and was not opened.

**Execution status:** both `probe.py` commands exited 0. The Python reference interpretations match all three retained canonical pairs for ebd08d719ed6 and all five for 05b5a82ace36. All retained episode inputs pass the current target `self_check` and are pairwise distinct. The new episode labels remain **Python-only pending supported Racket confirmation**. `verify_racket.py` will check exact inputs, source/rule pins and every returned output after the two `racket.json` files exist. Do not promote pending labels to Racket-verified based on this draft.

## A1: ebd08d719ed6 — color-restricted rival survives a four-query lesson

Current source: `repo/generators/ebd08d719ed6/generator.py`, SHA-256 `11501342d0db51f960e1e805844fd2c6949936c3c8e7988fc563b86f44af2ae8`. Canonical program SHA-256 `f5f6e2df9282bd2bb550728cbfc927a1de7d4fcf5099324c23254174e59ebeca`; short rule hash `f5f6e2df9282`.

The canonical rule selects the tile with the largest nonzero occupancy, regardless of its foreground color. A plausible competing rule selects the densest **color-2 tile** and ignores color-3 tiles. That rival matches all three canonical pairs.

**Exact reproduction:** `generate(seed=1, sample_index=i)` for `i=0..6`, default difficulty, no overrides; use indices 0–2 as demonstrations and 3–6 as four queries. All seven inputs are distinct and pass `self_check`. The rival matches all three demonstration outputs, then disagrees at source indices **4 and 5** (the second and third queries): seven and twelve cells differ in the current Python interpretation. The existing `fixed_five` rival is already refuted by the second and third demonstrations, so checking only that rival misses this ambiguity. This is an explicitly assembled legal 3-demo/4-query episode, not a claim about the default CLI's demonstration count or seed mapping.

**Cause and bounded recommendation:** `generate` schedules one-color versus mixed-color palettes but randomly assigns each tile's foreground color; it does not guarantee that the winning tile varies in color across the demonstrations. The executable semantic contract lists only `fixed_five`. Add the color-2-only rival and a distinguishing demonstration when a requested query needs color independence, while preserving existing fixed-five witnesses and the canonical rule. This is one demonstrated rival gap, not a claim that every lesson is ambiguous.

Current notes and `evidence/review_index.json` bind an accepted reviewer-reported repair at the current SHA. The older retained audit used `7b2d9d99...` and is explicitly resolved in notes; it is not the evidence for this new finding. The known finite-rival caveat remains accurate but does not prevent recording a newly reproduced counterexample.

Evidence: `checks/audit/ebd08d719ed6/{probe.py,report.json,inputs.json,python_reference_outputs.json,rival_outputs.json}`. The input-list file SHA-256 is `1f8ee17e9de0f67b1adfbef90c5bd47e7c4b96c8d3d530d7c88d4c6de40c4457`.

## A2: 05b5a82ace36 — exact controls and lesson identifiability need repair

Current source: `repo/generators/05b5a82ace36/generator.py`, SHA-256 `20de203b605235b2d1120b08f31f54b5fb172b77c3400224da0cc416575de305`. Canonical program SHA-256 `120d1cf30b8e23cdc1fbc7a0157e5b0aa5e8d1bbda6f7694e463bcc6dfcffba4`. Its notes are an empty working-notes stub and there is no retained current `review_index.json` in this home.

### A2.1 — Declared valid exact controls reject

At seed 17/index 0/default difficulty, each separate request `grid_h=8`, `grid_h=18`, `grid_w=10`, `grid_w=20`, `tpl_size=8`, or `n_anchors=4` raises a bounds `ValueError`, although every value is inside its declared AXES domain. The default call passes narrower sampling bounds to `draw_int`: 9–14, 11–16, 3–7 and 1–3. Thus intended sampling preference also rejects valid exact requests. The same probe shows that `texture="typo"` and an unknown keyword are silently accepted.

Honor the advertised exact domains across bands, explicitly document genuine incompatible combinations, and reject unknown texture/axis values. These are directly observed API failures; they need no Racket label to reproduce.

### A2.2 — Decoy presence does not guarantee a teaching witness

The canonical rule normalizes the unique largest connected >1-cell {2,4} component and stamps it at every anchor. The source comments name the plausible rival that combines all eligible {2,4} components into one template. That rival matches all five canonical pairs.

**Exact reproduction:** seed **12**, indices **0–3**, default difficulty, no overrides; first three are demonstrations and index 3 is the query. Component sizes are `[6]`, `[5]`, `[3,2]`, `[3,2]`. Despite a decoy in the third demonstration, clipping/placement makes the rival output equal there. Both programs match every demonstration; the query outputs differ in **eight cells** in the independently written Python interpretation. Inputs are distinct and accepted by current `self_check`. This explicit three-demonstration episode respects the source's `EXAMPLES_NEEDED=3`; no claim is made about the default CLI assembly.

Replace the prose-only rival claim with an executable per-query lesson check and retain a demo where largest-component versus union stamping visibly diverges. Merely including a decoy is insufficient when its effect is clipped away.

### A2.3 — Final validator accepts a float pixel

Generate seed 17/index 0 with `texture="plain"`, then replace the first color-2 pixel with `2.0`. The active final `self_check` returns no error. Set membership equates 2.0 with integer 2, and no exact integer check precedes component extraction. This is a validator hole on a deliberately mutated grid, not evidence that ordinary generation emits floats. Reject non-integer ARC cells before geometry checks.

Evidence: `checks/audit/05b5a82ace36/{probe.py,report.json,inputs.json,python_reference_outputs.json,rival_outputs.json,float_pixel_input.json}`. Input-list SHA-256: `2ddebae5267108e345929c9104026a47c7188910c3dc8b9063ce89f7df9e08ca`.

## Supported Racket confirmation still to run

From the outer extraction directory, sequentially:

```sh
python3 review.py run python3 -m arcpuzzles apply ebd08d719ed6 --input ../checks/audit/ebd08d719ed6/inputs.json --reference canonical --check-generator-domain --timeout 120 --out ../checks/audit/ebd08d719ed6/racket.json
python3 review.py run python3 -m arcpuzzles apply 05b5a82ace36 --input ../checks/audit/05b5a82ace36/inputs.json --reference canonical --check-generator-domain --timeout 120 --out ../checks/audit/05b5a82ace36/racket.json
python3 WORK/checks/audit/verify_racket.py
```

There are eleven total inputs (seven and four). These commands were prepared from the actual CLI schema; this subagent has not run them because root is serializing the shared Racket resource. The comparison helper refuses to claim confirmation if a receipt is missing, a source/rule pin differs, an input differs or any Racket output disagrees with the Python interpretation. No full battery or corpus rerun is requested.
