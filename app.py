import email
import imaplib
import json
import os
import platform
import re
import shutil
import smtplib
import ssl
import sys
import threading
import webbrowser
from datetime import datetime
from email.header import decode_header
from email.message import EmailMessage
from email.utils import parsedate_to_datetime
from pathlib import Path

import requests
from flask import Flask, jsonify, request, send_file, send_from_directory


APP_NAME = "Foto-Studio"
APP_VERSION = "2.5"
AUTHOR = "Marek Zettel"
PORT = int(os.environ.get("PORT", "3000"))
ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
IMAGE_EXT = re.compile(r"\.(jpg|jpeg|png|gif|webp|tiff|tif|bmp|heic|heif|avif)$", re.I)

app = Flask(__name__, static_folder=str(ROOT), static_url_path="")


def json_body():
    return request.get_json(silent=True) or {}


def safe_error(message, status=500):
    return jsonify({"error": str(message)}), status


def decode_mime(value):
    if not value:
        return ""
    parts = []
    for part, enc in decode_header(value):
        if isinstance(part, bytes):
            parts.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            parts.append(part)
    return "".join(parts)


def email_text(msg):
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))
            if content_type == "text/plain" and "attachment" not in disposition:
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                    return re.sub(r"<[^>]+>", " ", text)
        return ""
    payload = msg.get_payload(decode=True)
    if not payload:
        return str(msg.get_payload() or "")
    return payload.decode(msg.get_content_charset() or "utf-8", errors="replace")


def gmail_login():
    data = json_body()
    address = data.get("emailAddress")
    password = data.get("appPassword")
    if not address or not password:
        raise ValueError("Brak adresu Gmail lub hasła aplikacji.")
    imap = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    imap.login(address, password)
    return imap, address, password


def message_summary(imap, uid):
    status, fetched = imap.uid("fetch", uid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)] FLAGS)")
    if status != "OK" or not fetched or not fetched[0]:
        return None
    raw = fetched[0][1]
    msg = email.message_from_bytes(raw)
    flags = fetched[0][0].decode(errors="ignore")
    date = ""
    try:
        date = parsedate_to_datetime(msg.get("Date")).isoformat()
    except Exception:
        pass
    return {
        "uid": int(uid),
        "from": decode_mime(msg.get("From")),
        "subject": decode_mime(msg.get("Subject")) or "(brak tematu)",
        "date": date,
        "seen": "\\Seen" in flags,
    }


@app.get("/")
def index():
    return send_from_directory(ROOT, "index.html")


@app.get("/favicon.ico")
def favicon():
    return send_from_directory(ROOT / "icons", "icon-192.ico")


@app.post("/api/chat")
def chat():
    data = json_body()
    api_key = data.get("apiKey") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return safe_error("Brak klucza API.", 400)

    payload = {
        "model": data.get("model") or "claude-3-5-sonnet-20241022",
        "max_tokens": 1200,
        "system": data.get("system") or "",
        "messages": data.get("messages") or [],
    }
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "content-type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            json=payload,
            timeout=60,
        )
        result = r.json()
        if not r.ok:
            err = result.get("error", {})
            msg = err.get("message") or result.get("error") or "Błąd API Anthropic."
            return jsonify({"error": msg, "errorType": err.get("type")}), r.status_code
        return jsonify(result)
    except requests.RequestException as exc:
        return safe_error(f"Błąd połączenia z API: {exc}", 502)


@app.post("/api/ai/ideas")
def ai_ideas():
    data = json_body()
    key = data.get("apiKey") or os.environ.get("GEMINI_KEY")
    if not key:
        return safe_error("Brak klucza API.", 400)
    prompt = (
        "Jesteś dyrektorem kreatywnym. Zaproponuj 3 koncepcje sesji dla: "
        f"{data.get('clientContext', '')}. Typ: {data.get('sessionType', '')}. Styl: Photon Noir."
    )
    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=45,
        )
        result = r.json()
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        return jsonify({"ideas": text})
    except Exception as exc:
        return safe_error(f"Błąd AI: {exc}", 500)


