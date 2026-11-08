# f898eb5adb5d

0-bg grid (size varies). One color-2 START and one color-3 GOAL, 0-N color-5 WALL cells (sparse, non-blocking), and 0-3 WAYPOINT cells in distinct colors from {4,6,7,9}. Rule: BFS over all non-5 cells; the path must go START -> the waypoints in ASCENDING color order -> GOAL. Paint the intermediate route cells that are 0 with color 8 (start, goal, walls and waypoints are preserved). Net: a shortest route threading the waypoints in order, drawn in color 8. (Was mis-modelled as 8-walls + 4-portals.)

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
