# Working notes: 5e8e4691afde

## Current authority

- The canonical/default rule remains unchanged at normalized rule hash `ee2251228926`: move the framed center by the indicator-path vector, preserve the colored center, and draw the 3×3 frame plus both complete diagonals through its new center.
- Production generator baseline SHA-256 was `75d65fd7c77bcc8ee14c5e007d1efb94db747cd4725216f9d00748dacffd76b8`; the strict-boundary repair is `8a564c3cd700d2de4e2af7385a762998932d2f8ac009e9187473ddb12ca55b08`.

## Current decisions

1. The public `generate` boundary accepts only exact integers for `seed` and `sample_index`, rejects booleans/coercible scalars, rejects negative sample indices, and continues to allow negative integer seeds. Validation occurs before context construction so invalid values cannot enter deterministic generation state.
2. Task tests locate canonical/base data with `reviewer_support.find_root` and `canonical_path`, so relocated review runtimes exercise the same source. Canonical/base Racket identity is whitespace-normalized, while base raw/target equality and the pinned normalized rule hash remain exact.
3. The proposed parameter is a separate prototype, not a production axis: episode-fixed `diagonal_mode ∈ {both, falling, rising}`. `both` is byte-for-byte canonical; alternatives change only the unique diagonal predicate. Each retained setting has two demonstrations and four distinct queries, with labels and declared rivals executed by Racket.
4. Public prototype IDs hash only exact visible bytes. Hidden settings, seeds, programs, rival predictions, and query outputs stay in private evidence; duplicate visible payloads are rejected.

## Evidence and limits

- Focused task suite: `16 passed, 33 subtests passed`; canonical default replay: `5/5`; focused strict-scalar defect lint: `FLAGGED 0` after reproducing 33 invalid acceptances before the repair.
- Materialized prototype evidence is under `checks/parametric/5e8e4691afde-diagonal-mode-v1/` and includes exact Racket programs, private episodes, three visible-byte public challenges, a setting map, a pairwise-distinguishing witness, and a hash manifest.
- Identifiability is bounded to the two declared diagonal-mode rivals and the retained finite episodes. This does not prove unique induction against every program, approve a production parameter, alter the canonical rule, or admit data to training.
- Next useful owner action: replay the focused suite from the returned patch, then decide whether the isolated parameter deserves a separate production-axis/curriculum review. Do not infer that decision from this prototype evidence.

Imported historical evidence remains in `evidence/associated_notes.jsonl`; this file records only the current source-bound decisions.