@app.post("/api/backup/create")
def backup_create():
    data = json_body()
    backup_path = data.get("backupPath")
    state = data.get("data")
    if not backup_path:
        return safe_error("Brak ścieżki kopii zapasowej.", 400)
    if state is None:
        return safe_error("Brak danych do zapisania.", 400)
    try:
        folder = Path(backup_path).expanduser()
        folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().isoformat(timespec="seconds").replace(":", "-")
        filename = f"foto-studio-backup-{stamp}.json"
        destination = folder / filename
        destination.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

        backups = sorted(folder.glob("foto-studio-backup-*.json"))
        legacy = sorted(folder.glob("focusmaster-backup-*.json"))
        for old in (backups + legacy)[:-30]:
            try:
                old.unlink()
            except OSError:
                pass
        return jsonify({"success": True, "file": filename, "path": str(destination)})
    except Exception as exc:
        return safe_error(f"Błąd zapisu: {exc}", 500)


@app.get("/api/backup/list")
def backup_list():
    backup_path = request.args.get("path")
    if not backup_path:
        return jsonify({"files": []})
    try:
        folder = Path(backup_path).expanduser()
        files = sorted(
            list(folder.glob("foto-studio-backup-*.json")) + list(folder.glob("focusmaster-backup-*.json")),
            key=lambda p: p.name,
            reverse=True,
        )[:10]
        return jsonify(
            {
                "files": [
                    {
                        "name": f.name,
                        "size": f.stat().st_size,
                        "mtime": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                    }
                    for f in files
                ]
            }
        )
    except Exception as exc:
        return jsonify({"files": [], "error": str(exc)})


@app.post("/api/backup/restore")
def backup_restore():
    data = json_body()
    backup_path, filename = data.get("backupPath"), data.get("filename")
    if not backup_path or not filename:
        return safe_error("Brak parametrów.", 400)
    try:
        folder = Path(backup_path).resolve()
        file_path = (folder / filename).resolve()
        if folder not in file_path.parents and file_path != folder:
            return safe_error("Nieprawidłowa ścieżka pliku.", 403)
        return jsonify({"success": True, "data": json.loads(file_path.read_text(encoding="utf-8"))})
    except Exception as exc:
        return safe_error(f"Błąd odczytu: {exc}", 500)


@app.post("/api/backup/restore-path")
def backup_restore_path():
    file_path = json_body().get("filePath")
    if not file_path:
        return safe_error("Brak ścieżki pliku.", 400)
    if not str(file_path).lower().endswith(".json"):
        return safe_error("Tylko pliki .json są obsługiwane.", 400)
    try:
        path = Path(file_path).expanduser()
        data = json.loads(path.read_text(encoding="utf-8"))
        stat = path.stat()
        return jsonify(
            {
                "success": True,
                "data": data,
                "meta": {"size": stat.st_size, "mtime": datetime.fromtimestamp(stat.st_mtime).isoformat(), "name": path.name},
            }
        )
    except Exception as exc:
        return safe_error(f"Błąd odczytu: {exc}", 500)


@app.get("/api/fs/roots")
def fs_roots():
    roots = []
    home = Path.home()
    roots.append({"label": "Katalog domowy", "path": str(home)})
    for name in ("Desktop", "Pulpit", "Documents", "Dokumenty", "Pictures", "Obrazy"):
        p = home / name
        if p.exists():
            roots.append({"label": name, "path": str(p)})
    if platform.system() == "Windows":
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            drive = Path(f"{letter}:\\")
            if drive.exists():
                roots.append({"label": f"Dysk {letter}:", "path": str(drive)})
    else:
        for base in (Path("/Volumes"), Path("/media") / os.environ.get("USER", ""), Path("/mnt")):
            if base.exists():
                for child in base.iterdir():
                    if child.is_dir():
                        roots.append({"label": child.name, "path": str(child)})
        roots.append({"label": "Katalog główny (/)", "path": "/"})
    deduped = []
    seen = set()
    for root in roots:
        if root["path"] not in seen:
            deduped.append(root)
            seen.add(root["path"])
    return jsonify({"roots": deduped})


