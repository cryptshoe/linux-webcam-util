#!/usr/bin/env python3

import os
import subprocess
import sys
import re

# File dialog support
try:
    import tkinter as tk
    from tkinter import filedialog
except ImportError:
    print("tkinter is required for the file dialog. Please install it (e.g., sudo apt install python3-tk).")
    sys.exit(1)

GUV_PROFILE_TO_V4L2 = {
    "Brightness": "brightness",
    "Contrast": "contrast",
    "Saturation": "saturation",
    "Hue": "hue",
    "Gamma": "gamma",
    "Gain": "gain",
    "Sharpness": "sharpness",
    "White Balance, Automatic": "white_balance_temperature_auto",
    "White Balance Temperature": "white_balance_temperature",
    "Backlight Compensation": "backlight_compensation",
    "Power Line Frequency": "power_line_frequency",
    "Auto Exposure": "exposure_auto",
    "Exposure, Dynamic Framerate": "exposure_dynamic_framerate",
    "Pan, Absolute": "pan_absolute",
    "Tilt, Absolute": "tilt_absolute",
    "Focus, Absolute": "focus_absolute",
    "Focus, Automatic Continuous": "focus_auto",
    "Zoom, Absolute": "zoom_absolute",
    "Exposure, Auto Priority": "exposure_auto_priority",
}

GUV_CONFIG_TO_V4L2 = {
    "brightness": "brightness",
    "contrast": "contrast",
    "saturation": "saturation",
    "gain": "gain",
    "sharpness": "sharpness",
    "gamma": "gamma",
    "exposure_abs": "exposure_absolute",
    "exposure_auto": "exposure_auto",
    "white_balance_temperature_auto": "white_balance_temperature_auto",
    "white_balance_temperature": "white_balance_temperature",
    "focus_auto": "focus_auto",
    "focus_abs": "focus_absolute",
}

def list_video_devices():
    devices = []
    for dev in sorted(os.listdir('/dev')):
        if dev.startswith('video'):
            path = f'/dev/{dev}'
            try:
                info = subprocess.check_output(
                    f'v4l2-ctl -d {path} --info', shell=True, stderr=subprocess.DEVNULL
                ).decode().strip()
            except Exception:
                info = "Unknown device"
            devices.append((path, info))
    return devices

def select_from_list(options, prompt):
    print(prompt)
    for idx, (dev, info) in enumerate(options):
        print(f"{idx+1}: {dev} ({info.splitlines()[0]})")
    while True:
        try:
            choice = int(input("Enter the number of your choice: "))
            if 1 <= choice <= len(options):
                return options[choice-1][0]
        except Exception:
            pass
        print("Invalid selection, try again.")

def prompt_for_config_file():
    print("\nHow would you like to select the GUVCView config file?")
    print("1: Enter the path manually")
    print("2: Open file explorer to select the file")
    while True:
        choice = input("Enter 1 or 2: ").strip()
        if choice == "2":
            root = tk.Tk()
            root.withdraw()
            file_path = filedialog.askopenfilename(
                title="Select GUVCView config or profile file",
                filetypes=[("GUVCView files", "*.gpfl *.conf *video* *rc*"), ("All files", "*.*")]
            )
            root.destroy()
            if file_path and os.path.isfile(file_path):
                print(f"Selected: {file_path}")
                return file_path
            else:
                print("No file selected. Please try again.")
        elif choice == "1":
            while True:
                path = input("Enter the full path to your GUVCView config file (e.g. ~/.config/guvcview2/video0 or ~/Documents/default.gpfl): ").strip()
                path = os.path.expanduser(path)
                if os.path.isfile(path):
                    return path
                print("File not found, try again.")
        else:
            print("Invalid selection, try again.")

