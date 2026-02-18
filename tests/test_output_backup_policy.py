import tempfile
import unittest
from pathlib import Path

from templates.modern_resume_template import archive_root_pdfs


def write_dummy_pdf(path: Path) -> None:
    path.write_bytes(b"%PDF-1.4\n%resume-tailor-test\n")


class OutputBackupPolicyTest(unittest.TestCase):
    def test_archive_root_pdfs_moves_all_root_pdfs_except_excluded(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            old_backend = output_dir / "02_10_Alice_Backend_Engineer_resume.pdf"
            old_ml = output_dir / "02_11_Alice_ML_Engineer_resume.pdf"
            temp_new = output_dir / ".02_12_Alice_Data_Engineer_resume.tmp.pdf"

            write_dummy_pdf(old_backend)
            write_dummy_pdf(old_ml)
            write_dummy_pdf(temp_new)

            archived = archive_root_pdfs(output_dir, exclude_names={temp_new.name})

            self.assertEqual(len(archived), 2)
            self.assertFalse(old_backend.exists())
            self.assertFalse(old_ml.exists())
            self.assertTrue(temp_new.exists())

            backend_backup = (
                output_dir
                / "backup"
                / "Backend_Engineer"
                / f"{old_backend.stem}_old_1.pdf"
            )
            ml_backup = (
                output_dir / "backup" / "ML_Engineer" / f"{old_ml.stem}_old_1.pdf"
            )

            self.assertTrue(backend_backup.exists())
            self.assertTrue(ml_backup.exists())
            root_pdfs = sorted(item.name for item in output_dir.glob("*.pdf"))
            self.assertEqual(root_pdfs, [temp_new.name])

    def test_archive_root_pdfs_increments_backup_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            current_pdf = output_dir / "02_10_Alice_Backend_Engineer_resume.pdf"
            write_dummy_pdf(current_pdf)

            backup_dir = output_dir / "backup" / "Backend_Engineer"
            backup_dir.mkdir(parents=True, exist_ok=True)
            existing_backup = (
                backup_dir / "02_10_Alice_Backend_Engineer_resume_old_1.pdf"
            )
            write_dummy_pdf(existing_backup)

            archive_root_pdfs(output_dir)

            next_backup = backup_dir / "02_10_Alice_Backend_Engineer_resume_old_2.pdf"
            self.assertFalse(current_pdf.exists())
            self.assertTrue(existing_backup.exists())
            self.assertTrue(next_backup.exists())


if __name__ == "__main__":
    unittest.main()
