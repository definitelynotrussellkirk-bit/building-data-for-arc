# Current review decisions: dafb4f819b93

## Production source

- The selected canonical Racket rule remains unchanged: rule hash `6bb5aaacd2ec`, exact source SHA-256 `fd28f01b9690c2b68a529d5ecb88df555c53e93cc5254d1f6662017f1fdcf6cc`.
- Generation behavior is unchanged. `generator.py` now declares the missing executable semantic contract only: `strict_canonical_like`, matched/asymmetric branch witnesses, two axis-confusion rivals, three lesson competitors, and `lesson_identifiable` label checks.
- Final generator SHA-256 is `4cb2197b77338fd386373618400ef0e81be47b5a9cbc9e58f1e4c463d83e4b1b` (baseline `76a6435587f8b973716e6581f0f99cdec9e1e7c88c992aef3e8e51ffb6cb91c3`).
- The retained test suite no longer depends on a fixed repository depth and no longer reads private `ctx._drawn`; it uses packet-root discovery, the source-bound selected-generator loader, canonical-pair helpers, and `axis_value`.

## Proposed parametric extension

- `workspace/parametric/prototype.py` is **proposed and unapproved**. It does not change production generation, the canonical authority, approval, or training admission.
- One rule parameter is fixed once per episode: `label_offset ∈ {0,1}`. Offset `0` is byte-identical to the canonical equality rule. Offset `1` paints a row where the column label is the next color in the cyclic right-border palette, using the row label as paint.
- Each retained episode has 3 demonstrations and 4 distinct queries. Inputs are sampled independently of the hidden parameter, all outputs are executed by Racket, query answers remain private, and public IDs hash only the exact visible challenge bytes.
- The verifier checks an exhaustive file manifest, exact rule snapshots, a freshly recomputed distinguishing witness, canonical replay, public/private projection and IDs, fixed episode parameters, pair hashes, report counts, Racket labels, current prototype hash, and current selected-generator path/hash plus deterministic input regeneration.

## Evidence and limits

- Final packet-native audit: 44 pytest cases plus 12 subtests passed; strict semantic gate and required query rotations passed.
- Retained prototype evidence covers both settings in 2 episodes, 6 demonstrations, 8 queries, 4 canonical pairs, and 0 surviving declared parameter ambiguities.
- Bounded adversarial work checked 768 maximum-count inputs, forced and recovered a retry collision, rejected an over-limit count, and rejected public and hidden-answer tampering after manifest recomputation.
- Finite evidence covers only the declared two settings and retained seeds; rival checks do not rule out arbitrary programs. Maintainer review is still required before any approval or training use.
