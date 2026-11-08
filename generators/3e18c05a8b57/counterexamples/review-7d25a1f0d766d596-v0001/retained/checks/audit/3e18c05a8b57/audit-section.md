## 3e18c05a8b57

**Disposition: reproduced override-contract defects; no generated-label defect found in the checked scope.** Target VERSION `3.1.0`, unchanged source SHA-256 `5eaa7c3fe9035512e48058ddada053edae8ac4b8d3864dfedf0ff135d526e3fc`. Public canonical execution reports normalized rule hash `7e0d6124668b` and wrapped-callable SHA-256 `dcbb66e6c4aa8841b7ff90bde81811a72ba701f917037d7ef2e658eb3fc198a2`.

### A1 — Advertised exact controls are silently ignored

At `seed=17, sample_index=0, difficulty="easy"`, each of `palette_size=4` and `n_distinct_colors=4` returns exactly the default grid: its colors are `{0,8,9}`, with only two foreground colors. `self_check` returns `[]`. The claimed four-color count is unmet whether background is counted or excluded. The same call with `palette_kind="warm"`, `palette_kind="cool"`, `texture="warm"`, or `texture="cool"` also returns that identical grid; the generator never consumes these advertised controls. An unknown `audit_unknown_key=123` is also silently ignored. The source explains the observation: palette construction is an unconditional sample from a fixed eight-color list.

Implement the advertised controls and observable count contract, or remove unsupported axes and reject requests for them. A helpful-texture name should select a real distribution change or explicitly document its equivalence; it should not imply an implemented palette mode.

### A2 — Declared dimension endpoints reject

The same easy call rejects `grid_h=7`, `grid_h=14`, `grid_w=9`, and `grid_w=16` although `AXES` advertises height 7..14 and width 9..16. Errors identify the narrower easy-band ranges `[8,9]` and `[10,11]`. Reconcile the declared exact-override domain with difficulty-dependent sampling. These are reproducible API-contract failures, not incorrect Racket labels.

### Shortcut and executed scope

The plausible shortcut “crop color 2” fits **all 5 canonical records**. It is already refuted by **all 18 generated inputs** checked here (six fixed draws in each band). A concrete generated witness is retained in `checks/audit/3e18c05a8b57/color2-counterexample.json`; its expected label comes from fresh canonical Racket execution, cross-checked with an independent four-neighbor symmetry/crop implementation. Thus this canonical color shortcut is **not** an observed generator coverage defect.

The three-command probe checked 11 exact override requests and executed canonical Racket on 23 inputs: five canonical records and 18 generated inputs. All 23 labels matched canonical labels or the independent symmetry oracle. All checked inputs passed `self_check`. This small audit does not establish broad sampling correctness or lesson identifiability; no full battery or lesson census was run on this audit target.

Reproduction is `reproduce.py prepare`, public `arcpuzzles apply` on `inputs.json`, then `reproduce.py compare`, all through `review.py run` using the pinned review environment. The exact commands, source hash and exit-0 receipts are in `checks/audit/3e18c05a8b57/command-rows.json`. `observations.json`, `comparison.json`, `case_manifest.json`, `racket.json`, and the logs retain every tested call and label. The target generator, notes, canonical rules and tests were not edited.
