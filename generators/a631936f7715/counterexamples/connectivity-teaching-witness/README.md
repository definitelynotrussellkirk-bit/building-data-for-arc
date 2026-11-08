# Diagonal-connectivity teaching witness

Two magenta dominoes touch only at a corner. Under the selected four-connected
rule they remain separate and inherit their distinct orthogonal label colors.
The named eight-connected rival merges them and, under its documented
smallest-label tie break, paints both dominoes color 3.

Files:

- `input.json`: lawful 4×4 input accepted by `self_check`.
- `expected.json`: selected four-connected output.
- `eight-connected.json`: declared rival output.
- `provenance.json`: source/rule binding and hashes.

`tests/test_generator_contract.py` replays all three files.
