"""Run: python test_sms_code.py  (note: puts 482913 on your clipboard)"""
import json
import subprocess
import threading
import urllib.error
import urllib.request
from http.server import HTTPServer

import sms_code

assert sms_code.find_code("Your Chase code is 482913. Don't share it.") == "482913"
assert sms_code.find_code("G-771204 is your Google verification code.") == "771204"
assert sms_code.find_code("On 2026-11-08 your code is 553201") == "553201"
assert sms_code.find_code("Your PIN: 4821") == "4821"
assert sms_code.find_code("Call 800-555-12") is None

sms_code.TOKEN = "test-token"
server = HTTPServer(("127.0.0.1", 0), sms_code.Handler)  # loopback only, so no firewall prompt
threading.Thread(target=server.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{server.server_port}/"


def post(token, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"X-Token": token})
    try:
        return urllib.request.urlopen(req).status
    except urllib.error.HTTPError as e:
        return e.code


assert post("wrong", {"text": "code 111111"}) == 403
assert post("test-token", {"nope": 1}) == 400
assert post("test-token", {"text": "hello"}) == 422
assert post("test-token", {"text": "Your code is 482913"}) == 204
clip = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-Clipboard"], capture_output=True, text=True).stdout.strip()
assert clip == "482913", clip
print("all tests passed")
