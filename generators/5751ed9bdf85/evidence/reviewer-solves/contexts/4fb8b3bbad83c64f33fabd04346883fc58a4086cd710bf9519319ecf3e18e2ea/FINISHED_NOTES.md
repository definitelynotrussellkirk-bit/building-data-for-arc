# Solve notes

This is a human work log based only on `solve/challenge.json` during the post-repair solve phase.

## Visible-example hypothesis

The gray cells form several separate hollow rectangular frames. In each training pair:

- one frame is empty;
- one frame has multiple colored cells and remains unchanged; and
- exactly one frame contains a single colored marker.

Only the zeros inside the one-marker frame are recolored, using that marker's color. Gray borders and all other frames remain unchanged. The examples also rule out selecting by marker color, frame position, or frame size: the selected frame moves and its color can also occur in a multi-marker frame.

## Implementation probe

Detect four-connected gray components, use each component's bounding box as a frame, count nonzero/non-gray cells strictly inside it, and fill zeros only for the component with exactly one such marker. Return immediately after the unique target is filled.

No Racket rule, generator source, reference solution, or private labels were consulted during this solve attempt. I had earlier exposure to the task rule while reviewing the assigned generator, so this is an exposed reconstruction rather than a blind solve.
