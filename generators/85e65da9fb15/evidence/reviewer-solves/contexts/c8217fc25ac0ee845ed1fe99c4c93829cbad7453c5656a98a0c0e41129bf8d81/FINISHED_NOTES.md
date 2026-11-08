# Visible-only solve notes

The inputs contain two hollow rectangular border components and several loose solid components. The outputs erase every loose component from its original location, preserve both frames, and place at most one loose shape inside each frame.

Hypothesis from the three training pairs:

1. Identify exact hollow rectangular borders as frames; all other same-color 4-connected components are loose shapes.
2. Process loose shapes in top-left reading order.
3. For each loose shape, among still-unused frames, retain its orientation if its bounding box fits; otherwise allow one clockwise 90-degree rotation.
4. Choose the fitting frame with the least unused interior bounding-box area, breaking ties by the frame's top-left position.
5. Center the shape in the frame interior, with floor/top-left bias for odd slack. Keep only frame borders and successfully assigned shapes; erase unmatched loose shapes.

Evidence: training example 3 forces rotation of the first 2x4-bbox shape into a 4x2 interior; example 2 separates shape order from frame order; example 1 shows unmatched wide distractors disappear. The generated solver implements this directly without consulting a reference during this solve phase.
