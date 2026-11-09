"""SMS code -> PC clipboard. An iPhone Shortcut POSTs each text message here; we pull out the code and copy it.

Run:  python sms_code.py   (prints the URL and token to put in the Shortcut)
"""
import json
import re
import secrets
import socket
import subprocess
import winsound
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

PORT = 8765
TOKEN_FILE = Path(__file__).with_name("token.txt")
TOKEN = ""  # set in main(); the Shortcut must send it as the X-Token header


def find_code(text):
    # Prefer a 6-digit run (most OTPs), so dates/years in the message don't win; else any 4-8 digit run.
    m = re.search(r"(?<!\d)\d{6}(?!\d)", text) or re.search(r"(?<!\d)\d{4,8}(?!\d)", text)
    return m.group() if m else None


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if not secrets.compare_digest(self.headers.get("X-Token", "").encode(), TOKEN.encode()):
            return self.send_error(403)
        try:
            length = int(self.headers.get("Content-Length", 0))
            if not 0 < length <= 10_000:
                return self.send_error(413)
            text = str(json.loads(self.rfile.read(length))["text"])
        except (ValueError, KeyError, TypeError):
            return self.send_error(400)
        code = find_code(text)
        if not code:
            return self.send_error(422, "no code found")
        subprocess.run("clip", input=code, text=True, check=True)
        winsound.MessageBeep()
        print(f"Copied {code} - press Ctrl+V")
        self.send_response(204)
        self.end_headers()


def main():
    global TOKEN
    if not TOKEN_FILE.exists():
        TOKEN_FILE.write_text(secrets.token_urlsafe(16))
    TOKEN = TOKEN_FILE.read_text().strip()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))  # UDP connect sends nothing; it just picks the LAN IP
        ip = s.getsockname()[0]
    # shortcut: plain HTTP on your home Wi-Fi only; to work on cellular, run Tailscale on both and use the PC's Tailscale IP.
    print(f"URL:   http://{ip}:{PORT}/\nToken: {TOKEN}\nWaiting for codes... (Ctrl+C to stop)")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
