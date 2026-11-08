# Working notes: 959992fc8fa9

## Current decision — review-eabacf141829ac47

Built a native two-setting family under `workspace/parametric/`.

- `intersection_policy=different_red` is the exact canonical program (SHA-256 `169b27f394fc51119c2ee69dff8134d328a9812a4a2b62f2c2abc90b04c8741a`).
- `intersection_policy=repeated_color_priority` keeps matched inputs but makes the unique source color occurring twice win mixed intersections that include it; other mixed intersections remain red 2.
- Sequential dependency: A counts source colors and recovers `priority_color`; B consumes that input-derived value while resolving every mixed intersection. A protected-Racket wrong-intermediate replay changes the selected query by 10 cells.
- Two demonstrations constructively distinguish both declared settings and reject six retained shortcuts. This is a finite rival audit, not universal uniqueness.
- Counts are independent (2–6 demos, 1–4 stable query prefixes); query 4 is a genuine 30×30 boundary case. Public IDs use only masked public bytes.

The existing authority export minifies whitespace while preserving the same parsed Racket form. The focused authority test now requires its `raw_code` and `target_code` to be byte-identical to each other and structurally identical to the canonical ledger program, rather than requiring the export's formatting to match the ledger.

Reviewer qualification passed for both settings on seeds 0 and 17 with four queries (40 protected-Racket evaluations). Owner exact-source acceptance and training admission remain pending; the next action is owner integration, fresh native qualification on live bytes, then `parametric accept` if that replay remains green.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/959992fc8fa9/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
