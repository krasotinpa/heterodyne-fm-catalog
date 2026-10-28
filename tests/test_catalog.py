# SPDX-License-Identifier: GPL-3.0-or-later
import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import catalog  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class Fixtures(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(catalog.validate_region(FIXTURES / "valid" / "test.json"), [])

    def test_each_invalid_case_is_rejected(self):
        cases = sorted((FIXTURES / "invalid").iterdir())
        self.assertGreater(len(cases), 10)
        for case in cases:
            with self.subTest(case.name):
                self.assertTrue(catalog.validate_region(case / "test.json"))


class Repository(unittest.TestCase):
    def test_region_files_are_valid(self):
        self.assertEqual(catalog.validate_all(), [])

    def test_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            catalog.build(out, "2026-10-28")
            index = json.loads((out / "index.json").read_text(encoding="utf-8"))
            self.assertEqual(index["revision"], "2026-10-28")
            for r in index["regions"]:
                self.assertEqual(hashlib.sha256((out / r["file"]).read_bytes()).hexdigest(), r["sha256"])
            with zipfile.ZipFile(out / "catalog-2026-10-28.zip") as z:
                self.assertEqual(sorted(z.namelist()), sorted(["index.json"] + [r["file"] for r in index["regions"]]))


if __name__ == "__main__":
    unittest.main()
