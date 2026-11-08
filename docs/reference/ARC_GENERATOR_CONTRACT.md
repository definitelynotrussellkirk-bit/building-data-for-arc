# ARC Generator Contract

This contract is for synthetic task/variant generators that expand the base
solution corpus. It is separate from solver generators that expose
`solve(task)`.

The goal is to generate rows that can be trusted for training:

- visible task image + samples -> description
- visible task image + samples + description -> Racket code

Every generated row must carry the Racket oracle and the exact canonical
function inventory used by that oracle. The verifier executes the oracle
against generated train pairs and expected test outputs before the row is
accepted.

## Module Contract

Each generator module must expose:

```python
GENERATOR_ID = "periodic_denoise"
VERSION = "0.1.0"
SPEC_VERSION = "arc-generator-1.0"
BASE_TASK_IDS = ["0607ce86"]
CANONICAL_FUNCTIONS = ["grid-ref", "grid-positions", "paint-cells"]
TAGS = ["period", "denoise", "majority_vote"]
VARIANT_POLICY = "Vary period, palette, tile entropy, and bounded noise while preserving a unique periodic reconstruction."
PARAMETERS = {
    "row_period": "4..8",
    "col_period": "5..10",
    "noise_count": "0..12",
}
SUMMARY = "Generate periodic-grid denoising tasks with a Racket oracle."
RAISON_D_ETRE = {
    "capability": "Infer a global periodic template despite sparse corruption.",
    "ambiguity_removed": "Separates denoising from local copying shortcuts.",
    "retirement_criterion": "Merge only into a verified superset family with stronger identifiability."
}
```

Required:

- `GENERATOR_ID`: stable lowercase identifier, matching `^[a-z][a-z0-9_]*$`.
- `VERSION`: bump when generation semantics change.
- `SPEC_VERSION`: must be `"arc-generator-1.0"`.
- `BASE_TASK_IDS`: canonical seed tasks this generator is derived from.
- `CANONICAL_FUNCTIONS`: union of canonical Racket functions used by every
  oracle path this generator can emit.
- `TAGS`: routing and curriculum tags.
- `RAISON_D_ETRE`: why the family exists, which ambiguity it removes, and when
  it may be retired or merged. New model-facing primitives, fixed constants,
  objectives, and verifier rewards follow the same rule.
- `VARIANT_POLICY`: short statement of what is allowed to vary and what must
  stay invariant.
- `generate(seed: int, sample_index: int = 0, *, difficulty: str | None = None)`.

Recommended:

- `PARAMETERS`: machine-readable parameter ranges.
- `SUMMARY`: one-line human summary.

### Official source-lineage requirement

The corpus goal is two to four independently validated generator families per
supplied ARC puzzle (1,000 training plus 120 evaluation). `BASE_TASK_IDS` must
therefore name supplied 8-hex ARC source IDs, not generated content hashes.
Generated IDs remain in `GENERATOR_ID`.

Accepted relationships are exact seed, semantic variant, composed variant, and
adversarial variant. A mapping counts only when the generator preserves an
explicit latent transformation and evidence distinguishes that relationship
from superficial visual similarity. Record durable mappings in
`data/derived/official_generator_lineage.jsonl` and audit them with
`scripts/audit_official_generator_lineage.py`.

Each reviewed family also supplies structured Qwen supervision: a concept
skeleton, ordered plan steps, and candidate ARC-Racket v2 primitives. This
metadata never replaces executable Racket verification.

## Generated Row Contract

`generate(...)` must return a JSON-serializable dict:

```python
{
    "base_id": "0607ce86::periodic_denoise:v0",
    "task": {
        "train": [
            {"input": [[...]], "output": [[...]]}
        ],
        "test": [
            {"input": [[...]]}
        ],
    },
    "expected_test_outputs": [
        [[...]]
    ],
    "description": "Recover the clean periodic tile by majority vote, then fill every cell from that period.",
    "racket_oracle": "(rule! ...)",
    "canonical_functions": ["grid-ref", "grid-positions", "paint-cells"],
    "parameters": {
        "seed": 1,
        "sample_index": 0,
        "row_period": 5,
        "col_period": 7,
    },
}
```

Rules:

- `task.train` contains input/output pairs.
- `task.test` contains inputs only. Test outputs live only in
  `expected_test_outputs`.
- `description` is a target description, not a hidden-output leak.
- `racket_oracle` must be one top-level `(rule! ...)` form.
- `canonical_functions` must exactly match the oracle's mined canonical
  function inventory for this generated row.
- Module-level `CANONICAL_FUNCTIONS` must include every function used by every
  generated row sampled by the verifier.

## Verification

Run:

```bash
python3 scripts/verify_arc_generator.py path/to/generator.py
```

Useful options:

```bash
python3 scripts/verify_arc_generator.py path/to/generator.py \
  --seed 1 --seed 2 --sample-index 0 --sample-index 1 \
  --jsonl tmp/arc_generator_verify.jsonl
```

The verifier checks:

- module metadata and spec version;
- generated row schema and JSON serializability;
- grid validity and test-output leakage;
- determinism for each `(seed, sample_index)` pair;
- exact generated-row `canonical_functions` vs Racket oracle inventory;
- module-level `CANONICAL_FUNCTIONS` coverage;
- Racket parse/load;
- every generated train pair via `(test! i)`;
- every expected generated test output via `(apply! i)`.

Warnings become failures with `--strict`.

## Acceptance Rule

A generated row is not training data until it passes the verifier with Racket
execution enabled. Static-only checks are for authoring convenience, not for
corpus admission.

Generated variants should not be written into `data/base/solutions/`. Store
them in a separate generated dataset and retain `base_id` lineage back to the
canonical seed.
