# Solve notes

The input is divided into three hollow maroon (9) rectangular frames, read left to right. Each frame has one colored key cell in the row immediately above it and contains blue (1) and red (2) shapes.

For each frame, I computed the bounding boxes of all blue cells and all red cells inside that frame. The output piece is a solid rectangle in the frame's key color, with height and width equal to the intersection of those two bounding boxes. The three pieces are packed left to right with one zero column between adjacent pieces.

The examples with output height three distinguish vertical placement: shorter pieces are centered using floor division, not top- or bottom-aligned. In training example 0, the first two pieces sit in the middle row while the last height-3 piece fills all rows; training examples 1 and 2 show the same centering rule with different widths and key repetitions.

The implementation detects actual 9-components rather than assuming fixed frame widths or input dimensions, so it also covers the two 12-row test inputs.
