#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_r3dfox_fullinstall.py
Windows 7+ compatible updater for r3dfox full install.
Downloads and runs the latest .exe installer silently.
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

# Installer patterns (adjust if filename changes)
ASSET_PATTERNS = {
    "win32": ["r3dfox-win32-installer.exe", "r3dfox-setup-win32.exe"],
    "win64": ["r3dfox-win64-installer.exe", "r3dfox-setup-win64.exe"],
}

# ----------------------------------------------------------------------
# 1. Windows 7+ Check
# ----------------------------------------------------------------------
if platform.system() != "Windows":
    print("This script only runs on Windows.")
    sys.exit(1)

winver = platform.win32_ver()[1]
if winver < "6.1":
    print("Windows 7 or later required.")
    sys.exit(1)

# ----------------------------------------------------------------------
# 2. Detect architecture (Win7-safe)
# ----------------------------------------------------------------------
import struct
is_64bit = struct.calcsize("P") == 8
arch = "win64" if is_64bit else "win32"
print(f"Architecture: {arch}")

# ----------------------------------------------------------------------
# 3. Check installation
# ----------------------------------------------------------------------
if not os.path.exists(INSTALL_DIR):
    print(f"r3dfox not found in:\n  {INSTALL_DIR}")
    print("Please install r3dfox first.")
    sys.exit(1)

if not os.path.exists(FIREFOX_EXE):
    print("r3dfox.exe missing. Corrupted install?")
    sys.exit(1)

# ----------------------------------------------------------------------
# 4. Get current version from application.ini (Win7-safe)
# ----------------------------------------------------------------------
def get_current_version():
    if not os.path.exists(APP_INI):
        return None
    try:
        with open(APP_INI, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        m = re.search(r'^\s*Version\s*=\s*([\d\.]+)', content, re.MULTILINE)
        return m.group(1) if m else None
    except:
        return None

current_version = get_current_version()
print(f"Current version: {current_version or 'Unknown'}")

# ----------------------------------------------------------------------
# 5. Fetch latest release
# ----------------------------------------------------------------------
print("Checking for updates...")
try:
    req = urllib.request.Request(LATEST_API, headers={'User-Agent': 'r3dfox-updater'})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    latest_tag = data['tag_name'].lstrip('v')
    print(f"Latest version: {latest_tag}")
except Exception as e:
    print(f"Failed to fetch release: {e}")
    sys.exit(1)

# Compare versions
if current_version and current_version >= latest_tag:
    print("You are up to date!")
    sys.exit(0)

# ----------------------------------------------------------------------
# 6. Find installer asset
# ----------------------------------------------------------------------
installer_url = None
installer_name = None
patterns = ASSET_PATTERNS[arch]

for asset in data.get('assets', []):
    name = asset['name']
    if any(p.lower() in name.lower() for p in patterns) and name.endswith('.exe'):
        installer_url = asset['browser_download_url']
        installer_name = name
        break

if not installer_url:
    print(f"Installer not found for {arch}.")
    print("Available files:")
    for a in data.get('assets', []):
        print(f"  - {a['name']}")
    sys.exit(1)

print(f"Found: {installer_name}")

# ----------------------------------------------------------------------
# 7. Download installer
# ----------------------------------------------------------------------
temp_dir = tempfile.mkdtemp(prefix='r3dfox_')
installer_path = os.path.join(temp_dir, installer_name)

print(f"Downloading to:\n  {installer_path}")
try:
    req = urllib.request.Request(installer_url, headers={'User-Agent': 'r3dfox-updater'})
    with urllib.request.urlopen(req) as src, open(installer_path, 'wb') as dst:
        shutil.copyfileobj(src, dst)
except Exception as e:
    print(f"Download failed: {e}")
    sys.exit(1)

# ----------------------------------------------------------------------
# 8. Run installer silently
# ----------------------------------------------------------------------
print("Installing silently...")
try:
    # NSIS installers use /S
    cmd = [installer_path, '/S']
    proc = subprocess.run(cmd, cwd=temp_dir, capture_output=True, text=True)
    if proc.returncode == 0:
        print(f"Updated to {latest_tag}!")
    else:
        print(f"Installer failed (code {proc.returncode})")
        print(proc.stdout)
        print(proc.stderr)
except Exception as e:
    print(f"Install error: {e}")
finally:
    # Cleanup
    try:
        shutil.rmtree(temp_dir)
    except:
        pass