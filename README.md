# Linux Webcam Utility

A Python utility to persist and restore Logitech (or other UVC) webcam settings on Linux.  
This script extracts settings from GUVCView config or profile files and ensures your preferred camera configuration is always applied-at login, at boot, and whenever the camera is reconnected.

---

## Features

- **Extracts settings** from GUVCView config (`video0`, etc.) or profile (`.gpfl`) files.
- **Generates a restore script** to apply settings using `v4l2-ctl`.
- **Sets up desktop autostart** so settings are restored at every login.
- **Creates a udev rule** to re-apply settings whenever the camera is plugged in.
- **Optionally sets up a systemd service** to apply settings at system boot (before login).
- **Applies settings immediately** after setup.

---

## Requirements

- Python 3
- `v4l-utils` (`sudo apt install v4l-utils`)
- `tkinter` (`sudo apt install python3-tk`)
- `sudo` privileges (for udev rule and optional systemd service)

---

# Install GUVCView and Save Your Webcam Profile
## Install GUVCView

- On Ubuntu, Debian, Linux Mint, or derivatives:
```
sudo apt update
sudo apt install guvcview
```
- On Fedora:
```
sudo dnf install guvcview
```
- On openSUSE:
```
sudo zypper install guvcview
```
- On Arch Linux/Manjaro:
```
sudo pacman -S guvcview
```
- Or use Snap (works on most distributions):
```
sudo snap install guvcview
```
## Configure Your Webcam Settings

- Launch GUVCView from your applications menu or by running guvcview in a terminal.
- Select your webcam device if prompted.
- Adjust the image, video, and audio settings as desired (e.g., brightness, contrast, resolution, etc.).
- Test your settings in the preview window.
- Save Your Profile
- In GUVCView, go to the menu and choose Settings → Save profile.
- Choose a location and filename for your profile (for example, ~/Documents/default.gpfl).

This .gpfl file contains all your custom webcam settings and will be used by this script to persist your configuration.

---

## Usage

1. **Install dependencies:**
sudo apt install v4l-utils python3-tk


2. **Run the script:**
python3 linux-webcam-util.py


3. **Follow the prompts:**
- Select your webcam device.
- Choose your GUVCView config or profile file (manual path or file explorer).
- The script will parse your settings, generate a restore script, set up autostart and udev rules, and apply the settings immediately.
- Optionally, you can enable a systemd service for system-wide boot-time restoration.

---

## How It Works

- **Settings Extraction:**  
The script parses GUVCView config (`key=value`) or `.gpfl` profile (two-line control/value) files and maps them to `v4l2-ctl` controls.
- **Restore Script:**  
A shell script is generated at `~/.restore-webcam-settings.sh` to apply your settings.
- **Autostart:**  
A `.desktop` entry is created in `~/.config/autostart` to run the restore script at login.
- **udev Rule:**  
A rule in `/etc/udev/rules.d/99-webcam-settings.rules` ensures settings are reapplied when the camera is reconnected (requires `sudo`).
- **Systemd Option:**  
You can optionally enable a systemd service to apply settings at system boot (requires `sudo`).

---

## Uninstall

To remove all persistent settings:

- Delete the autostart entry:
rm ~/.config/autostart/restore-webcam-settings.desktop

- Remove the udev rule (requires `sudo`):
sudo rm /etc/udev/rules.d/99-webcam-settings.rules
sudo udevadm control --reload-rules

- Remove the systemd service (if enabled):
sudo systemctl disable restore-webcam-settings.service
sudo rm /etc/systemd/system/restore-webcam-settings.service
sudo systemctl daemon-reload


---

## Troubleshooting

- **No settings applied:**  
Ensure your GUVCView config/profile contains valid controls and that `v4l2-ctl` is installed.
- **udev rule not working:**  
Make sure you ran the script with `sudo` when prompted for udev rule creation.
- **tkinter error:**  
Install with `sudo apt install python3-tk`.
