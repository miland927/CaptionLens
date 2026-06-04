from __future__ import annotations

from pathlib import Path
import shutil
import struct
import subprocess
import sys
import zipfile


APP_VERSION = "0.2.0"
MARKER = b"TCT_PAYLOAD_V1"


def run(command: list[str], cwd: Path) -> None:
    print(" ".join(command))
    result = subprocess.run(command, cwd=cwd)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def zip_app(app_dir: Path, payload_path: Path) -> None:
    if payload_path.exists():
        payload_path.unlink()
    with zipfile.ZipFile(payload_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for file_path in app_dir.rglob("*"):
            if file_path.is_file():
                archive.write(file_path, file_path.relative_to(app_dir))


def append_payload(stub_exe: Path, payload_zip: Path, output_exe: Path) -> None:
    output_exe.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(stub_exe, output_exe)
    payload = payload_zip.read_bytes()
    with output_exe.open("ab") as handle:
        handle.write(payload)
        handle.write(MARKER)
        handle.write(struct.pack("<Q", len(payload)))


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    python = root / ".venv" / "Scripts" / "python.exe"
    if not python.exists():
        raise SystemExit("Missing .venv. Run scripts\\run.bat first.")

    app_dir = root / "dist" / "TeamsCaptionTranslator"
    installer_build = root / "build" / "installer_stub"
    installer_work = root / "build" / "installer_work"
    installer_dir = root / "installer"
    stub_exe = installer_build / "TeamsCaptionTranslatorSetupStub.exe"
    payload_zip = installer_work / "payload.zip"
    output_exe = installer_dir / f"TeamsCaptionTranslatorSetup-{APP_VERSION}.exe"

    run(
        [
            str(python),
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--onefile",
            "--windowed",
            "--name",
            "TeamsCaptionTranslatorSetupStub",
            "--distpath",
            str(installer_build),
            "--workpath",
            str(root / "build" / "installer_stub_work"),
            str(root / "scripts" / "installer_stub.py"),
        ],
        cwd=root,
    )

    if not app_dir.exists():
        raise SystemExit("Missing frozen app. Run scripts\\build_installer.ps1 -SkipInno first.")

    installer_work.mkdir(parents=True, exist_ok=True)
    zip_app(app_dir, payload_zip)
    append_payload(stub_exe, payload_zip, output_exe)
    print(f"Installer created: {output_exe}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
