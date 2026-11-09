# sms-code-relay

Get the verification codes texted to your iPhone onto your Windows PC's clipboard, so you can paste them with **Ctrl+V**.

iPhones don't let apps read your texts, so this has two parts:

- **iPhone:** a Shortcuts automation that sends each text containing "code" to your PC.
- **PC:** `sms_code.py`, a small Python script that finds the code, copies it to the clipboard and beeps.

It works while your phone and PC are on the same Wi-Fi. It uses only Python's standard library, so there's nothing to install apart from Python.

## Requirements

- Windows 10 or 11
- [Python 3.8 or newer](https://www.python.org/downloads/)
- An iPhone with the Shortcuts app (iOS 17 or newer, for "Run Immediately")

## Set up the PC

1. Download this repo: click **Code → Download ZIP** and unzip it, or run:

   ```bash
   git clone https://github.com/fayofye/sms-code-relay.git
   ```

2. In that folder, run:

   ```bash
   python sms_code.py
   ```

3. It prints a **URL** (like `http://192.168.1.20:8765/`) and a **Token**. Keep the window open.
4. When Windows Firewall asks about Python, allow it on **Private networks**.

The token is created on first run and saved in `token.txt`. It stops other devices on your network from sending things to your clipboard, so don't share it.

## Set up the iPhone

1. Open **Shortcuts** → **Automation** tab → **+** → **Message**.
2. Set **Message Contains** to `code`, choose **Run Immediately**, then tap **Next** → **New Blank Automation**.
3. Add the **Get Contents of URL** action and set:
   - **URL:** the URL the script printed
   - **Method:** POST
   - **Headers:** `X-Token` = the token the script printed
   - **Request Body:** JSON, with one Text field named `text` set to **Shortcut Input → Content**
4. Tap **Done**.

If some services say "PIN" or "OTP" instead of "code", add a second automation with that word.

## Use it

When a code arrives, the PC beeps and the console shows `Copied 123456`. Click the code box and press **Ctrl+V**.

## Security notes

- Codes travel over your home Wi-Fi without encryption. That's fine for short-lived codes on a network you trust; don't use it on public Wi-Fi.
- Requests without the right token are rejected.
- To use it away from home, install [Tailscale](https://tailscale.com/) on both devices and use the PC's Tailscale IP in the Shortcut.

## Test

```bash
python test_sms_code.py
```

This puts `482913` on your clipboard.

## License

MIT, see [LICENSE](LICENSE).
