import json
import tempfile
import unittest
from pathlib import Path

import app as foto_studio


class FotoStudioApiTests(unittest.TestCase):
    def setUp(self):
        self.client = foto_studio.app.test_client()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_static_entrypoints_load(self):
        index = self.client.get("/")
        favicon = self.client.get("/favicon.ico")
        roots = self.client.get("/api/fs/roots")
        self.assertEqual(index.status_code, 200)
        self.assertEqual(favicon.status_code, 200)
        self.assertEqual(roots.status_code, 200)
        index.close()
        favicon.close()
        roots.close()

    def test_backup_create_list_and_restore(self):
        backup_dir = self.root / "backup"
        payload = {"sessions": [{"name": "Test"}], "contacts": []}

        created = self.client.post(
            "/api/backup/create",
            json={"backupPath": str(backup_dir), "data": payload},
        )
        self.assertEqual(created.status_code, 200)
        created_data = created.get_json()
        self.assertTrue((backup_dir / created_data["file"]).exists())

        listed = self.client.get("/api/backup/list", query_string={"path": str(backup_dir)})
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(len(listed.get_json()["files"]), 1)

        restored = self.client.post(
            "/api/backup/restore",
            json={"backupPath": str(backup_dir), "filename": created_data["file"]},
        )
        self.assertEqual(restored.status_code, 200)
        self.assertEqual(restored.get_json()["data"], payload)

    def test_fs_browse_and_mkdir(self):
        created = self.client.post("/api/fs/mkdir", json={"dirPath": str(self.root), "name": "Nowy"})
        self.assertEqual(created.status_code, 200)
        self.assertTrue((self.root / "Nowy").is_dir())

        browsed = self.client.get("/api/fs/browse", query_string={"path": str(self.root)})
        self.assertEqual(browsed.status_code, 200)
        names = {entry["name"] for entry in browsed.get_json()["dirs"]}
        self.assertIn("Nowy", names)

    def test_gallery_scan_create_serve_and_copy(self):
        source = self.root / "source"
        output = self.root / "output"
        copied = self.root / "copied"
        source.mkdir()
        (source / "a.jpg").write_bytes(b"fake-jpeg")
        (source / "notes.txt").write_text("skip", encoding="utf-8")

        scanned = self.client.get("/api/gallery/scan", query_string={"path": str(source)})
        self.assertEqual(scanned.status_code, 200)
        self.assertEqual(scanned.get_json()["images"], ["a.jpg"])

        created = self.client.post(
            "/api/gallery/create",
            json={"sourceDir": str(source), "outputDir": str(output), "name": "Galeria", "sessionName": "Sesja"},
        )
        self.assertEqual(created.status_code, 200)
        gallery_file = Path(created.get_json()["galleryFile"])
        self.assertTrue(gallery_file.exists())

        served = self.client.get("/api/gallery/serve", query_string={"path": str(gallery_file)})
        self.assertEqual(served.status_code, 200)
        self.assertIn("Galeria", served.get_data(as_text=True))

        copy_res = self.client.post(
            "/api/gallery/copy-files",
            json={"photosDir": str(output / "photos"), "files": ["a.jpg"], "destDir": str(copied)},
        )
        self.assertEqual(copy_res.status_code, 200)
        self.assertTrue((copied / "a.jpg").exists())

    def test_gallery_static_blocks_directory_traversal(self):
        base = self.root / "gallery"
        outside = self.root / "outside.txt"
        base.mkdir()
        outside.write_text("secret", encoding="utf-8")

        response = self.client.get(
            "/api/gallery/static",
            query_string={"base": str(base), "file": "../outside.txt"},
        )
        self.assertEqual(response.status_code, 403)

    def test_restore_path_rejects_non_json(self):
        not_json = self.root / "state.txt"
        not_json.write_text(json.dumps({"ok": True}), encoding="utf-8")
        response = self.client.post("/api/backup/restore-path", json={"filePath": str(not_json)})
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
