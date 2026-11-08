# Retained counterexamples

- `identity_all_axis.json` preserves the old failure: an all-axis input is unchanged by the authority and therefore teaches identity. Version 2.0.0 rejects it.
- `semantic_witness.json` is a lawful minimal teaching witness. Its output disagrees with every rival declared in `SEMANTIC_RIVALS`.

`tests/test_generator.py` loads both files, so these examples remain executable rather than prose-only evidence.
