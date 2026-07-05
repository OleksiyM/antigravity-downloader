# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests",
# ]
# ///

import os
import sys
import re
import urllib.parse
import platform
from pathlib import Path
import requests

# Base manifest config
MANIFEST_BASE_URLS = {
    "Antigravity 2 (App)": "https://antigravity-hub-auto-updater-974169037036.us-central1.run.app/manifest",
    "Antigravity IDE": "https://antigravity-ide-auto-updater-974169037036.us-central1.run.app",
}

DEFAULT_DOWNLOAD_DIR = Path.home() / "Downloads"

class Colors:
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

def detect_platform():
    # Detect OS
    os_name = platform.system().lower()
    if os_name == "darwin":
        os_key = "mac"
    elif os_name == "windows":
        os_key = "win"
    else:
        os_key = "linux"

    # Detect Architecture
    arch = platform.machine().lower()
    if arch in ["arm64", "aarch64"]:
        arch_key = "arm64"
    else:
        arch_key = "x64"

    return os_key, arch_key

def get_latest_downloads(os_key, arch_key):
    results = {}
    
    # 1. Fetch Antigravity 2 (App) manifest
    # Filename format: latest-{arch}-{os}.yml (e.g. latest-x64-linux.yml, latest-arm64-mac.yml)
    manifest_name = f"latest-{arch_key}-{os_key}.yml"
    manifest_url = f"{MANIFEST_BASE_URLS['Antigravity 2 (App)']}/{manifest_name}"
    
    try:
        r = requests.get(manifest_url, timeout=10)
        r.raise_for_status()
        text = r.text
        
        version_match = re.search(r"version:\s*(\d+\.\d+(?:\.\d+[a-zA-Z0-9\-]*)?)", text)
        version = version_match.group(1) if version_match else "unknown"
        
        # Extract files links from YAML
        urls = re.findall(r"url:\s*(https?://\S+)", text)
        
        if os_key == "mac":
            # Mac builds
            dmg_url = next((u for u in urls if ".dmg" in u), None)
            zip_url = next((u for u in urls if ".zip" in u), None)
            
            if dmg_url:
                results["Antigravity 2 (DMG)"] = {"version": version, "url": dmg_url}
            if zip_url:
                results["Antigravity 2 (ZIP)"] = {"version": version, "url": zip_url}
            if not dmg_url and not zip_url and urls:
                results["Antigravity 2"] = {"version": version, "url": urls[0]}
                
        elif os_key == "win":
            # Windows builds
            exe_url = next((u for u in urls if ".exe" in u), None)
            if exe_url:
                results["Antigravity 2 (EXE)"] = {"version": version, "url": exe_url}
            else:
                for idx, u in enumerate(urls, 1):
                    results[f"Antigravity 2 (Option {idx})"] = {"version": version, "url": u}
        else:
            # Linux builds
            appimage_url = next((u for u in urls if "AppImage" in u), None)
            deb_url = next((u for u in urls if ".deb" in u), None)
            
            if appimage_url:
                results["Antigravity 2 (AppImage)"] = {"version": version, "url": appimage_url}
                # Construct tar.gz package url based on AppImage's folder path
                # e.g. https://storage.googleapis.com/.../linux-x64/Antigravity.AppImage -> .../linux-x64/Antigravity.tar.gz
                base_dir_url = appimage_url.rsplit("/", 1)[0]
                tar_url = f"{base_dir_url}/Antigravity.tar.gz"
                results["Antigravity 2 (TAR.GZ)"] = {"version": version, "url": tar_url}
            if deb_url:
                results["Antigravity 2 (DEB)"] = {"version": version, "url": deb_url}
            if not appimage_url and not deb_url and urls:
                results["Antigravity 2"] = {"version": version, "url": urls[0]}
                
    except Exception as e:
        results[f"Antigravity 2 (App)"] = {"error": f"No build for {os_key}-{arch_key} ({str(e)})"}

    # 2. Fetch Antigravity IDE latest stable version details via API
    try:
        r = requests.get(MANIFEST_BASE_URLS["Antigravity IDE"], timeout=10)
        r.raise_for_status()
        text = r.text
        version_match = re.search(r"Stable Version:\s*(\d+\.\d+(?:\.\d+[a-zA-Z0-9\-]*)?)", text)
        version = version_match.group(1) if version_match else "unknown"
        
        # Build platform key for IDE update API
        if os_key == "mac":
            platform_key = "darwin" if arch_key == "x64" else "darwin-arm64"
        elif os_key == "win":
            platform_key = f"win32-{arch_key}-user"
        else:
            platform_key = f"linux-{arch_key}"
            
        api_url = f"{MANIFEST_BASE_URLS['Antigravity IDE']}/api/update/{platform_key}/stable/latest"
        r_api = requests.get(api_url, timeout=10)
        r_api.raise_for_status()
        data = r_api.json()
        
        ide_url = data.get("url")
        if not ide_url:
            raise ValueError(f"No download URL returned by API for platform: {platform_key}")
            
        # Determine extension for label
        ext_label = ""
        if ide_url:
            if ide_url.endswith(".dmg"):
                ext_label = " (DMG)"
            elif ide_url.endswith(".zip"):
                ext_label = " (ZIP)"
            elif ide_url.endswith(".exe"):
                ext_label = " (EXE)"
            elif ide_url.endswith(".tar.gz") or ide_url.endswith(".tgz"):
                ext_label = " (TAR.GZ)"
            elif "tar.gz" in ide_url.lower():
                ext_label = " (TAR.GZ)"
            elif ide_url.endswith(".deb"):
                ext_label = " (DEB)"
            elif ide_url.endswith(".AppImage"):
                ext_label = " (AppImage)"
                
        results[f"Antigravity IDE{ext_label}"] = {
            "version": version,
            "url": ide_url
        }
    except Exception as e:
        results["Antigravity IDE"] = {"error": str(e)}

    return results

