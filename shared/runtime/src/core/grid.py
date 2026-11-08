"""Grid representation for ARC-AGI-2."""

import numpy as np


class Grid:
    """A 2D grid of integer values (0-9)."""

    def __init__(self, data):
        if isinstance(data, np.ndarray):
            self.array = data.astype(int)
        else:
            self.array = np.array(data, dtype=int)

    @property
    def height(self) -> int:
        return self.array.shape[0]

    @property
    def width(self) -> int:
        return self.array.shape[1]

    @property
    def shape(self) -> tuple:
        return self.array.shape

    @property
    def colors(self) -> set:
        return set(self.array.flatten().tolist())

    def to_list(self) -> list:
        return self.array.tolist()

    def __eq__(self, other):
        if not isinstance(other, Grid):
            return False
        return np.array_equal(self.array, other.array)

    def __repr__(self):
        return f"Grid({self.height}x{self.width})"
