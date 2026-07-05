# Antigravity Downloader 🚀

A universal Python utility designed to automatically retrieve, download, and configure the latest versions of the Google Antigravity ecosystem applications. 

## Features

- **Platform Auto-Detection:** Automatically identifies your Operating System (Linux, macOS, Windows) and architecture (x64, ARM64) to fetch the correct build.
- **Cross-Platform Downloads:** Ability to bypass auto-detection and manually select target platform details (e.g. downloading macOS DMG files from Linux).
- **Auto-Executable:** Automatically grants executable permissions (`chmod +x`) to Linux AppImage files and CLI binaries upon download.
- **Progressive Download Monitor:** Elegant console status bar displaying download speeds, sizes, and progression.
- **No Manual Tracking:** Directly polls the official Google Antigravity update distribution server manifests, ensuring you always get the latest stable releases.

## Supported Software

1. **Antigravity 2 (App)**
   - Linux: AppImage, Debian Package (`.deb`)
   - macOS: DMG Installer, ZIP archive
   - Windows: Setup Executive (`.exe`)
2. **Antigravity IDE**
   - Linux: `tar.gz` archive
   - macOS: Universal DMG Installer
   - Windows: Setup Executive (`.exe`)
3. **Antigravity CLI (`agy`)**
   - Pre-compiled binaries for Linux, macOS, and Windows

## Installation & Running

Make sure you have [`uv`](https://docs.astral.sh/uv/) installed.

Clone the repository and run using the sandboxed script environment:

```bash
git clone https://github.com/OleksiyM/antigravity-downloader.git
cd antigravity-downloader
uv run download.py
```

## How It Works

The downloader queries stable updates endpoints:
- **App Updates:** Retrieves dynamic release assets configuration directly from the cloud-updater manifest API.
- **IDE & CLI Updates:** Scrapes the rollout versions and builds paths targeting public Google Cloud Storage (`storage.googleapis.com`) buckets.

## License

MIT License.
