# Allocation-quality probe

Seed: `9bc134f1609b62f979f7550c46c63f25f0b6c0a58e99161be9f16eaa2f665372`
Sample: `548c1010ce89, 6fde852adb54, f3076f3858b4`

## Current policy

The authoring draw uses a 10% evaluation-focus branch and a 90% uniform normal branch over 162 IDs. Dataset weights are a separate mechanism.

## Sample findings

- `548c1010ce89`: approved=True, train_safety=reviewed_safe, dataset_weight=1.0, normal_pool=True, open_audits=2, parametric_artifact=False, four_query=False, source=official_or_augmented_arc.
- `6fde852adb54`: approved=True, train_safety=reviewed_safe, dataset_weight=0.0, normal_pool=True, open_audits=0, parametric_artifact=False, four_query=False, source=official_or_augmented_arc.
- `f3076f3858b4`: approved=False, train_safety=unverified, dataset_weight=1.0, normal_pool=False, open_audits=1, parametric_artifact=False, four_query=False, source=internal_bank.

The notable mismatch is concrete: a reviewed-safe record has weight 0, while an unverified record with an unresolved domain/validator audit has weight 1. Another full-weight reviewed-safe record retains unresolved teaching ambiguity. All three derived catalog rows predate their current source versions.

## Bounded alternative

Keep the 10% evaluation-focus branch unchanged. In a 30-assignment experiment, use 3 focus assignments and 27 normal assignments; stratify 6 of the normal assignments across open teachability evidence, weight/safety mismatches, and missing parameter/four-query evidence, leaving 21 uniform. Compare six targeted assignments with six matched uniform assignments.

Adopt only if targeted allocation yields at least 1.25x accepted ambiguity-free, Racket-replayed, deduplicated four-query episodes per reviewer-hour without a higher failure rate. Stop after three matched pairs if yield is <=0.5x or cost exceeds 2x; always stop at 30 assignments.

## Limits

- Only three assignment-seeded records were inspected; rates and effect sizes are unknown.
- No sampled record is ARC-GEN or RE-ARC, so this probe supports no source-specific conclusion about either corpus.
- Derived generator_catalog rows are stale relative to all three sampled source versions; lint/axis metadata are treated as leads, not current verdicts.
- Dataset weights are reported as stored and are not authoring draw probabilities.
- No corpus-wide rerun, model job, new approval, or training-policy change was performed.