@app.get("/api/fs/browse")
def fs_browse():
    dir_path = Path(request.args.get("path") or str(Path.home())).expanduser()
    show_files = request.args.get("files") == "1"
    try:
        entries = list(dir_path.iterdir())
        dirs = sorted(
            [{"name": e.name, "path": str(e)} for e in entries if e.is_dir() and not e.name.startswith(".")],
            key=lambda item: item["name"].lower(),
        )
        files = []
        if show_files:
            files = sorted(
                [
                    {
                        "name": e.name,
                        "path": str(e),
                        "size": e.stat().st_size,
                        "mtime": datetime.fromtimestamp(e.stat().st_mtime).isoformat(),
                    }
                    for e in entries
                    if e.is_file() and e.name.lower().endswith(".json")
                ],
                key=lambda item: item["mtime"],
                reverse=True,
            )
        parent = str(dir_path.parent) if dir_path.parent != dir_path else None
        return jsonify({"current": str(dir_path), "parent": parent, "dirs": dirs, "files": files})
    except Exception as exc:
        return safe_error(f"Brak dostępu: {exc}", 400)


@app.post("/api/fs/mkdir")
def fs_mkdir():
    data = json_body()
    dir_path, name = data.get("dirPath"), data.get("name")
    if not dir_path or not name:
        return safe_error("Brak parametrów.", 400)
    if re.search(r'[/\\:*?"<>|]', name):
        return safe_error("Nieprawidłowa nazwa folderu.", 400)
    try:
        new_dir = Path(dir_path) / name
        new_dir.mkdir(parents=True, exist_ok=True)
        return jsonify({"success": True, "path": str(new_dir)})
    except Exception as exc:
        return safe_error(f"Błąd tworzenia: {exc}", 500)


@app.get("/api/gallery/serve")
def gallery_serve():
    file_path = request.args.get("path")
    if not file_path or not file_path.lower().endswith(".html"):
        return "Nieprawidłowy plik.", 400
    path = Path(file_path)
    if not path.exists():
        return "Nie znaleziono galerii.", 404
    html = path.read_text(encoding="utf-8", errors="replace")
    base = str(path.parent)
    html = html.replace('src="photos/', f'src="/api/gallery/static?base={requests.utils.quote(base)}&file=photos%2F')
    html = html.replace("src='photos/", f"src='/api/gallery/static?base={requests.utils.quote(base)}&file=photos%2F")
    return html, 200, {"Content-Type": "text/html; charset=utf-8"}


@app.get("/api/gallery/static")
def gallery_static():
    base = request.args.get("base")
    file_name = request.args.get("file")
    if not base or not file_name:
        return "Brak parametrów.", 400
    base_path = Path(base).resolve()
    full_path = (base_path / file_name).resolve()
    if base_path not in full_path.parents and full_path != base_path:
        return "Forbidden.", 403
    if not full_path.exists():
        return "Nie znaleziono.", 404
    return send_file(full_path)


@app.get("/api/gallery/thumb")
def gallery_thumb():
    file_path = request.args.get("path")
    if not file_path:
        return "Brak ścieżki.", 400
    if not IMAGE_EXT.search(file_path):
        return "Nie jest zdjęciem.", 400
    path = Path(file_path)
    if not path.exists():
        return "Nie znaleziono.", 404
    return send_file(path.resolve())


@app.get("/api/gallery/scan")
def gallery_scan():
    dir_path = request.args.get("path")
    if not dir_path:
        return safe_error("Brak ścieżki.", 400)
    try:
        images = sorted([p.name for p in Path(dir_path).iterdir() if p.is_file() and IMAGE_EXT.search(p.name)])
        return jsonify({"images": images, "count": len(images)})
    except Exception as exc:
        return safe_error(f"Błąd odczytu: {exc}", 400)


@app.post("/api/gallery/create")
def gallery_create():
    data = json_body()
    source_dir, output_dir, name = data.get("sourceDir"), data.get("outputDir"), data.get("name")
    if not source_dir or not output_dir or not name:
        return safe_error("Brak parametrów.", 400)
    try:
        source = Path(source_dir)
        output = Path(output_dir)
        photos_out = output / "photos"
        photos_out.mkdir(parents=True, exist_ok=True)
        images = sorted([p.name for p in source.iterdir() if p.is_file() and IMAGE_EXT.search(p.name)])
        if not images:
            return safe_error("Brak zdjęć w wybranym folderze.", 400)
        for image in images:
            shutil.copy2(source / image, photos_out / image)
        gallery_file = output / "gallery.html"
        gallery_file.write_text(build_gallery_html(name, data.get("sessionName") or "", images, output), encoding="utf-8")
        return jsonify({"success": True, "count": len(images), "galleryFile": str(gallery_file)})
    except Exception as exc:
        return safe_error(exc, 500)


