# Blind solve notes — e5887c52e323

## Visible-example hypothesis

The color-2 cells form small orthogonally connected objects. Every object that is exactly a three-cell L (a 2×2 box with one missing cell) has exactly one elbow cell touching the other two. The output changes that elbow from color 2 to color 4. Other cells are preserved, including a 2×2 square, isolated/smaller color-2 objects, and unrelated colors 1 and 5.

## Implementation

1. Copy the input.
2. Find orthogonally connected components of color 2.
3. For a component of three cells spanning exactly two rows and two columns, find the unique cell with two orthogonal neighbors inside the component.
4. Recolor that elbow to 4.

This component formulation handles all four rotations and avoids changing non-L distractors.
