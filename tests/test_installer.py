import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


@unittest.skipUnless(sys.platform.startswith("linux"), "Bash dependency test requires Linux")
class InstallerTests(unittest.TestCase):
    def test_dependency_failure_is_short_and_keeps_nonzero_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "dirname").symlink_to(shutil.which("dirname"))
            package_manager = folder / "pkg"
            package_manager.write_text("#!/bin/sh\necho 'SSH key generation details'\necho 'package trace' >&2\nexit 17\n")
            package_manager.chmod(0o755)
            environment = dict(os.environ, PATH=directory)
            script = Path(__file__).resolve().parents[1] / "installer.sh"
            result = subprocess.run(["/bin/bash", str(script)], env=environment,
                                    capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout, "")
            self.assertIn("Préparation impossible", result.stderr)
            self.assertNotIn("package trace", result.stderr)
            self.assertNotIn("SSH", result.stderr)
