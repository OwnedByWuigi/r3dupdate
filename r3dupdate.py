#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_r3dfox_fullinstall.py
Windows 7+ updater for r3dfox full install.
Matches: r3dfox-VERSION.en-US.winBITS.installer.exe
"""

import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from urllib.error import HTTPError, URLError

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
INSTALL_ROOT = r"C:\Program Files\Eclipse Community"
INSTALL_DIR  = os.path.join(INSTALL_ROOT, "r3dfox")
FIREFOX_EXE  = os.path.join(INSTALL_DIR, "r3dfox.exe")
APP_INI      = os.path.join(INSTALL_DIR, "application.ini")

LATEST_API   = "https://api.github.com/repos/Eclipse-Community/r3dfox/releases/latest"

if platform.system() != "Windows":
    print("Error: This script only runs on Windows.")
    sys.exit(1)

winver = platform.win32_ver()[1]

# 64-bit detection (works on Win7)
import struct
is_64bit = struct.calcsize("P") == 8
arch = "win64" if is_64bit else "win32"
print(f"Detected: Windows {winver.split('.')[0]}, {arch}")

if not os.path.exists(INSTALL_DIR):
    print(f"r3dfox not installed in:\n  {INSTALL_DIR}")
    print("Please install r3dfox first.")
    sys.exit(1)

if not os.path.exists(FIREFOX_EXE):
    print("firefox.exe missing. Corrupted install?")
    sys.exit(1)

def get_current_version():
    if not os.path.exists(APP_INI):
        return None
    try:
        with open(APP_INI, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if line.strip().startswith("Version="):
                    return line.split("=", 1)[1].strip()
    except:
        pass
    return None

current_version = get_current_version()
print(f"Current version: {current_version or 'Unknown'}")

print("Fetching latest release...")
try:
    req = urllib.request.Request(
        LATEST_API,
        headers={'User-Agent': 'r3dfox-updater/1.0'}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    latest_tag = data['tag_name'].lstrip('v')  # e.g., "144.0.2"
    print(f"Latest version: {latest_tag}")
except Exception as e:
    print(f"Failed to fetch release: {e}")
    sys.exit(1)

# Skip if already up to date
if current_version and current_version >= latest_tag:
    print("You are already up to date!")
    sys.exit(0)

installer_url = None
installer_name = None
pattern = f"r3dfox-{latest_tag}.en-US.{arch}.installer.exe"

for asset in data.get('assets', []):
    name = asset['name']
    if name == pattern:
        installer_url = asset['browser_download_url']
        installer_name = name
        break

if not installer_url:
    print(f"Installer not found: {pattern}")
    print("Available installers:")
    for asset in data.get('assets', []):
        if asset['name'].endswith('.exe'):
            print(f"  - {asset['name']}")
    sys.exit(1)

print(f"Found installer: {installer_name}")

temp_dir = tempfile.mkdtemp(prefix='r3dfox_update_')
installer_path = os.path.join(temp_dir, installer_name)

print(f"Downloading...\n  → {installer_path}")
try:
    req = urllib.request.Request(
        installer_url,
        headers={'User-Agent': 'r3dfox-updater/1.0'}
    )
    with urllib.request.urlopen(req, timeout=60) as src, open(installer_path, 'wb') as dst:
        shutil.copyfileobj(src, dst)
    print("Download complete.")
except Exception as e:
    print(f"Download failed: {e}")
    sys.exit(1)

print("Installing silently (this may take a moment)...")
try:
    cmd = [installer_path, '/S']  # Silent mode
    proc = subprocess.run(cmd)
    if proc.returncode == 0:
        print(f"Successfully updated to {latest_tag}!")
    else:
        print(f"Installer exited with code {proc.returncode}")
        if proc.stdout:
            print("STDOUT:", proc.stdout)
        if proc.stderr:
            print("STDERR:", proc.stderr)
except subprocess.TimeoutExpired:
    print("Installer timed out.")
except Exception as e:
    print(f"Failed to run installer: {e}")
finally:
    # Cleanup
    try:
        shutil.rmtree(temp_dir)
    except:
        pass