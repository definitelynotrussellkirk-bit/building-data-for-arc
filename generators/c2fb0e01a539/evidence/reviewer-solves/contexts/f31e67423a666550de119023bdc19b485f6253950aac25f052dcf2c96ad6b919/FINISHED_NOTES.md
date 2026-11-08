# Solve work log

## Prior exposure declaration

Before this exposed solve I had already inspected the selected task's canonical rule and generator while reviewing and repairing the packet. I therefore declare earlier rule exposure **yes**. During this solve episode I did not reopen the rule, generator, reference solutions, private query labels, or the earlier blind-solve explanation; I used only `solve/challenge.json`, this work log, and the prescribed check command.

## Revision 1

### Visible evidence

Across all four training pairs, only zero-valued cells change, and every changed cell becomes 7. The changed cells form zero regions completely surrounded by nonzero cells. Large exterior zero fields and zero corridors that reach an outer grid edge remain zero. Several examples show that an enclosed region may be nonrectangular, may contain more than one cell, and may be bounded cooperatively by more than one nonzero color. A diagonal contact is not enough to connect a zero pocket to the exterior in the visible examples, so the natural adjacency is orthogonal (4-neighbor).

### Hypothesis

Copy the grid, enumerate every 4-connected component of zeros, and recolor the whole component to 7 exactly when none of its cells touches the grid border.

### Program/probe

Implemented a breadth-first flood fill over zero cells. For each unseen component, record whether any cell lies on the outer row or column. Fill the component only when that flag is false. The implementation does not mutate the supplied grid.

### Alternatives considered

- Fill every zero inside a nonzero object's bounding box. Rejected because it depends on object decomposition and would mishandle cooperative/mixed-color enclosures.
- Fill only rectangular holes or one representative cell per hole. Rejected because visible outputs include bent and multi-cell enclosed regions.
- Use 8-neighbor connectivity. Rejected because diagonal leakage would merge some visibly enclosed pockets with exterior background.
- Fill zeros with the surrounding wall color. Rejected because the output color is consistently 7 regardless of the wall palette.

### Remaining uncertainty

The visible examples strongly identify the topological rule, but private query labels are withheld. The check can validate only execution and the four visible training outputs; it cannot establish private-query correctness.
