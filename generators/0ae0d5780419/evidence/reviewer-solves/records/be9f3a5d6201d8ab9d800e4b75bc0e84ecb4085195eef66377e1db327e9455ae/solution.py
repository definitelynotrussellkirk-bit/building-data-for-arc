import numpy as np


def _crop(panel):
    rows, cols = np.nonzero(panel)
    if not len(rows):
        return np.zeros((1, 1), dtype=int)
    return panel[rows.min():rows.max() + 1, cols.min():cols.max() + 1]


def solve(grid):
    """Infer a panel analogy using exact rotations and reflections."""
    array = np.asarray(grid, dtype=int)
    separators = [c for c in range(array.shape[1])
                  if np.all(array[:, c] == 5)]
    boundaries = [-1] + separators + [array.shape[1]]
    panels = [_crop(array[:, left + 1:right])
              for left, right in zip(boundaries, boundaries[1:])
              if right > left + 1]
    if len(panels) != 3:
        raise ValueError("Expected three panels separated by gray columns")
    before, after, target = panels
    transforms = (
        lambda a: a,
        lambda a: np.rot90(a, -1),
        lambda a: np.rot90(a, 2),
        lambda a: np.rot90(a, 1),
        lambda a: a[::-1, :],
        lambda a: a[:, ::-1],
        lambda a: a.T,
        lambda a: a[::-1, ::-1].T,
    )
    for transform in transforms:
        if np.array_equal(transform(before), after):
            return transform(target).tolist()
    return target.tolist()
