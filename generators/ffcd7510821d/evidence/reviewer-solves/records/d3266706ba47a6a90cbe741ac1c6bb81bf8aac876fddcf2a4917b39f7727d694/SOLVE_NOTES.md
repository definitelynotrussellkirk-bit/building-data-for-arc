# Visible-example solve work log

This is an assistant-authored summary of actual experiments and one submitted
Python solution revision, not a captured Qwen conversation, token-level trace,
log-probability record, or evidence of an independent blind solve.

**Earlier rule exposure: yes.** I reviewed the generator and canonical authority
before preparing this fresh episode. **Reference consulted during solve: no.**
After preparation I used only `challenge.json`, public-example Python experiments,
and the supplied visible-only checker. I did not read generator/reference source,
previous solution explanations, or masked-query labels during this phase.

## Public observations and experiment

The four visible inputs have 3, 4, 1, and 2 top-row gray (9) markers, respectively.
There is blank space separating this row from the content. The first and third
examples preserve multiple content colors and their relative spacing; they do not
select just the largest object. Output dimensions agree with a tight content crop,
possibly transposed by a quarter turn.

`visible_probe.py` removes only the top-row marker cells, computes the full
nonzero-content bounding box, and enumerates the four clockwise rotations. It
found exactly one matching rotation for each public demonstration:

| Demonstration | Marker count | Matching clockwise quarter turns |
|---|---:|---:|
| 0 | 3 | 3 |
| 1 | 4 | 0 |
| 2 | 1 | 1 |
| 3 | 2 | 2 |

The retained experiment is `checks/solve-visible-probe.json`. The public query
marker counts are 3 and 4, both represented among the demonstrations. This
supports applying the same crop-and-rotate rule, not a claim that its masked
answers have been checked. Fixed rotation, reverse-direction rotation, and
largest-object-only behavior would not fit all four visible examples.

## Implementation and verification

Before implementing, the local public-example tests encountered the preparation
tool's `NotImplementedError` scaffold. That is retained as a test-development
failure in `checks/solve-tests-red.log`; it is not a submitted failed solve or an
intentional teaching negative. No wrong solver was manufactured for a preference
pair.

Revision 1 implements non-mutating tight cropping and count-modulo-four clockwise
rotation using the Python standard library only. It validates rectangular ARC
inputs and does not import any repository module. The local tests check all four
visible input/output pairs, input immutability on all six public inputs, and
malformed-grid rejection. The supplied checker records the sole actual submitted
attempt, with intent `solve`. No subsequent algorithm revision was needed.

Stopping criterion: the visible examples agree and the implementation executes
on the public query inputs. Masked-query correctness is deliberately withheld;
independent maintainer scoring is still required. Training admission is not
claimed, and these notes are not a Qwen training performance measurement.
