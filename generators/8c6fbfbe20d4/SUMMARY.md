# 8c6fbfbe20d4

Rows 0 and 1 are independent sparse color lists: scan each row left-to-right and discard zeros. Pair the first min(source_count, target_count) entries. Rows 2+ are the body. The output removes both header rows, recolors paired source values, and preserves zeros, unpaired sources, target-colored distractors, and other unmapped body values.

Kind: `per_puzzle`. Imported version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.

Teaching schedule: every default four-example lesson includes both a target-colored body control and a truly neutral body color absent from both headers, so preserving arbitrary unmapped values is identifiable.