def download_file(url: str, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    filename = urllib.parse.unquote(url.split("/")[-1])
    dest_path = dest_dir / filename
    
    print(f"\n⚙️  Downloading {Colors.BLUE}{filename}{Colors.RESET}...")
    
    with requests.get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        total_size = int(r.headers.get('content-length', 0))
        
        downloaded = 0
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        percent = int((downloaded / total_size) * 100)
                        bar = "#" * (percent // 5) + "-" * (20 - (percent // 5))
                        sys.stdout.write(f"\r[{bar}] {percent}% ({downloaded // 1024 // 1024}MB / {total_size // 1024 // 1024}MB)")
                        sys.stdout.flush()
        print()
    return dest_path

def main():
    print(f"{Colors.BOLD}🚀 Antigravity Universal Downloader{Colors.RESET}")
    
    # Platform detection
    cur_os, cur_arch = detect_platform()
    
    print(f"Detected Platform: {Colors.BLUE}{cur_os} ({cur_arch}){Colors.RESET}")
    print("Would you like to download for this platform or choose another?")
    print(" 1. Use detected platform")
    print(" 2. Choose different platform")
    
    plat_choice = input("\nEnter choice [1-2, default: 1]: ").strip()
    if plat_choice == "2":
        # Ask for custom platform
        print("\nSelect Operating System:")
        print(" 1. Linux")
        print(" 2. macOS")
        print(" 3. Windows")
        os_choice = input("Enter choice [1-3]: ").strip()
        if os_choice == "2":
            cur_os = "mac"
        elif os_choice == "3":
            cur_os = "win"
        else:
            cur_os = "linux"
            
        print("\nSelect Architecture:")
        print(" 1. x86_64 (Intel/AMD)")
        print(" 2. ARM64")
        arch_choice = input("Enter choice [1-2]: ").strip()
        if arch_choice == "2":
            cur_arch = "arm64"
        else:
            cur_arch = "x64"
            
    print(f"\nFetching manifests for {Colors.YELLOW}{cur_os}-{cur_arch}{Colors.RESET}...")
    downloads = get_latest_downloads(cur_os, cur_arch)
    
    options = []
    print(f"\n{Colors.BOLD}Select application to download:{Colors.RESET}")
    for idx, (app_name, info) in enumerate(downloads.items(), 1):
        if "error" in info:
            print(f" {idx}. {app_name:<35} | {Colors.RED}Not available ({info['error']}){Colors.RESET}")
        else:
            print(f" {idx}. {Colors.GREEN}{app_name:<35}{Colors.RESET} | Version: {Colors.YELLOW}{info['version']}{Colors.RESET}")
            options.append((app_name, info["url"]))
            
    if not options:
        print(f"\n{Colors.RED}No active download options found. Please check internet connection.{Colors.RESET}")
        sys.exit(1)
        
    try:
        choice = input(f"\nEnter choice [1-{len(options)}]: ").strip()
        choice_idx = int(choice) - 1
        if choice_idx < 0 or choice_idx >= len(options):
            raise ValueError()
    except (ValueError, IndexError):
        print(f"{Colors.RED}Invalid choice.{Colors.RESET}")
        sys.exit(1)
        
    app_name, url = options[choice_idx]
    
    try:
        dest_path = download_file(url, DEFAULT_DOWNLOAD_DIR)
        print(f"✅ {Colors.GREEN}Successfully downloaded to:{Colors.RESET} {dest_path}")
        
        # Make executable if applicable
        if (dest_path.name.endswith(".AppImage") or dest_path.name == "agy") and platform.system().lower() != "windows":
            os.chmod(dest_path, 0o755)
            print(f"🔧 Marked as executable.")
    except Exception as e:
        print(f"❌ {Colors.RED}Download failed: {e}{Colors.RESET}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}🛑 Download cancelled by user (Ctrl+C). Exiting...{Colors.RESET}")
        sys.exit(130)
