#!/usr/bin/env python3
"""Bundle Blender and BlenderDMX addon for Lightman."""
import os, re, shutil, subprocess, sys
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BLENDER_RESOURCES_DIR = PROJECT_ROOT / "src/director/resources"
BLENDER_APP_DEST = BLENDER_RESOURCES_DIR / "Blender.app"


def get_latest_blender_version():
    download_url = "https://download.blender.org/release/"
    try:
        req = Request(download_url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8")
    except (URLError, HTTPError) as e:
        print(f"Error fetching Blender download page: {e}")
        return None
    version_pattern = r'/release/([\d]+\.[\d]+\.[\d]+)/'
    matches = re.findall(version_pattern, html)
    if not matches:
        print("Could not parse Blender version from download page.")
        return None
    from packaging import version
    try:
        versions = sorted(matches, key=version.parse, reverse=True)
        latest = versions[0]
        print(f"Latest Blender version detected: {latest}")
        return latest
    except Exception:
        latest = matches[-1]
        print(f"Latest Blender version detected (fallback): {latest}")
        return latest


def download_blender_dmg(version):
    dmg_filename = f"blender-{version}-macos.universal2.dmg"
    dmg_url = f"https://download.blender.org/release/{version}/{dmg_filename}"
    dmg_path = Path(f"/tmp/{dmg_filename}")
    print(f"Downloading Blender DMG from: {dmg_url}")
    try:
        req = Request(dmg_url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=120) as response, open(dmg_path, "wb") as out_file:
            shutil.copyfileobj(response, out_file)
        print(f"Downloaded to {dmg_path}")
        return dmg_path
    except (URLError, HTTPError) as e:
        print(f"Error downloading Blender DMG: {e}")
        return None


def mount_and_copy_blender(dmg_path, version):
    mount_point = subprocess.run(
        ["hdiutil", "attach", str(dmg_path), "-nobrowse", "-quiet"],
        capture_output=True,
        text=True,
    )
    output = mount_point.stdout
    print(f"hdiutil attach output: {output}")

    blender_app_mounted = None
    for line in output.splitlines():
        if "/Volumes/Blender" in line:
            blender_app_mounted = line.split(" ", 1)[-1].strip()
            break

    if not blender_app_mounted:
        blender_app_mounted = subprocess.run(
            ["find", "/Volumes", "-name", "Blender.app", "-maxdepth", "4"],
            capture_output=True, text=True, timeout=30
        ).stdout.strip()

    if not blender_app_mounted:
        print("Blender.app not found on mounted volume.")
        subprocess.run(["hdiutil", "detach", blender_app_mounted], capture_output=True)
        return None

    print(f"Found Blender.app at: {blender_app_mounted}")

    BLENDER_RESOURCES_DIR.mkdir(parents=True, exist_ok=True)
    dest_app = BLENDER_APP_DEST
    if dest_app.exists():
        print("Removing existing Blender.app...")
        shutil.rmtree(dest_app)

    print(f"Copying Blender.app to {dest_app} ...")
    shutil.copytree(blender_app_mounted, dest_app)
    print("Blender.app copied successfully.")

    print("Unmounting dmg...")
    subprocess.run(["hdiutil", "detach", blender_app_mounted], capture_output=True, timeout=10)

    return str(dest_app)


def clone_blender_dmx(blender_app_path, version):
    addon_dest_dir = Path(blender_app_path) / "Contents" / "Resources" / version / "scripts" / "addons"
    addon_dest_dir.mkdir(parents=True, exist_ok=True)

    clone_dir = Path("/tmp/blender-dmx")
    if clone_dir.exists():
        print("blender-dmx already cloned, pulling latest...")
        subprocess.run(["git", "pull"], cwd=str(clone_dir), capture_output=True, timeout=30)
    else:
        print("Cloning blender-dmx...")
        subprocess.run(
            ["git", "clone", "--depth", "1", "https://github.com/open-stage/blender-dmx.git",
             str(clone_dir)],
            capture_output=True, timeout=120
        )

    source_addon = clone_dir / "blenderdmx"
    if not source_addon.exists():
        print(f"Error: blenderdmx source folder not found at {source_addon}")
        return False

    dest_addon = addon_dest_dir / "blenderdmx"
    if dest_addon.exists():
        print("Removing existing blenderdmx addon...")
        shutil.rmtree(dest_addon)

    print(f"Copying blenderdmx to {dest_addon} ...")
    shutil.copytree(source_addon, dest_addon)
    print("blenderdmx addon copied successfully.")

    # ── NEW: Copy fixture catalog into BlenderDMX addon ─────────────────────
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    fixtures_catalog = PROJECT_ROOT / "data" / "fixtures_catalog.json"
    dest_fixture_dir = dest_addon / "fixtures"
    dest_fixture_dir.mkdir(parents=True, exist_ok=True)

    if fixtures_catalog.exists():
        print(f"Copying fixture catalog from {fixtures_catalog} ...")
        # Copy all .gdtf and .json fixture files
        import glob
        patterns = ["*.gdtf", "*.json"]
        for pattern in patterns:
            for f in glob.glob(str(fixtures_catalog.parent / pattern if fixtures_catalog.parent else pattern)):
                shutil.copy2(f, str(dest_fixture_dir / Path(f).name))
        print(f"Fixture catalog copied to {dest_fixture_dir}")
    else:
        print(f"Warning: {fixtures_catalog} not found — skipping fixture copy.")

    return True


def write_version_file(blender_app_path, version):
    version_file = Path(blender_app_path) / "Contents" / "Resources" / "blender_version.txt"
    with open(version_file, "w") as f:
        f.write(version)
    print(f"Written version file: {version_file} (content: {version})")


def main():
    print("=== Bundling Blender and BlenderDMX ===\n")

    version = get_latest_blender_version()
    if not version:
        print("Failed to determine Blender version. Aborting.")
        sys.exit(1)

    dmg_path = download_blender_dmg(version)
    if not dmg_path:
        print("Failed to download Blender DMG. Aborting.")
        sys.exit(1)

    blender_app_path = mount_and_copy_blender(dmg_path, version)
    if not blender_app_path:
        print("Failed to copy Blender.app. Aborting.")
        sys.exit(1)

    success = clone_blender_dmx(blender_app_path, version)
    if not success:
        print("Warning: blender-dmx addon could not be cloned, but Blender is bundled.")

    write_version_file(blender_app_path, version)

    if dmg_path.exists():
        dmg_path.unlink()
        print(f"Cleaned up DMG: {dmg_path}")

    print("\n=== Bundling complete! ===")
    print(f"Blender.app is at: {BLENDER_APP_DEST}")
    print(f"BlenderDMX addon should be at: {BLENDER_APP_DEST}/Contents/Resources/{version}/scripts/addons/blenderdmx")


if __name__ == "__main__":
    main()