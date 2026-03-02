from __future__ import annotations

import subprocess
import sys


def pick_workspace_native() -> str | None:
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        selected = filedialog.askdirectory(title="Выберите папку workspace проекта")
        root.destroy()
        if selected:
            return selected
    except Exception:  # noqa: BLE001
        pass

    if sys.platform == "darwin":
        script = 'POSIX path of (choose folder with prompt "Выберите папку workspace проекта")'
        proc = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            selected = proc.stdout.strip()
            return selected or None
        return None

    if sys.platform.startswith("win"):
        powershell_script = (
            "Add-Type -AssemblyName System.Windows.Forms; "
            "$d=New-Object System.Windows.Forms.FolderBrowserDialog; "
            "$d.Description='Выберите папку workspace проекта'; "
            "$r=$d.ShowDialog(); "
            "if ($r -eq [System.Windows.Forms.DialogResult]::OK) { Write-Output $d.SelectedPath }"
        )
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", powershell_script],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            selected = proc.stdout.strip()
            return selected or None
        return None

    return None

