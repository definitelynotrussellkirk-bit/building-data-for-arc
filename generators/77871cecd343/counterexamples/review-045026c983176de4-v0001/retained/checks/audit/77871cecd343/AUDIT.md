## 77871cecd343

**Reproduced existing current-source finding: default dimensions and the horizontal divider predict the vertical divider.** This audit independently confirms the unresolved schedule-correlation lead already retained in `repo/generators/77871cecd343/evidence/review_index.json`; it is not a new distinct defect. Findings only; the target generator, rule, notes, catalog and shared files were left unchanged.

### Source identity

| Item | Hash |
| --- | --- |
| Selected `repo/generators/77871cecd343/generator.py`, version 2.1.0 | `5e1fdbc628e7c565974c9cfeacef0d6fbe5b412ce9ab23a6f45a94ffe4ff0aca` |
| Catalog and actual Racket rule | `1bad9bf6a465` |
| Canonical ledger row, excluding newline | `56ccb1c6c0a682e5ec1a6009de1bae41d2ce07d49897f86c443cf650619d85fc` |
| Raw canonical rule text | `87a6a2aef09221ccf468dff7e29a8f5ee9fd572d9a587e5940771c21cab91206` |
| Executed wrapped rule text | `ea17fb917a7ef76bb5cbfa2a64391591a477f9bd9e362432d164457b505c3029` |

Read the selected generator, complete notes, canonical row (bank `3cb9777539c7`, original ID `M147`, ledger line 2240), and relevant prior audit entries. The source hash is asserted on both probe invocations and independently reported by public apply. No private runner imports or blind/private solve material were used.

### Mechanism and retained witness

The six-entry dimension schedule and nine-entry offset schedule share a period-three factor. Canvas dimensions reveal the phase modulo three; within each group the visible horizontal divider's offset identifies the vertical divider's offset. A rival can therefore infer an off-center vertical axis from dimensions plus row offset, without locating that vertical divider. `probe.py:rival` implements this lookup with a centered-cross special case that fits canonical data.

| Dimensions, height × width | Column offset for row offset −1 / 0 / +1 |
| --- | --- |
| 9×9, 11×11, 13×13 | +1 / 0 / −1 |
| 9×11, 13×9, 13×11, 15×13 | −1 / −1 / 0 |
| 11×9, 9×13, 11×13, 13×15 | 0 / +1 / +1 |

The witness is **actually generator-produced**, using `seed=7787199`, `sample_index=1`, `difficulty="medium"`, `grid_w=9`; it is not merely validator-accepted. It passes `self_check` and exposes all advertised exact controls. Its axes are `(3,3)` on a 9×9 grid, with offsets `(-1,-1)`, five connected source cells in the top-right quadrant. The rival guesses `(3,5)` and differs from actual Racket at **16/81 cells**. Full input, actual output, rival output, controls, axes and cell differences are in `checks/audit/77871cecd343/counterexample.json`. It is input/result index 59 in the public batch.

### Tested scope and result

The small public Racket batch contains 60 inputs: 18 consecutive default phases (`sample_index=0..17`, seed `7787100+index`, no overrides) for each of easy, medium and hard; all five labeled canonical pairs; and the override witness. Eighteen phases exhaust the default dimension/offset joint period. Shape randomness and the source quadrant do not enter the lookup proof; this is not an exhaustive shape or override census.

- **54/54 defaults:** valid, deterministic on regeneration, rival output equals actual Racket.
- **5/5 canonical pairs:** valid; stored output, rival output and actual Racket agree.
- **1/1 override witness:** valid; rival differs from actual Racket in 16 cells.
- **60/60 public Racket applications:** no per-input execution error; independent coordinate reflection equals actual output throughout. Public apply reports `rule_hash_matches_catalog: true`.

No Racket-label discrepancy was found in this bounded batch. The defect concerns default curriculum support: the sampler's declared rivals do not cover this surviving canonical-fitting shortcut. No additional independent issue is claimed, and no lesson assembly or broad battery was rerun.

**Actionable repair:** decouple dimension choice from the joint row/column offset schedule so identical dimensions and horizontal-divider positions can produce different vertical-divider positions. Add this rival and its generator-produced override witness to semantic regression coverage. Existing unresolved findings should remain open until a source-bound repair check demonstrates that decoupling.

Reproduce using the three exact argv arrays in `checks/audit/77871cecd343/commands.json`: prepare, public apply, analyze. Paths there are relative to `WORK`, with `packet_root` denoting its outer extraction. Apply requires a fresh output path on replay. `probe.py` is runnable through the supported wrapper and uses only public reviewer helpers; the authority output is `racket.json`, and compact counts/hashes are in `summary.json`.
