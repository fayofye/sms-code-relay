"""Run: python test_sms_code.py  (puts 482913 on your clipboard and shows a few test notifications)"""
import json
import os
import subprocess
import threading
import urllib.error
import urllib.request
import winreg

import sms_code

assert sms_code.find_code("Your Chase code is 482913. Don't share it.") == "482913"
assert sms_code.find_code("G-771204 is your Google verification code.") == "771204"
assert sms_code.find_code("On 2026-11-08 your code is 553201") == "553201"
assert sms_code.find_code("Your PIN: 4821") == "4821"
assert sms_code.find_code("Call 800-555-12") is None

sms_code.TOKEN = "test-token"
server = sms_code.Server(("127.0.0.1", 0), sms_code.Handler)  # loopback only, so no firewall prompt
threading.Thread(target=server.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{server.server_port}/"


def post(token, body):
    data = body if isinstance(body, bytes) else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={"X-Token": token})
    try:
        return urllib.request.urlopen(req).status
    except urllib.error.HTTPError as e:
        return e.code


def clipboard():
    return subprocess.run(["powershell", "-NoProfile", "-Command", "Get-Clipboard"], capture_output=True, text=True).stdout.strip()


assert post("wrong", {"text": "code 111111"}) == 403
assert post("test-token", {"nope": 1}) == 422
assert post("test-token", {"text": "hello"}) == 422
assert post("test-token", b"") == 422  # a test run from the Shortcut editor, with no message
assert post("test-token", {"Your code is 771204": "text"}) == 204  # key and value swapped in the Shortcut
assert clipboard() == "771204"
assert post("test-token", b"Your code is 553201") == 204  # plain-text body
assert clipboard() == "553201"
assert post("test-token", {"text": "Your code is 482913"}) == 204
assert clipboard() == "482913"

# a second copy must fail to start rather than silently share the port
try:
    sms_code.Server(("127.0.0.1", server.server_port), sms_code.Handler)
    raise AssertionError("second server bound the same port")
except OSError:
    pass

# notification script runs without errors
assert sms_code.powershell(sms_code.TOAST, {**os.environ, "CODE": "000000"}).wait() == 0

# sign-in entry, under a test name so a real install isn't touched
sms_code.RUN_NAME = "sms-code-relay-test"
sms_code.set_autostart(True)
with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sms_code.RUN_KEY) as key:
    value = winreg.QueryValueEx(key, "sms-code-relay-test")[0]
assert "pythonw.exe" in value and "sms_code.py" in value, value
sms_code.set_autostart(False)
sms_code.set_autostart(False)  # removing twice is fine
with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sms_code.RUN_KEY) as key:
    try:
        winreg.QueryValueEx(key, "sms-code-relay-test")
        raise AssertionError("sign-in entry not removed")
    except FileNotFoundError:
        pass

print("all tests passed")
