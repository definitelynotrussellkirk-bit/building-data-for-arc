"""Include the standalone library in wheels without duplicating authored sources."""
from pathlib import Path
import shutil

from setuptools import setup
from setuptools.command.build_py import build_py


class BuildLibrary(build_py):
    def run(self):
        super().run()
        root = Path(__file__).resolve().parent
        destination = Path(self.build_lib) / "arcpuzzles/library"
        if destination.exists():
            shutil.rmtree(destination)  # Generated build output only; avoid retaining deleted library files.
        for name in ("catalog", "generators", "shared", "GUIDE", "docs"):
            source = root / name
            shutil.copytree(source, destination / name, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", ".venv", ".env"))
        for name in ("README.md", "AGENTS.md", "REVIEW/README.md", "REVIEW/incoming/README.md", "shared/README.md"):
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(root / name, target)

    def get_outputs(self, include_bytecode=1):
        outputs = super().get_outputs(include_bytecode)
        library = Path(self.build_lib) / "arcpuzzles/library"
        return outputs + [str(p) for p in library.rglob("*") if p.is_file()]


setup(cmdclass={"build_py": BuildLibrary})
