"""Focused CLI tests; all temporary paths belong to this test run."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
HELPER = HERE / "private_memory_workspace.py"

class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="memory-helper-test-", dir=HERE)
        self.root = Path(self.temp.name)
        self.target = self.root / "memory"
        self.output = self.root / "saved"
    def tearDown(self):
        self.temp.cleanup()
    def run_helper(self, *args):
        return subprocess.run([sys.executable, "-B", str(HELPER), *map(str,args)], capture_output=True, text=True)
    def base(self):
        return ["--work-dir",self.target,"--output-dir",self.output,"--size-mib","4"]
    def test_rejects_existing_target(self):
        self.target.mkdir()
        r=self.run_helper(*self.base(),"--",sys.executable,"-c","pass")
        self.assertEqual(r.returncode,2,r.stderr)
        self.assertIn("must not already exist",r.stderr)
    def test_rejects_symlink_parent(self):
        (self.root/"link").symlink_to(self.root, target_is_directory=True)
        r=self.run_helper("--work-dir",self.root/"link"/"memory","--output-dir",self.output,"--","true")
        self.assertEqual(r.returncode,2,r.stderr)
        self.assertIn("symlink",r.stderr)
    def test_rejects_invalid_size_and_missing_command(self):
        r=self.run_helper(*self.base(),"--size-mib","0","--","true")
        self.assertEqual(r.returncode,2,r.stderr)
        r=self.run_helper(*self.base())
        self.assertEqual(r.returncode,2,r.stderr)
        self.assertIn("command",r.stderr)
    def test_success_preserves_literal_argv_and_exports(self):
        before=os.readlink("/proc/self/ns/mnt")
        literal="literal $(touch SHOULD_NOT_EXIST); *"
        code="from pathlib import Path; import sys; Path('return/result.txt').write_text(sys.argv[1])"
        r=self.run_helper(*self.base(),"--",sys.executable,"-c",code,literal)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual((self.output/"result.txt").read_text(),literal)
        self.assertEqual(os.readlink("/proc/self/ns/mnt"),before)
        self.assertEqual(list(self.target.iterdir()),[])
        self.assertFalse((self.target/"SHOULD_NOT_EXIST").exists())
    def test_failure_propagates_and_still_exports(self):
        code="from pathlib import Path; Path('return/failure.txt').write_text('retained'); raise SystemExit(23)"
        r=self.run_helper(*self.base(),"--",sys.executable,"-c",code)
        self.assertEqual(r.returncode,23,r.stderr)
        self.assertEqual((self.output/"failure.txt").read_text(),"retained")
    def test_rejects_output_inside_transient_tree(self):
        r=self.run_helper("--work-dir",self.target,"--output-dir",self.target/"saved","--","true")
        self.assertEqual(r.returncode,2,r.stderr)
        self.assertIn("outside",r.stderr)
    def test_refuses_symlink_exports(self):
        code="from pathlib import Path; Path('return/link').symlink_to('/etc/passwd')"
        r=self.run_helper(*self.base(),"--",sys.executable,"-c",code)
        self.assertNotEqual(r.returncode,0)
        self.assertIn("symlink",r.stderr)
        self.assertFalse((self.output/"link").exists())

if __name__ == "__main__":
    unittest.main(verbosity=2)
