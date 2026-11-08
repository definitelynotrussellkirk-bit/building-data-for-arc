# Blind visible-only solve work log

## Access and scope

I read only `WORK/solve-blind/README.md` and `challenge.json` as task evidence.
I did not consult the generator, Racket rule, canonical data, reference solver,
private labels, audits, or earlier solution notes. Earlier rule exposure: no.
Reference consulted: no. All authored files are in `WORK/solve-blind/`.

This is an agent work log of hypotheses, experiments, and revisions, not a
token-level transcript. Official checks will be preserved by the blind checker.
Private query correctness is unavailable and is not claimed here.

## Initial inspection

Each input has a nonzero top-left pixel separated from a small foreground
pattern. The output retains the pattern's colors and counts, excludes the
top-left pixel, and matches the tight bounding rectangle of the pattern after
a geometric transformation. I therefore treat the top-left pixel as a selector,
remove that coordinate only, and crop the remaining nonzero cells. Removing
every pixel of the selector's color would be an unsupported extra assumption.

The observed mapping, inferred directly from the five examples, is:

| Selector | Proposed operation | Example input dimensions | Output dimensions |
|---|---|---|---|
| 1 | Identity | 9 rows x 10 columns | 3 rows x 3 columns |
| 2 | Rotate 90 degrees clockwise | 10 rows x 10 columns | 3 rows x 3 columns |
| 3 | Rotate 180 degrees | 8 rows x 9 columns | 2 rows x 3 columns |
| 4 | Transpose across the main diagonal | 9 rows x 9 columns | 3 rows x 2 columns |
| 5 | Reflect left-right | 8 rows x 8 columns | 3 rows x 2 columns |

My first impression from selectors 1, 2, and 3 was an ordered rotation code.
Inspection of selector 4 rejected that conjecture: its output is the transpose,
and differs from a 90-degree counterclockwise rotation. This was a reasoning
revision during inspection, not a failed official check or failed implementation.

## Unseen selector and independent reasoning check

Test query 0 has selector 6, absent from the training examples. I choose a
top-bottom reflection because it naturally pairs with the observed left-right
reflection for selector 5. This is underdetermined. Even if all selectors denote
distinct rectangle symmetries, counterclockwise rotation and anti-diagonal
reflection are also unused and cannot be ruled out by the visible examples.
The numbers themselves establish no unique convention.

A second reasoning agent was given only the five cropped input/output pairs
and the selector-6 query crop in its prompt, with explicit instructions not to
read files, sources, or the web. It independently confirmed the five observed
mappings, preferred the same extrapolation for selector 6, and stressed the
same ambiguity. That agreement does not add evidence about the private answer.

Test query 1 uses observed selector 3 and therefore has substantially stronger
support for a 180-degree rotation of its crop.

## Initial implementation and intended check

I implemented the inferred crop rule and the five observed transformations,
plus the explicitly uncertain selector-6 reflection. The solver does not mutate
the input. Empty payloads return an empty list; unsupported selector values
raise an error. Neither edge behavior is established by the visible examples.

Before the first official check I will enumerate all eight rectangle symmetries
against each visible pair, then check `solve(grid)` against all five outputs.
The purpose is to catch orientation or cropping errors and to test whether any
visible pair leaves its own selector ambiguous. No private correctness feedback
will be requested or interpreted.

## Local experiment result

The eight-symmetry enumeration gives exactly one matching operation for each
visible pair, confirming all five observed mappings. The initial candidate
exactly matches all five visible outputs. Full local result: `VISIBLE_PROBE.txt`.
No hidden-output comparison was performed. There was no failed local candidate
or failed official check before this result.

I will now submit the first official blind check without changing the candidate.