def parse_guvcview_profile(profile_path):
    settings = {}
    last_ctrl_name = None
    with open(profile_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") and not line.startswith("#V4L2/CTRL"):
                last_ctrl_name = line.lstrip("#").strip()
            elif "=VAL{" in line and last_ctrl_name:
                m = re.search(r"=VAL{([-\d]+)}", line)
                if m:
                    val = m.group(1)
                    v4l2_ctrl = GUV_PROFILE_TO_V4L2.get(last_ctrl_name)
                    if v4l2_ctrl:
                        settings[v4l2_ctrl] = val
                last_ctrl_name = None
    return settings

def parse_guvcview_config(config_path):
    settings = {}
    with open(config_path) as f:
        for line in f:
            if "=" in line:
                key, val = line.strip().split("=", 1)
                key = key.strip()
                val = val.strip()
                if key in GUV_CONFIG_TO_V4L2:
                    if val.lower() in ("true", "yes", "on"):
                        val = "1"
                    elif val.lower() in ("false", "no", "off"):
                        val = "0"
                    settings[GUV_CONFIG_TO_V4L2[key]] = val
    return settings

def parse_guvcview_config_or_profile(path):
    with open(path) as f:
        first_line = f.readline()
    if path.endswith('.gpfl') or first_line.startswith('#V4L2/CTRL'):
        return parse_guvcview_profile(path)
    else:
        return parse_guvcview_config(path)

def write_restore_script(settings, script_path, device):
    with open(script_path, "w") as f:
        f.write("#!/bin/bash\n")
        for ctrl, val in settings.items():
            f.write(f"v4l2-ctl -d {device} -c {ctrl}={val}\n")
    os.chmod(script_path, 0o755)
    print(f"Restore script written to {script_path}")

def setup_autostart(script_path):
    autostart_dir = os.path.expanduser("~/.config/autostart")
    os.makedirs(autostart_dir, exist_ok=True)
    autostart_file = os.path.join(autostart_dir, "restore-webcam-settings.desktop")
    with open(autostart_file, "w") as f:
        f.write(f"""[Desktop Entry]
Type=Application
Exec={script_path}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=Restore Webcam Settings
""")
    print(f"Autostart entry created at {autostart_file}")

def get_usb_ids(device):
    try:
        udev_info = subprocess.check_output(
            f"udevadm info --query=all --name={device}", shell=True
        ).decode()
        vid, pid = None, None
        for line in udev_info.splitlines():
            if "ID_VENDOR_ID=" in line:
                vid = line.split("=",1)[1].strip()
            if "ID_MODEL_ID=" in line:
                pid = line.split("=",1)[1].strip()
        return vid, pid
    except Exception as e:
        print("Could not determine USB IDs for udev rule:", e)
        return None, None

def setup_udev_rule(script_path, device):
    vid, pid = get_usb_ids(device)
    if not (vid and pid):
        print("Skipping udev rule creation (could not determine USB IDs).")
        return
    rule = (
        f'ACTION=="add", SUBSYSTEM=="video4linux", '
        f'ATTRS{{idVendor}}=="{vid}", ATTRS{{idProduct}}=="{pid}", '
        f'RUN+="{script_path}"\n'
    )
    udev_rule_path = "/etc/udev/rules.d/99-webcam-settings.rules"
    tmp_rule = "/tmp/99-webcam-settings.rules"
    with open(tmp_rule, "w") as f:
        f.write(rule)
    print(f"Creating udev rule at {udev_rule_path} (requires sudo)...")
    try:
        subprocess.run(f"sudo mv {tmp_rule} {udev_rule_path}", shell=True, check=True)
        subprocess.run("sudo udevadm control --reload-rules", shell=True, check=True)
        subprocess.run("sudo udevadm trigger", shell=True, check=True)
        print("udev rule installed and reloaded.")
    except Exception as e:
        print("Failed to install udev rule:", e)

def run_restore_script(script_path):
    print(f"Applying settings immediately by running: {script_path}")
    subprocess.run([script_path])

def setup_systemd_service(script_path):
    service_name = "restore-webcam-settings"
    service_path = f"/etc/systemd/system/{service_name}.service"
    python_path = sys.executable
    user = os.environ.get("USER")
    with open("/tmp/restore-webcam-settings.service", "w") as f:
        f.write(f"""[Unit]
Description=Restore webcam settings at boot
After=network.target

[Service]
Type=oneshot
ExecStart={script_path}
User={user}

[Install]
WantedBy=multi-user.target
""")
    print(f"Creating systemd service at {service_path} (requires sudo)...")
    try:
        subprocess.run(f"sudo mv /tmp/restore-webcam-settings.service {service_path}", shell=True, check=True)
        subprocess.run("sudo systemctl daemon-reload", shell=True, check=True)
        subprocess.run(f"sudo systemctl enable {service_name}.service", shell=True, check=True)
        print(f"Systemd service {service_name}.service enabled.")
    except Exception as e:
        print("Failed to install systemd service:", e)

def main():
    devices = list_video_devices()
    if not devices:
        print("No video devices found.")
        sys.exit(1)
    device = select_from_list(devices, "Select the camera to apply settings to:")

    config_path = prompt_for_config_file()

    settings = parse_guvcview_config_or_profile(config_path)
    if not settings:
        print("No relevant settings found in GUVCView config/profile.")
        print("\nIf you selected a GUVCView profile (.gpfl), make sure it contains control data.")
        sys.exit(1)
    restore_script = os.path.expanduser("~/.restore-webcam-settings.sh")
    write_restore_script(settings, restore_script, device)

    setup_autostart(restore_script)
    setup_udev_rule(restore_script, device)
    run_restore_script(restore_script)

    print("\nWould you like to also set up a systemd service to apply settings at system boot (before login)?")
    print("1: Yes")
    print("2: No")
    choice = input("Enter 1 or 2: ").strip()
    if choice == "1":
        setup_systemd_service(restore_script)

    print("\nAll done! Your webcam settings will now persist at login and when the camera is reconnected.")
    print(f"To apply settings manually, run:\n  {restore_script}")

if __name__ == "__main__":
    main()