@app.post("/api/gallery/copy-files")
def gallery_copy_files():
    data = json_body()
    photos_dir, files, dest_dir = data.get("photosDir"), data.get("files") or [], data.get("destDir")
    if not photos_dir or not files or not dest_dir:
        return safe_error("Brak parametrów.", 400)
    try:
        source = Path(photos_dir).resolve()
        dest = Path(dest_dir)
        dest.mkdir(parents=True, exist_ok=True)
        copied = 0
        for file_name in files:
            if not IMAGE_EXT.search(file_name):
                continue
            source_file = (source / file_name).resolve()
            if source not in source_file.parents and source_file != source:
                continue
            shutil.copy2(source_file, dest / Path(file_name).name)
            copied += 1
        return jsonify({"success": True, "copied": copied})
    except Exception as exc:
        return safe_error(exc, 500)


@app.get("/api/gallery/mounts")
def gallery_mounts():
    mounts = []
    if platform.system() == "Windows":
        for letter in "DEFGHIJKLMNOPQRSTUVWXYZ":
            drive = Path(f"{letter}:\\")
            if drive.exists():
                mounts.append({"label": f"Dysk {letter}:", "path": str(drive)})
    else:
        for base in (Path("/Volumes"), Path("/media") / os.environ.get("USER", ""), Path("/mnt")):
            if base.exists():
                for child in base.iterdir():
                    if child.is_dir():
                        mounts.append({"label": child.name, "path": str(child)})
    return jsonify({"mounts": mounts})


@app.post("/api/gallery/open")
def gallery_open():
    file_path = json_body().get("filePath")
    if file_path and Path(file_path).exists():
        webbrowser.open(Path(file_path).resolve().as_uri())
    return jsonify({"success": True})


@app.post("/api/email/test")
def email_test():
    try:
        imap, _, _ = gmail_login()
        imap.logout()
        return jsonify({"ok": True})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)})


