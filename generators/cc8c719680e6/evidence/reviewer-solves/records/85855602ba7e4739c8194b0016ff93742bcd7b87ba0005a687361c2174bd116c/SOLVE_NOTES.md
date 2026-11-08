# Visible-only solve notes

This is a model-authored summary of hypotheses, probes, and uncertainty, not a token-level trace.

## Exposure boundary

The root agent had earlier rule exposure during repair. This isolated solving agent read only `solve/challenge.json` before deriving the rule. It did not inspect the generator, rules, prior explanations, canonical records, tests, reference programs, or hidden/private labels and did not consult another agent for a rule. Subsequent access is limited to its own solve files and the supplied checker's public feedback. The finish flag records the root's earlier exposure, not exposure by this solver.

## Hypothesis and evidence

Treat zero as background. Split nonzero cells into monochromatic components using four-neighbor connectivity. Replace each component with the outline of its tight, axis-aligned bounding rectangle, preserving its color and clearing its interior.

- Training example 1 completes a 3 by 3 outline and a 3 by 2 rectangle.
- Training example 2 removes an existing interior 7 while completing its 3 by 3 border. Objects of different colors remain separate even where they touch.
- Training example 3 turns the 5-colored plus into a hollow 3 by 3 border, confirming that interior cells must be cleared rather than preserved.
- Training example 4 contains two diagonally adjacent components of color 2. Their separate 3 by 3 and 2 by 2 output rectangles distinguish four-neighbor connectivity from eight-neighbor connectivity or grouping by color alone.

## Actual probes and attempt history

1. Read the visible challenge and enumerated the colors, sizes, and tight bounding boxes of four-neighbor components in all four training inputs and both test inputs. The observed groups support the same component-based rule throughout.
2. Wrote the first solver directly from this hypothesis. No earlier solver revision or failed submission occurred.
3. Checker result: pending.

## Uncertainty

The visible examples do not establish a precedence rule for intersecting outlines from overlapping component bounding boxes. No visible training or test input has that ambiguity. The implementation renders component borders onto an initially zero grid in row-major discovery order.
