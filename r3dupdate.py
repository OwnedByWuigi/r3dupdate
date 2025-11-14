#!/usr/bin/env python3
"""
update_r3dfox_fullinstall.py
Updates a full r3dfox installation (C:\Program Files\Eclipse Community\r3dfox)
to the latest GitHub release by downloading and silently executing the installer .exe.
Uses only the Python standard library. Checks if current version is older than latest.
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
FIREFOX_EXE  = os.path.join(INSTALL_DIR, "firefox.exe")

LATEST_API   = "https://api.github.com/repos/Eclipse-Community/r3dfox/releases/latest"

# Installer asset patterns (.exe for full install)
ASSET_PATTERNS = {
    "win32": "r3dfox-win32-installer.exe",
    "win64": "r3dfox-win64-installer.exe",
    # Fallback if exact name not found; adjust based on actual naming
    # From GitHub, check if it's something like "r3dfox-setup-win64.exe" etc.
}

# ----------------------------------------------------------------------
# 1. Sanity checks – Windows only
# ----------------------------------------------------------------------
if platform.system() != "Windows":
    print("This script only runs on Windows.")
    sys.exit(1)

# Detect architecture
is_64bit = sys.maxsize > 2**32 or os.environ.get("PROCESSOR_ARCHITEW6432", "")
arch = "win64" if is_64bit else "win32"
print(f"Detected architecture: {arch}")

# Check if current installation exists
if not os.path.exists(INSTALL_DIR):
    print(f"No r3dfox installation found in '{INSTALL_DIR}'. Please install first.")
    sys.exit(1)

if not os.path.exists(FIREFOX_EXE):
    print(f"firefox.exe not found in '{INSTALL_DIR}'. Installation may be incomplete.")
    sys.exit(1)

# ----------------------------------------------------------------------
# 2. Get current version from application.ini
# ----------------------------------------------------------------------
def get_current_version():
    app_ini_path = os.path.join(INSTALL_DIR, "application.ini")
    if not os.path.exists(app_ini_path):
        print("application.ini not found. Cannot determine current version.")
        return None
    try:
        with open(app_ini_path, 'r', encoding='utf-8') as f:
            content = f.read()
        match = re.search(r'Version=(\d+(?:\.\d+)+)', content)
        if match:
            return match.group(1)
        else:
            print("Could not parse version from application.ini.")
            return None
    except Exception as e:
        print(f"Error reading application.ini: {e}")
        return None

current_version = get_current_version()
if current_version:
    print(f"Current version: {current_version}")
else:
    print("Warning: Could not detect current version. Proceeding anyway.")

# ----------------------------------------------------------------------
# 3. Fetch latest release info from GitHub API
# ----------------------------------------------------------------------
print("Fetching latest r3dfox release info...")
try:
    with urllib.request.urlopen(LATEST_API) as response:
        data = json.loads(response.read().decode())
    latest_tag = data['tag_name']
    print(f"Latest version: {latest_tag}")
except (URLError, HTTPError, json.JSONDecodeError, KeyError) as e:
    print(f"Error fetching release info: {e}")
    sys.exit(1)

# Compare versions (simple string compare works for semantic versioning like 144.0.2 > 140.5.0)
if current_version and latest_tag <= current_version:
    print(f"Current version {current_version} is up to date or newer than {latest_tag}. No update needed.")
    sys.exit(0)

# Find the installer asset
installer_url = None
installer_name = None
for asset in data['assets']:
    name = asset['name'].lower()
    pattern = ASSET_PATTERNS[arch].lower()
    if pattern in name and name.endswith('.exe'):
        installer_url = asset['browser_download_url']
        installer_name = asset['name']
        break

if not installer_url:
    print(f"No matching installer .exe found for {arch}.")
    print("Available assets:")
    for asset in data['assets']:
        print(f"  - {asset['name']}")
    sys.exit(1)

print(f"Found installer: {installer_name}")

# ----------------------------------------------------------------------
# 4. Download the installer to temp
# ----------------------------------------------------------------------
temp_dir = tempfile.gettempdir()
installer_path = os.path.join(temp_dir, installer_name)
print(f"Downloading installer to {installer_path}...")
try:
    with urllib.request.urlopen(installer_url) as response:
        with open(installer_path, 'wb') as f:
            shutil.copyfileobj(response, f)
    print("Download completed.")
except URLError as e:
    print(f"Download failed: {e}")
    sys.exit(1)

# ----------------------------------------------------------------------
# 5. Silently execute the installer
# ----------------------------------------------------------------------
print("Executing installer silently...")
try:
    # Assume /S for silent install (common for NSIS installers; adjust if different)
    # You may need to check the actual installer flags from release notes
    cmd = [installer_path, '/S']  # Silent install
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Installation completed successfully. Updated to {latest_tag}.")
    else:
        print(f"Installer returned code {result.returncode}. Output: {result.stdout} {result.stderr}")
        sys.exit(1)
except Exception as e:
    print(f"Error executing installer: {e}")
    sys.exit(1)
finally:
    # Cleanup
    if os.path.exists(installer_path):
        os.remove(installer_path)