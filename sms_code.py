"""SMS code -> PC clipboard. An iPhone Shortcut POSTs each text message here; we pull out the code and copy it.

python sms_code.py              run in this window (shows the URL and token for the Shortcut)
python sms_code.py --install    run hidden now and every time you sign in to Windows
python sms_code.py --uninstall  stop the hidden copy and remove it from sign-in
"""
import base64
import json
import os
import re
import secrets
import socket
import subprocess
import sys
import winreg
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

PORT = 8765
SCRIPT = Path(__file__).resolve()
TOKEN_FILE = SCRIPT.with_name("token.txt")
LOG_FILE = SCRIPT.with_name("sms_code.log")
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_NAME = "sms-code-relay"
PYTHONW = Path(sys.executable).with_name("pythonw.exe")
NO_WINDOW = subprocess.CREATE_NO_WINDOW  # stops console windows flashing up when running hidden
TOKEN = ""  # set in main(); the Shortcut must send it as the X-Token header

# Toast under PowerShell's own app ID, so nothing needs installing. The code arrives via $env:CODE, never the script text.
TOAST = r"""$ErrorActionPreference = 'Stop'
$m = [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]
$x = $m::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
$t = $x.GetElementsByTagName('text')
$t.Item(0).AppendChild($x.CreateTextNode("Code $env:CODE copied")) > $null
$t.Item(1).AppendChild($x.CreateTextNode('Press Ctrl+V to paste it')) > $null
$m::CreateToastNotifier('{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe').Show([Windows.UI.Notifications.ToastNotification]::new($x))
"""
STOP = r"""Get-CimInstance Win32_Process -Filter "Name='pythonw.exe'" |
  Where-Object CommandLine -like '*sms_code.py*' | Invoke-CimMethod -MethodName Terminate > $null"""


def powershell(script, env=None):
    cmd = ["powershell", "-NoProfile", "-EncodedCommand", base64.b64encode(script.encode("utf-16-le")).decode()]
    return subprocess.Popen(cmd, env=env, creationflags=NO_WINDOW)


def find_code(text):
    # Prefer a 6-digit run (most codes), so dates/years in the message don't win; else any 4-8 digit run.
    m = re.search(r"(?<![0-9])[0-9]{6}(?![0-9])", text) or re.search(r"(?<![0-9])[0-9]{4,8}(?![0-9])", text)
    return m.group() if m else None


class Server(HTTPServer):
    allow_reuse_address = False  # on Windows, reuse lets a second copy share the port; we want it to fail instead


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
        try:
            subprocess.run("clip", input=code, text=True, check=True, creationflags=NO_WINDOW)
        except subprocess.CalledProcessError:  # Windows blocks the clipboard while the PC is locked
            return self.send_error(503, "couldn't copy the code - is the PC locked?")
        powershell(TOAST, {**os.environ, "CODE": code})
        print(f"Copied {code}")
        self.send_response(204)
        self.end_headers()


def set_autostart(on):
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        if on:
            winreg.SetValueEx(key, RUN_NAME, 0, winreg.REG_SZ, f'"{PYTHONW}" "{SCRIPT}"')
        else:
            try:
                winreg.DeleteValue(key, RUN_NAME)
            except FileNotFoundError:
                pass


def main():
    global TOKEN
    if sys.stdout is None:  # pythonw has no console, so log to a file
        sys.stdout = sys.stderr = open(LOG_FILE, "a", buffering=1, encoding="utf-8")
    if "--uninstall" in sys.argv:
        set_autostart(False)
        powershell(STOP).wait()
        return print("Stopped, and it won't start when you sign in any more.")
    if not TOKEN_FILE.exists():
        TOKEN_FILE.write_text(secrets.token_urlsafe(16))
    TOKEN = TOKEN_FILE.read_text().strip()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))  # UDP connect sends nothing; it just picks the LAN IP
            ip = s.getsockname()[0]
    except OSError:  # no network yet (e.g. right after sign-in); the server still works once Wi-Fi connects
        ip = "<this PC's IP>"
    # shortcut: plain HTTP on your home Wi-Fi only; to work on cellular, run Tailscale on both and use the PC's Tailscale IP.
    print(f"Put these in the iPhone Shortcut:\n  URL:   http://{ip}:{PORT}/\n  Token: {TOKEN}\n")
    if "--install" in sys.argv:
        if not PYTHONW.exists():
            return print(f"Can't find {PYTHONW}, so can't run hidden. Run 'python sms_code.py' instead.")
        set_autostart(True)
        subprocess.Popen([str(PYTHONW), str(SCRIPT)], creationflags=NO_WINDOW)
        return print("Installed: it's running in the background now and starts whenever you sign in to Windows.")
    try:
        server = Server(("0.0.0.0", PORT), Handler)
    except OSError:
        return print(f"Already running in the background (port {PORT} is in use), so nothing else to do.")
    print("Waiting for codes... (close this window to stop)")
    server.serve_forever()


if __name__ == "__main__":
    main()
