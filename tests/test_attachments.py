from bot.services.attachments import delete_user_uploads


def test_delete_user_uploads(tmp_path, monkeypatch):
    uploads_root = tmp_path / "uploads"
    user_id = "user123"
    user_folder = uploads_root / user_id
    user_folder.mkdir(parents=True)

    sample = user_folder / "file.txt"
    sample.write_text("content")

    monkeypatch.setenv("UPLOAD_ROOT", str(uploads_root))
    monkeypatch.setattr("bot.services.attachments.UPLOAD_ROOT", str(uploads_root))

    delete_user_uploads(user_id)

    assert not user_folder.exists()
