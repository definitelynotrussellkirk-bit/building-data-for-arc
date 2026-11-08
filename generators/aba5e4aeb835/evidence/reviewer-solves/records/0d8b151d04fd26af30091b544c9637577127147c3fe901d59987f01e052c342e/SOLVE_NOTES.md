# Blind solve notes — aba5e4aeb835

## Revision 1 hypothesis

The nonzero cells encode a turtle-like orthogonal path.

- Color 2 is the unique start.
- The first segment goes in the unique row/column direction that reaches a color-3 or color-4 waypoint.
- At the first waypoint the path turns left.
- At later waypoints, keep the same turning handedness when the new waypoint color differs from the preceding waypoint; flip left/right when two consecutive waypoints have the same color.
- Color 5 is not a turning waypoint. A segment may pass through it unchanged; when that happens, the path terminates on the next color-3/4 waypoint rather than turning again.
- If a chosen direction has no further color-3/4 waypoint, fill zeros with color 8 through the border and stop.
- Existing colored cells remain unchanged; only traversed zeros become 8.

Evidence from the four demonstrations:

1. 2→4→3 has left turns at both differently colored waypoints and then exits the grid.
2. 2→3→4→3→3 keeps left turns across color changes. The last straight segment crosses a 5, so it stops at the final 3.
3. Waypoint colors are 4,3,3,4,4. Starting left, equal consecutive colors flip the handedness, giving L,L,R,R,L, exactly selecting the shown branch and border exit.
4. Four consecutive 3 waypoints flip every time, giving L,R,L,R and the shown zig-zag to the border.

The two tests appear deliberately parallel to these cases. Test 2 has the same 3,4,3,3 color pattern as demonstration 2 and a 5 on its final segment, so it should stop at the last 3.

Uncertainty: the start-direction tie-break is not exposed because every visible instance has one aligned color-3/4 candidate from the red start. I use nearest candidate only as a defensive fallback.
