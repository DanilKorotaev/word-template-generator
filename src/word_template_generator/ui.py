from __future__ import annotations

from pathlib import Path

from .generator import build_one, load_workspace


def run_ui() -> None:
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Tkinter is not available in this Python build. "
            "Use CLI commands (ws-build-all/ws-build-one) or install Python with Tk support."
        ) from exc

    root = tk.Tk()
    root.title("Word Template Generator")
    root.geometry("820x500")

    workspace_var = tk.StringVar()
    status_var = tk.StringVar(value="Select a document workspace folder.")
    acts_list: list[Path] = []

    def append_status(message: str) -> None:
        status_text.configure(state=tk.NORMAL)
        status_text.insert(tk.END, message + "\n")
        status_text.see(tk.END)
        status_text.configure(state=tk.DISABLED)
        status_var.set(message)
        root.update_idletasks()

    def refresh_acts() -> None:
        listbox.delete(0, tk.END)
        acts_list.clear()
        ws = workspace_var.get().strip()
        if not ws:
            return
        try:
            cfg, found = load_workspace(Path(ws))
        except Exception as exc:  # noqa: BLE001
            append_status(f"[ERR] {exc}")
            return
        acts_list.extend(found)
        for act in found:
            listbox.insert(tk.END, act.name)
        append_status(f"[OK] Workspace loaded. Acts: {len(found)}. Template: {cfg.template_name}")

    def choose_workspace() -> None:
        selected = filedialog.askdirectory(title="Select document workspace")
        if not selected:
            return
        workspace_var.set(selected)
        refresh_acts()

    def generate_all() -> None:
        ws = workspace_var.get().strip()
        if not ws:
            messagebox.showwarning("Word Template Generator", "Select workspace first.")
            return
        cfg, found = load_workspace(Path(ws))
        if not found:
            messagebox.showwarning("Word Template Generator", "No act markdown files found.")
            return
        append_status("[RUN] Generating all acts...")
        count = 0
        for act in found:
            result = build_one(
                project_data=cfg.project_data,
                act_file=act,
                templates_dir=cfg.templates_dir,
                output_dir=cfg.output_dir,
                strict=True,
            )
            count += 1
            append_status(f"[OK] {result.act_file.name} -> {result.output_file.name}")
        append_status(f"[OK] Done. Generated {count} file(s).")

    def generate_selected() -> None:
        ws = workspace_var.get().strip()
        if not ws:
            messagebox.showwarning("Word Template Generator", "Select workspace first.")
            return
        selected = listbox.curselection()
        if not selected:
            messagebox.showwarning("Word Template Generator", "Select one act in the list.")
            return
        act = acts_list[selected[0]]
        cfg, _ = load_workspace(Path(ws))
        result = build_one(
            project_data=cfg.project_data,
            act_file=act,
            templates_dir=cfg.templates_dir,
            output_dir=cfg.output_dir,
            strict=True,
        )
        append_status(f"[OK] Rebuilt: {result.act_file.name} -> {result.output_file.name}")

    top = tk.Frame(root)
    top.pack(fill=tk.X, padx=12, pady=10)

    tk.Label(top, text="Workspace:").pack(side=tk.LEFT)
    tk.Entry(top, textvariable=workspace_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
    tk.Button(top, text="Choose...", command=choose_workspace).pack(side=tk.LEFT)
    tk.Button(top, text="Refresh", command=refresh_acts).pack(side=tk.LEFT, padx=(8, 0))

    body = tk.Frame(root)
    body.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 10))

    left = tk.Frame(body)
    left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    tk.Label(left, text="Act files").pack(anchor="w")
    listbox = tk.Listbox(left)
    listbox.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

    right = tk.Frame(body, width=240)
    right.pack(side=tk.LEFT, fill=tk.Y, padx=(12, 0))
    tk.Button(right, text="Generate all", command=generate_all, height=2).pack(fill=tk.X)
    tk.Button(right, text="Generate selected", command=generate_selected, height=2).pack(fill=tk.X, pady=(8, 0))
    tk.Label(right, textvariable=status_var, wraplength=220, justify=tk.LEFT).pack(fill=tk.X, pady=(16, 0))

    bottom = tk.Frame(root)
    bottom.pack(fill=tk.BOTH, expand=False, padx=12, pady=(0, 12))
    tk.Label(bottom, text="Log").pack(anchor="w")
    status_text = tk.Text(bottom, height=8, state=tk.DISABLED)
    status_text.pack(fill=tk.BOTH, expand=True)

    root.mainloop()