@app.post("/api/email/inbox")
def email_inbox():
    page = max(int(json_body().get("page") or 1), 1)
    per_page = 20
    try:
        imap, _, _ = gmail_login()
        imap.select("INBOX")
        status, data = imap.uid("search", None, "ALL")
        if status != "OK":
            raise RuntimeError("Nie można odczytać skrzynki.")
        uids = data[0].split()[::-1]
        total = len(uids)
        pages = max((total + per_page - 1) // per_page, 1)
        selected = uids[(page - 1) * per_page : page * per_page]
        messages = [m for uid in selected if (m := message_summary(imap, uid))]
        imap.logout()
        return jsonify({"total": total, "pages": pages, "messages": messages})
    except Exception as exc:
        return safe_error(exc, 500)


@app.post("/api/email/search")
def email_search():
    query = json_body().get("query") or ""
    try:
        imap, _, _ = gmail_login()
        imap.select("INBOX")
        status, data = imap.uid("search", None, "TEXT", f'"{query}"')
        if status != "OK":
            raise RuntimeError("Nie można przeszukać skrzynki.")
        uids = data[0].split()[::-1][:50]
        messages = [m for uid in uids if (m := message_summary(imap, uid))]
        imap.logout()
        return jsonify({"total": len(messages), "messages": messages})
    except Exception as exc:
        return safe_error(exc, 500)


@app.post("/api/email/message")
def email_message():
    uid = str(json_body().get("uid") or "")
    if not uid:
        return safe_error("Brak UID wiadomości.", 400)
    try:
        imap, _, _ = gmail_login()
        imap.select("INBOX")
        status, fetched = imap.uid("fetch", uid, "(RFC822)")
        if status != "OK" or not fetched or not fetched[0]:
            raise RuntimeError("Nie znaleziono wiadomości.")
        msg = email.message_from_bytes(fetched[0][1])
        date = ""
        try:
            date = parsedate_to_datetime(msg.get("Date")).isoformat()
        except Exception:
            pass
        imap.logout()
        return jsonify(
            {
                "uid": int(uid),
                "from": decode_mime(msg.get("From")),
                "to": decode_mime(msg.get("To")),
                "subject": decode_mime(msg.get("Subject")) or "(brak tematu)",
                "date": date,
                "text": email_text(msg),
                "messageId": msg.get("Message-ID") or "",
            }
        )
    except Exception as exc:
        return safe_error(exc, 500)


@app.post("/api/email/send")
def email_send():
    data = json_body()
    address, password = data.get("emailAddress"), data.get("appPassword")
    to, subject, text = data.get("to"), data.get("subject"), data.get("text")
    if not all([address, password, to, subject, text]):
        return safe_error("Wypełnij adres, hasło aplikacji, odbiorcę, temat i treść.", 400)
    try:
        msg = EmailMessage()
        msg["From"] = address
        msg["To"] = to
        msg["Subject"] = subject
        if data.get("inReplyTo"):
            msg["In-Reply-To"] = data.get("inReplyTo")
        if data.get("references"):
            msg["References"] = data.get("references")
        msg.set_content(text)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as smtp:
            smtp.login(address, password)
            smtp.send_message(msg)
        return jsonify({"success": True})
    except Exception as exc:
        return safe_error(exc, 500)


@app.post("/api/contacts/google")
def contacts_google():
    return safe_error("Synchronizacja Kontaktów Google nie jest dostępna w tej wersji lokalnej.", 501)


def build_gallery_html(name, session_name, images, output_dir):
    date = datetime.now().strftime("%d.%m.%Y")
    output = str(output_dir)
    photo_items = "\n".join(
        f"""
        <div class="photo-item" data-file="{img}" onclick="toggleSelect(this)">
          <img src="/api/gallery/static?base={requests.utils.quote(output)}&file=photos%2F{requests.utils.quote(img)}" loading="lazy" alt="{img}">
          <div class="photo-name">{img}</div>
        </div>"""
        for img in images
    )
    return f"""<!doctype html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name}</title>
<style>
body{{font-family:Segoe UI,system-ui,sans-serif;margin:0;background:#101010;color:#eee}}
header{{position:sticky;top:0;background:#181818;border-bottom:1px solid #333;padding:16px;z-index:2}}
h1{{margin:0 0 8px;color:#c9a84c;font-size:22px}} .meta{{color:#999;font-size:13px}}
.toolbar{{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:12px}}
button{{border:0;border-radius:7px;padding:8px 12px;font-weight:700;cursor:pointer}}
.gold{{background:#c9a84c;color:#101010}} .ghost{{background:#292929;color:#eee;border:1px solid #444}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px;padding:16px}}
.photo-item{{background:#181818;border:2px solid #333;border-radius:8px;overflow:hidden;cursor:pointer}}
.photo-item.selected{{border-color:#c9a84c}} img{{width:100%;aspect-ratio:4/3;object-fit:cover;display:block}}
.photo-name{{padding:6px 8px;color:#aaa;font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
</style>
</head>
<body>
<header>
  <h1>{name}</h1>
  <div class="meta">{session_name + " · " if session_name else ""}{len(images)} zdjęć · {date} · {APP_NAME} {APP_VERSION}</div>
  <div class="toolbar">
    <button class="ghost" onclick="toggleAll(true)">Zaznacz wszystko</button>
    <button class="ghost" onclick="toggleAll(false)">Odznacz wszystko</button>
    <span id="count">0 zaznaczonych</span>
    <button class="gold" onclick="copySelected()">Kopiuj wybrane</button>
  </div>
</header>
<main class="grid">{photo_items}</main>
<script>
const selected = new Set();
function toggleSelect(el) {{
  const f = el.dataset.file;
  selected.has(f) ? selected.delete(f) : selected.add(f);
  el.classList.toggle('selected', selected.has(f));
  document.getElementById('count').textContent = selected.size + ' zaznaczonych';
}}
function toggleAll(on) {{ document.querySelectorAll('.photo-item').forEach(el => {{ if (on !== selected.has(el.dataset.file)) toggleSelect(el); }}); }}
async function copySelected() {{
  const dest = prompt('Folder docelowy:');
  if (!dest || !selected.size) return;
  const res = await fetch('/api/gallery/copy-files', {{
    method:'POST', headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{photosDir:{json.dumps(str(Path(output_dir) / "photos"))}, files:[...selected], destDir:dest}})
  }});
  const data = await res.json();
  alert(res.ok ? 'Skopiowano: ' + data.copied : data.error);
}}
</script>
</body>
</html>"""


if __name__ == "__main__":
    print(f"{APP_NAME} {APP_VERSION} ({AUTHOR}) działa na http://localhost:{PORT}")
    if os.environ.get("FOTO_STUDIO_NO_BROWSER") != "1":
        threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()
    app.run(host="127.0.0.1", port=PORT)
