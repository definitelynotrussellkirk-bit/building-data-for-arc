# Working notes: a89702404b3c

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/a89702404b3c/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Current reviewed state — 2026-10-25

The selected canonical default is unchanged byte-for-byte: odd widths return the top-left 2×2 crop and even widths return the top-right 2×2 crop. The base generator now rejects booleans, integral floats, and strings for integer controls; its portable tests use packet runtime discovery; and `strict_canonical_like` exposes the complete structural validator to semantic review.

The native parametric family adds `rule_mode=corner_key_payload`. Step A performs the canonical parity crop; its upper-left color is the input-derived key. Step B finds that key in an independently permuted marker row and returns the 2×2 payload below it. Three demonstrations are required: two odd-width scenes reverse the key-to-payload placement, while a third even-width scene teaches the other parity branch. Four query inputs are retained, including a substantive dense 30×30 case. The canonical setting remains `corner_crop`.

Current limits: demonstrations 3–6, queries 1–4. Qualification and owner acceptance are separate; this task-local source remains owner-pending until the exact integrated bytes are reviewed and accepted.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-0fd77e2c8a314ae1:v0001`. Disposition: **resolved**. Evidence basis: focused copied-runtime tests retained in `workspace/parametric/evidence/current/` and the packet check `checks/a89702404b3c-tests-final/result.json`.

Audited source SHA-256: `2e9083095100031917f1798441fa439cf74cf72eb5803ce425a6b6340b38b5a7`. The audited source differs from the current source; this assessment covers the reported defects and their direct regressions.

### Current decision

The scalar-validation defect is fixed by exact-type integer checks, the staged-runtime path defect is fixed by `reviewer_support` discovery, and the missing semantic contract is fixed by `strict_canonical_like`. Regressions exercise each invalid scalar class, all canonical pairs, generated lawful inputs, and malformed inputs. The original audit did not assess the new parametric family; its separate manifest, authoring qualification, and causal witness remain the relevant evidence for that work.

### Prior finding

The former generator accepted integral floats such as `palette_size=6.0`, failed inconsistently for other invalid scalars, used a nonportable test path, and declared no semantic review hook.

This disposition records a bounded source repair. It does not imply universal correctness, owner acceptance, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
