# generic_waypoint_route_gen1

Generate panel sequences whose oriented cursor consumes an aligned route.

Inspired by supplied evaluation task 5545f144.  Each input contains two or
three equal panels separated by a full-height color column.  A three-cell arrow
advances through a nested, shrinking set of singleton waypoints.  Consecutive
waypoints share exactly one row or column, while every nonconsecutive pair has
different row and column coordinates.  The output is the next clean state:
the arrow at the final waypoint, oriented along the final leg.

Kind: `generic`. Imported version: `1.0.0`.
Approval is derived by the catalog from current code and retained evidence.
