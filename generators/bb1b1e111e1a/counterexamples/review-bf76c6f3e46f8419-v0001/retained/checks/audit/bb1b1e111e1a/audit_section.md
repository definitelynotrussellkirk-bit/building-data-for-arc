## bb1b1e111e1a

**Findings-only audit; selected target source unchanged.** The current source is SHA-256 `70aab6d4d8228c7f1ac306161229c087837cd9013a06aebd6031aa2e1df209af`. Existing `evidence/review_index.json` marks the identity/density findings unresolved on these same bytes. This audit reproduces them; it does not claim they are newly discovered or resolved.

### B1 — The advertised identical-panels texture does not make identical colored panels

At seed `audit-bb1-20261023`, sample index `0`, difficulty `None`, overrides `{"texture":"identical_panels"}`, the generator returns a 5×17 input whose A/B occupied coordinates match but whose colors are 2 and 6. Thus A != B. Both direct `self_check` and public reference-domain checking accept it.

Source lines 9–10 and 152–156 promise A == B and a mask-independent answer, but line 139 assigns different panel colors and line 156 passes those distinct colors to the assembler. Actual canonical Racket output differs from both A and B. This is a named-branch invariant failure, not an incorrect Racket label: the actual output agrees with the ordinary cellwise mask selector.

Exact input/output are row 0 in `checks/audit/bb1b1e111e1a/racket.json`; the recipe is case 0 of `probe.json`. Input SHA-256 is `a4b11aabc58cf54325b6125456960cdb96e1aa22d8208e41750c8c8a823e7342`; output SHA-256 is `1476d01be7e076a83d854b80ffd802b63817b22fd9bcbf364c5c21606197add0`.

### B2 — Advertised mask-density override remains unused

At the same seed, indices 0–2, difficulty `None`, fixed `grid_h=4, panel_w=4`, compare `mask_density=0.1` against `0.9`. **All 3/3 paired complete input grids are equal**: six calls, three unique paired grids. Input rows 1–6 and `probe.json.density_pairs` retain each comparison. The source declares density on line 45 but directly draws `rng.uniform(0.3, 0.7)` on line 100 instead of consuming the override. The exact equality plus the code establishes an ignored control; this is not a statistical density estimate.

### B3 — Public dimension domains exceed the implemented default override bounds

The axis contract at lines 43–44 advertises `grid_h=3..10` and `panel_w=3..9`. At the same seed, index 0, difficulty `None`, each of `grid_h=3`, `grid_h=10`, `panel_w=3`, and `panel_w=9` raises `ValueError` reporting the requested override is outside `[4, 7]`. A positive control with `grid_h=4, panel_w=4` generates a valid 4×14 input. Exact requests and exception text are in `probe.json.dimension_endpoint_probes`.

This is a declared-domain/default-call mismatch. In addition, the normal easy/medium/hard branches never allow height 3 or 10, or panel width 3. Panel width 9 is supported by the hard branch. No input or Racket output exists for the four rejected requests, and none is fabricated.

### Reference checks and limits

Public `arcpuzzles apply` completed on **10/10 requests, containing 7 unique inputs**: the identity witness, six density requests, and one ordinary example in each difficulty band. Every actual Racket output matched an independent `mask != 0 ? A : B` selector. All ten domain checks were valid. This is bounded semantic evidence; no broad battery, lesson census, canonical-pair sweep, or universal correctness claim was made.

The receipt reports catalog/executed rule ID `00da4b1016cc`, agreement `true`, and exact executed rule-text SHA-256 `14ba31e9cd328aa345ee89d7e1f1673e8cec2678081b475b155d73ad406b73a1`. Generator hashes were checked before generation and against the public receipt and live source afterward.

Evidence directory: `checks/audit/bb1b1e111e1a/`. `probe.py` records exact recipes and inputs; `input.json` feeds the public reference; `racket.json` preserves all actual outputs; `summarize.py` asserts source/input binding and writes `summary.json`; `commands.json` records actual commands, working directories, and exits. The three substantive runtime commands exited 0. An initial broad file search returned 2 for a nonexistent optional path and a Git status check returned 128 because this extracted packet is not a Git checkout; neither is a target defect.

Suggested owner action: consume density controls; make the identical-panels branch copy complete colored contents and define branch-aware validation; honor declared dimension overrides independently of default difficulty draw ranges, or describe narrower supported domains accurately. No target code was edited, no unresolved audit was cleared, and no approval or training admission was granted.

