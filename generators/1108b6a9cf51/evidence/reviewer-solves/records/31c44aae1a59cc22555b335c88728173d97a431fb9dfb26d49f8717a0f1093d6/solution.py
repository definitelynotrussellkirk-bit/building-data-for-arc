def _turn(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _orientations(grid):
    for mirror in (False, True):
        current = [row[::-1] if mirror else row[:] for row in grid]
        for turns in range(4):
            yield (mirror, turns), current
            current = _turn(current)


def solve(grid):
    """Infer a panel-to-panel symmetry, then apply it to the third panel."""
    width = len(grid[0])
    if (width - 2) % 3:
        raise ValueError("Expected three equally wide panels and two separators")
    side = (width - 2) // 3
    first = [row[:side] for row in grid]
    second = [row[side + 1:2 * side + 1] for row in grid]
    third = [row[2 * side + 2:] for row in grid]
    matching = {key for key, oriented in _orientations(first) if oriented == second}
    answers = [oriented for key, oriented in _orientations(third) if key in matching]
    if not answers:
        raise ValueError("No dihedral transformation fits the demonstration panels")
    if any(answer != answers[0] for answer in answers[1:]):
        raise ValueError("Demonstration panels leave the output ambiguous")
    return answers[0]
