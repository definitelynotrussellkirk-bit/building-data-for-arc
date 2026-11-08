# Working notes: 483682b75e12

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/483682b75e12/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Review b468dd0695d7139e — native parametric candidate

Built a separate two-setting family without changing the production generator or canonical authority. `motion_mode=own_size` is the exact canonical rule. `motion_mode=complement_to_largest` first computes the input-dependent largest component size `K`, then moves each component of size `s` upward by `K - s + 1`.

The adapter supports 2–6 demonstrations and 1–4 prefix-stable queries on matched visible inputs. The bounded audit covered 320 lessons, 2,560 visible pairs, 3,840 declared-rival checks, 1,280 cross-setting query disagreements and 320 actual 30×30 queries; its protected-Racket dry run used 40 evaluations. Native qualification passed both settings at seeds 0 and 17 with 40 protected-Racket evaluations. A source-bound causal witness substitutes `K+1` for `K` and changes 14 final cells while keeping input geometry and colors fixed.

The copied-runtime test was repaired to locate canonical data through `reviewer_support` instead of a fixed checkout depth. Fresh task tests: 39/39. Production generator SHA-256 remains `189fbe70222e7cb05feeb7114eb0ad2a3f4f557e532cf23e3ea0a8c686979f7e`; canonical program SHA-256 is `1ecd0b9f4b26f707a759a230df287a997b214b82103aad8d3ba3db4a3d582e3f`; alternate program SHA-256 is `aa40600b5ef5806a2758ac64a66cf4fd00035bfd3580364ddc71388ac86da221`.

Status is reviewer-reported `ready`, not accepted. Next action: integrate the exact source, replay native qualification and the causal witness, then record owner acceptance. Training admission remains false.
