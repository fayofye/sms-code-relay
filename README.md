# sms-code-relay

Get the verification codes texted to your iPhone onto your Windows PC, ready to paste.

When a text with a code arrives, your PC shows a notification ("Code 482913 copied") and the code is already on your clipboard. Click the code box and press **Ctrl+V**.

iPhones don't let apps read your texts, so this has two parts:

- **iPhone:** a Shortcuts automation that sends each text containing "code" to your PC.
- **PC:** a small Python script that runs in the background, finds the code and copies it.

It works when your phone and PC are on the same Wi-Fi. Apart from Python, there's nothing to install.

## What you need

- A Windows 10 or 11 PC
- [Python 3.8 or newer](https://www.python.org/downloads/). In the installer, tick **Add python.exe to PATH**.
- An iPhone on iOS 17 or newer

## 1. Set up the PC (2 minutes)

1. On this page, click **Code → Download ZIP**.
2. Unzip it somewhere permanent, like your Documents folder. It runs from there, so don't leave it in Downloads.
3. Double-click **`install.bat`**. A window shows two things the iPhone needs:

   ```
   Put these in the iPhone Shortcut:
     URL:   http://192.168.1.20:8765/
     Token: (a random string, different for every PC)
   ```

   Keep that window open while you set up the iPhone. The script now runs hidden in the background and starts again each time you sign in to Windows.
4. If Windows asks whether to let Python through the firewall, tick **Private networks** and click **Allow access**.

## 2. Set up the iPhone (5 minutes)

Apple changed how automations work in iOS 27, so the steps depend on your version. To check yours, go to **Settings → General → About → iOS Version**.

Either way, you need the **URL** and **Token** from the PC window (step 1.3 above).

### iOS 27

1. Open the **Shortcuts** app and tap **+** to make a new shortcut.
2. In the list of actions, tap **Automation**, then **Message**.
3. The trigger reads **When I receive a message where Sender is…**. You don't need a sender: tap the word **Sender** and change it to **Message**. It now reads **Message contains**.
4. Tap the empty box after **contains**, type `code`, and tap **✓**.
5. Under the trigger, make sure **Automation** is **on** and **Confirm Before Run** is **off**. This replaced "Run Immediately".
6. Tap the search bar at the bottom, search for **Get Contents of URL**, and tap it to add it.
7. Tap **URL** and type the URL from the PC window, for example `http://192.168.1.20:8765/`.
8. Tap the **›** arrow next to the URL to show more options, then set:
   - **Method:** tap it and choose **POST**.
   - **Headers:** tap **Add new header**. Type `X-Token` as the key, and paste the token from the PC window as the value.
   - **Request Body:** choose **JSON**. Tap **Add new field → Text**, type `text` as the key, then tap the value, choose **Select Variable**, and tap **Message**.
9. Tap back to save it. It now appears in **All Shortcuts**.
10. So that it works while your phone is locked, open the shortcut, tap **Edit**, then the **ⓘ** button, then **Privacy**, and turn on **Allow Running When Locked**.

### iOS 26 or earlier

1. Open the **Shortcuts** app and tap the **Automation** tab at the bottom.
2. Tap **+** (or **New Automation**), scroll down and tap **Message**.
3. Tap **Message Contains**, type `code`, and tap **Done**. Leave **Sender** empty: you only need one of the two.
4. Choose **Run Immediately**. Optionally, turn off **Notify When Run** so you don't get an extra banner each time.
5. Tap **Next**, then **New Blank Automation**.
6. Search for **Get Contents of URL** and tap it to add it.
7. Tap the blue **URL** field and type the URL from the PC window, for example `http://192.168.1.20:8765/`.
8. Tap the **›** arrow on the action to show its options, then set:
   - **Method:** POST
   - **Headers:** tap **Add new header**. Set the key to `X-Token` and the value to the token from the PC window.
   - **Request Body:** JSON. Tap **Add new field → Text**, type `text` as the key, then tap the value and pick **Shortcut Input** from the bar above the keyboard.
9. Tap **Done**.

### Test it

Get a real code sent to you, such as a "text me a code" sign-in. Your PC should show the notification within a couple of seconds.

The first time it runs, the iPhone may ask to let Shortcuts **find devices on your local network** or **connect to 192.168…**. Tap **Allow**.

Some services say "PIN", "OTP" or "passcode" instead of "code". For those, make a second shortcut (or automation) the same way, with that word instead of `code`.

## Troubleshooting

- **Nothing happens on the PC:**
  - Check the phone and PC are on the same Wi-Fi.
  - On the iPhone, go to **Settings → Privacy & Security → Local Network** and make sure **Shortcuts** is on.
  - On iOS 27, open the shortcut and check that **Automation** is on, **Confirm Before Run** is off, and **Allow Running When Locked** is on.
  - On iOS 26 or earlier, turn **Notify When Run** back on to check that the automation fires at all.
- **The PC is locked:** Windows blocks the clipboard while it's locked, so a code that arrives then is skipped. Unlock first.
- **It worked, then stopped:** your PC's IP address probably changed. Double-click `install.bat` again to see the new URL, then update it in the Shortcut. To stop the IP changing, reserve it in your router's settings (look for "DHCP reservation").
- **Windows treats your Wi-Fi as public:** the firewall then blocks the phone. Go to **Settings → Network & Internet → Wi-Fi → (your network)** and set it to **Private**.
- **Anything else:** look at `sms_code.log` in the folder. It records every request.

## Uninstall

Double-click **`uninstall.bat`**. That stops the script and removes it from sign-in. Then delete the folder, and delete the shortcut (or automation) on your iPhone.

## Run it in a window instead

```bash
python sms_code.py
```

This shows each code as it arrives, and closing the window stops it. If the background copy is already running, this says so and exits.

## Security notes

- Requests without your token are rejected. The token is created on first run and stored in `token.txt`; don't share it.
- Codes travel over your Wi-Fi without encryption. That's fine for short-lived codes on your home network; don't use it on public Wi-Fi.
- To use it away from home, install [Tailscale](https://tailscale.com/) on both devices and use the PC's Tailscale IP in the Shortcut.

## Test

```bash
python test_sms_code.py
```

The test puts `482913` on your clipboard and shows two test notifications. Run it while the PC is unlocked.

## License

MIT, see [LICENSE](LICENSE).
