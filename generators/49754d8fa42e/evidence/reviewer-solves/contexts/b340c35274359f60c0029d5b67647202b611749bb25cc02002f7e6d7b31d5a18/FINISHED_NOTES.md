# Exposed solve notes

Earlier exposure is **yes** because I inspected the assigned generator before
this required post-repair solve. During this solve I used only the visible
examples in `solve/README.md`; I did not reopen the generator, Racket rule,
reference solutions, private labels, or earlier solution explanations.

## Hypothesis

Ignore zeros and count every remaining color. The uniquely most frequent
nonzero color selects one of three fixed five-cell glyphs:

- mode color 1 -> plus;
- mode color 2 -> downward-stem T;
- mode color 3 -> right-facing L.

Visible support:

- example 0 has counts 1:8, 2:14, 3:11 and returns the T;
- example 1 has 1:1, 2:10, 3:11 and returns the L;
- examples 2 and 3 isolate colors 1 and 3 and return plus and L;
- example 4 has 1:11, 2:10, 3:1 and returns plus, refuting first-cell,
  endpoint-only, and largest-visible-object shortcuts.

The two masked queries therefore select color 2 (16 cells) and color 1 (8
cells), respectively. The implementation includes an all-zero fallback only to
remain total; the visible lesson does not claim such an input is in scope.
