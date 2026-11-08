# Exposed visible-only solve work log

This is an assistant-authored work log, not a token-level captured conversation
or a log-probability trace. Earlier rule exposure: **yes**, from the completed
generator review. During this episode I read only the preparation's public grids,
my Python program, and visible-example experiment/check results. Generator code,
reference rule text, previous solution explanations and hidden answers were closed.

## Visible observations and first hypothesis

Preparation displayed three labeled demonstrations and two query inputs. All
demonstrations preserve dimensions and foreground cell locations; whole connected
components change to 2, 3, 4. Demonstration 0 has two identical filled 3x3 squares
receiving 2 and 3, and a smaller concave component receiving 4. This refutes simple
ascending occupied area. Their equal-sized bounding boxes also fail to explain
why the concave shape receives the last rank.

The candidate is increasing exposed-edge perimeter. The two squares both have
perimeter 12, and the square first encountered in row-major scanning gets the
earlier rank. This supplies a visible stable-tie cue. Demonstration 1 contains
three different boundary lengths, and demonstration 2 includes another tie-like
comparison, so a small component-metric experiment can check the rule across
all visible examples. No wrong solution is invented as an earlier attempt.

## Implementation and experiment

Revision 1 independently flood-fills nonzero cells with four-neighbor adjacency,
counts edges facing a cell outside the component, stably sorts components by
that count, and paints 2, 3, 4. Component discovery starts at the smallest remaining
(row, column), making the tie decision explicit. It imports no task or runtime
modules. Background and shape are preserved; foreground color is not a rank cue.

The recorded Python experiment prints each visible component's area, perimeter,
bounding-box size and observed output color, then compares the predicted grid
with the visible output. Only the challenge's three `train` pairs are used to
judge agreement; queries remain unscored. Check results and query execution are
retained by the ordinary solve checker.
