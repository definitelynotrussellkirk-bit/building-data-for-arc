# Parametric halo coverage family

`coverage_mode=union` returns the exact canonical program. The alternative
computes the same per-background-cell orthogonal seed coverage counts, keeps
count-one cells cyan (8), and marks count-two-or-more cells blue (1).

The hidden setting is fixed for the episode and never influences input
sampling. The declared minimum is three demonstrations. Every minimum lesson
contains coverage-2, coverage-3, and coverage-4 cases plus ordinary count-one
halo cells. Its coverage-2 demonstration deliberately includes both a
same-color opposite pair and a different-color perpendicular pair. Those
crossed witnesses prevent shortcuts based on axis mixing, collinearity, or
neighbor-color inequality. Four private queries include transfer, boundary,
dense, and substantive 30x30 scenes; the shared exporter reveals them one at a
time from a private permutation.

Sequential dependency:

- **A:** count orthogonally adjacent seeds for every original background cell.
- **Intermediate:** the integer coverage map, including values 0, 1, 2, 3, 4.
- **B:** preserve source seeds and render each background cell from that count
  according to the episode setting.

`binary_coverage_counterfactual.rkt` clips A's integer counts to a boolean
covered/not-covered map before B. On an overlap case it therefore produces the
canonical union rather than the alternative's blue multiple-coverage cells.
The protected causal witness executes both programs on the same source-bound
input.

`adversarial_audit.py` is a reusable bounded audit for future agents. It checks
matched inputs, minimum-lesson rivals, count boundaries, 30x30 content,
public-turn privacy, malformed payload rejection, and crossed controls. The
retained finding records the first lesson hole and the focused repair. These
finite checks establish reviewer readiness only, not owner acceptance,
universal uniqueness, learning benefit, or training admission.
