"""Type atoms for the deliberately small ARC-Racket v2 core."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True, order=True)
class V2Type:
    name: str

    def __str__(self) -> str:
        return self.name


GRID = V2Type("Grid")
COLOR = V2Type("Color")
INTEGER = V2Type("Integer")
BOOLEAN = V2Type("Boolean")
POSITION = V2Type("Position")
CELL_SET = V2Type("CellSet")
OBJECT = V2Type("Object")
OBJECT_LIST = V2Type("ObjectList")
BOUNDING_BOX = V2Type("BoundingBox")
DIRECTION = V2Type("Direction")
REFLECTION = V2Type("Reflection")
ROTATION = V2Type("Rotation")
AXIS = V2Type("Axis")

ALL_TYPES = (
    GRID,
    COLOR,
    INTEGER,
    BOOLEAN,
    POSITION,
    CELL_SET,
    OBJECT,
    OBJECT_LIST,
    BOUNDING_BOX,
    DIRECTION,
    REFLECTION,
    ROTATION,
    AXIS,
)
