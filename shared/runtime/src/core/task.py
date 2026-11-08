"""Task representation for ARC-AGI-2."""

from .grid import Grid


class Task:
    """Wraps a single ARC task with convenience accessors."""

    def __init__(self, task_id: str, data: dict):
        self.task_id = task_id
        self.train = [
            (Grid(p["input"]), Grid(p["output"])) for p in data["train"]
        ]
        self.test = []
        for p in data["test"]:
            inp = Grid(p["input"])
            out = Grid(p["output"]) if "output" in p else None
            self.test.append((inp, out))

    @property
    def num_train(self) -> int:
        return len(self.train)

    @property
    def num_test(self) -> int:
        return len(self.test)

    def __repr__(self):
        return f"Task({self.task_id}, train={self.num_train}, test={self.num_test})"
