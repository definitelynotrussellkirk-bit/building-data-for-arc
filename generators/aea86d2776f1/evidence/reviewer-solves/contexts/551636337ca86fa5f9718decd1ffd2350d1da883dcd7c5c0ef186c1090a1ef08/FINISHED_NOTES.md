# Blind visible-only solve notes

Task: `aea86d2776f1`.

## Exposure and source limits

I started this solve without earlier rule or reference-solution exposure. I ran
`python3 review.py blind prepare`, then read only this episode's `README.md` and
`challenge.json`. I have not opened the generator, canonical data, rule files,
private labels, audit evidence, reference solutions, or another solve. The
reasoning below uses only the three visible training examples and two visible
query inputs. Query output correctness is unknown to me.

## Observations and hypotheses

All visible inputs contain two 3-by-3 tiles in rows 2 through 4, at columns 1
through 3 and 7 through 9. Four nonzero header values occur in row 0, columns
1, 3, 7, and 9. All visible outputs are four 3-by-3 tiles combined into a 6-by-6
mosaic.

I first considered sorting the header numbers to place transformed copies of
the tile beneath each header. That explains the source order in training
example 0, but not training example 1: its output has three copies of the left
tile and one of the right although there are two headers over each source. I
rejected this hypothesis during inspection before writing implementation code.

Reading the four headers left to right as instructions for output quadrants
in row-major order yields a consistent mapping in every visible training
example:

| Code | Source tile | Transformation observed |
| --- | --- | --- |
| 2 | Left | 90 degrees clockwise |
| 3 | Left | Left-right reflection |
| 4 | Left | 180 degrees |
| 5 | Right | Identity |
| 6 | Right | 90 degrees clockwise |
| 8 | Right | 180 degrees |

For example, training example 0 has instructions 8, 5, 2, 3 and its quadrants
are right-half-turn, right-identity, left-clockwise, left-reflected. Training
example 1 has 3, 5, 3, 4 and the repeated code 3 reproduces the same reflected
left tile twice. Training example 2 has 2, 4, 6, 2, matching the observed two
left-clockwise copies and one right-clockwise copy.

## Revision 1

Hypothesis: codes 1 through 4 form a left-source bank and codes 5 through 8
form a right-source bank. Each bank has the same operation order: identity,
clockwise quarter turn, left-right reflection, half turn. The four instructions
are read in their input order and placed into output quadrants in row-major
order. Multicolor tiles retain their pixel colors.

The mapping for code 1 (left identity) and code 7 (right reflection) is an
extrapolation from the parallel four-code banks: neither code appears as a
header in visible training examples, though both occur in visible queries.
This is a genuine generalization uncertainty, not a claim of verified query
correctness. The fixed input framing is also inferred from the visible set.

I implemented this hypothesis in `solution.py`. The official visible-only
check will determine whether this implementation reproduces all visible
training outputs and executes on the visible queries.

### Check result and stopping reason

The revision-1 official check exited 0 and reported `execution_status:
completed`, `visible_passed: 3`, `visible_total: 3`, and `reported_label:
unknown`. Thus all three visible training outputs match exactly. No failed
official attempts occurred, and I have not changed the implementation after
this check. The rejected sorting idea above was only a preimplementation
hypothesis, so it did not produce a frozen code revision.

I stop after the first successful visible check because the same compact
instruction-bank rule explains every visible training pair. The query
correctness remains withheld, and codes 1 and 7 depend on the explicitly
recorded bank-symmetry extrapolation. I did not seek private output feedback.
