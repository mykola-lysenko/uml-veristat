#!/usr/bin/env python3
"""Exercise installer failure boundaries without network access."""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest


INSTALLER = Path(__file__).resolve().with_name("install_llvm.sh")
RELEASE = "llvmorg-23.1.0"
ARCHIVE = "LLVM-23.1.0-Linux-X64.tar.xz"


class InstallerFailures(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.install = self.root / "installed"
        self.install.mkdir()
        (self.install / "reference").write_text("preserve me")
        self.work = self.root / "downloads"
        self.work.mkdir()
        shim = self.root / "bin"
        shim.mkdir()
        curl = shim / "curl"
        curl.write_text("""#!/usr/bin/env python3
import os, pathlib, sys
root = pathlib.Path(os.environ['FIXTURE_ROOT'])
with (root/'requests').open('a') as f:
    f.write(next(a for a in sys.argv if a.startswith('https://')) + '\\n')
if os.environ.get('FAIL_API'):
    sys.exit(22)
pathlib.Path(sys.argv[sys.argv.index('-o') + 1]).write_bytes((root/'release.json').read_bytes())
""")
        curl.chmod(0o755)
        self.env = dict(os.environ, PATH=str(shim) + os.pathsep + os.environ["PATH"],
                        FIXTURE_ROOT=str(self.root), REBUILD_LLVM="1", REUSE_LLVM="0")
        for key in ("GITHUB_TOKEN", "GH_TOKEN"):
            self.env.pop(key, None)

    def metadata(self, tag=RELEASE, digest=None):
        (self.root / "release.json").write_text(json.dumps({
            "tag_name": tag,
            "assets": [{"name": ARCHIVE,
                        "browser_download_url": "https://example.invalid/" + ARCHIVE,
                        "digest": "sha256:" + (digest or "0" * 64)}],
        }))

    def reject(self, message):
        result = subprocess.run(["bash", str(INSTALLER), RELEASE, str(self.work),
                                 str(self.install)], env=self.env, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(message, result.stdout)
        self.assertEqual((self.install / "reference").read_text(), "preserve me")
        self.assertFalse((self.install / ".uml-llvm-release.json").exists())
        self.assertEqual((self.root / "requests").read_text().splitlines(), [
            "https://api.github.com/repos/llvm/llvm-project/releases/tags/" + RELEASE])
        self.assertFalse(list(self.root.glob("installed.new.*")))

    def test_api_failure_does_not_query_latest(self):
        self.env["FAIL_API"] = "1"
        self.reject("no alternate release will be selected")

    def test_wrong_release_response_is_rejected(self):
        self.metadata(tag="llvmorg-22.1.8")
        self.reject("does not match the requested tag")

    def test_corrupt_cached_archive_preserves_installation(self):
        self.metadata()
        (self.work / ARCHIVE).write_bytes(b"damaged archive")
        self.reject("checksum mismatch")

    def test_wrong_compiler_version_preserves_installation(self):
        archive = self.work / ARCHIVE
        with tarfile.open(archive, "w:xz") as tar:
            for tool in ("clang", "llc", "llvm-config", "llvm-strip", "llvm-objcopy"):
                data = b"#!/bin/sh\necho 22.1.8\n"
                member = tarfile.TarInfo("llvm/bin/" + tool)
                member.size, member.mode = len(data), 0o755
                tar.addfile(member, io.BytesIO(data))
        self.metadata(digest=hashlib.sha256(archive.read_bytes()).hexdigest())
        self.reject("existing installation preserved")


if __name__ == "__main__":
    unittest.main()
