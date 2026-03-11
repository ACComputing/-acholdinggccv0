import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os


class GCCFrontend(tk.Tk):
    """
    Tiny Tkinter wrapper around gcc/clang.
    - Select a C file
    - Compile with a pre‑baked command
    - Run the resulting binary
    """

    def __init__(self):
        super().__init__()
        self.title("AC Compiler HDR v0 - GCC Frontend")
        self.configure(bg="#111111")

        self.c_file = None
        # per‑platform outputs
        self.outputs = {}

        self._build_ui()

    def _build_ui(self):
        frame = tk.Frame(self, bg="#111111")
        frame.pack(padx=12, pady=12, fill="both", expand=True)

        title = tk.Label(
            frame,
            text="AC Compiler HDR v0\n(pre‑baked gcc frontend)",
            fg="#00ff99",
            bg="#111111",
            font=("Consolas", 12, "bold"),
            justify="left",
        )
        title.pack(anchor="w", pady=(0, 10))

        # File path label
        self.file_label = tk.Label(
            frame,
            text="No C file selected",
            fg="#cccccc",
            bg="#111111",
            font=("Consolas", 10),
            anchor="w",
        )
        self.file_label.pack(fill="x", pady=(0, 8))

        # Buttons row (all black text as requested)
        btn_row = tk.Frame(frame, bg="#111111")
        btn_row.pack(fill="x", pady=(0, 8))

        self.btn_select = tk.Button(
            btn_row,
            text="Select C File",
            command=self.select_file,
            bg="#00ff99",
            fg="black",  # black text
            activebackground="#00cc77",
            activeforeground="black",
            relief="flat",
            padx=10,
            pady=6,
        )
        self.btn_select.pack(side="left", padx=(0, 6))

        self.btn_compile = tk.Button(
            btn_row,
            text="Compile (gcc)",
            command=self.compile_file,
            bg="#ffaa00",
            fg="black",  # black text
            activebackground="#dd8800",
            activeforeground="black",
            relief="flat",
            padx=10,
            pady=6,
            state="disabled",
        )
        self.btn_compile.pack(side="left", padx=(0, 6))

        self.btn_run = tk.Button(
            btn_row,
            text="Run Binary",
            command=self.run_binary,
            bg="#66aaff",
            fg="black",  # black text
            activebackground="#4477dd",
            activeforeground="black",
            relief="flat",
            padx=10,
            pady=6,
            state="disabled",
        )
        self.btn_run.pack(side="left")

        # Output console
        self.output = tk.Text(
            frame,
            bg="#000000",
            fg="#00ff00",
            insertbackground="#00ff00",
            height=16,
            font=("Consolas", 10),
        )
        self.output.pack(fill="both", expand=True, pady=(8, 0))

    def log(self, text: str):
        self.output.insert("end", text + "\n")
        self.output.see("end")

    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Select C source file",
            filetypes=[("C source", "*.c"), ("All files", "*.*")],
        )
        if not file_path:
            return

        self.c_file = file_path
        base, _ = os.path.splitext(os.path.basename(file_path))
        dirname = os.path.dirname(file_path)

        # Pre‑baked multi‑platform output names (same source, different filenames)
        self.outputs = {
            "mac": os.path.join(dirname, f"{base}_mac"),
            "windows": os.path.join(dirname, f"{base}_win.exe"),
            "bsd": os.path.join(dirname, f"{base}_bsd"),
            "unix": os.path.join(dirname, f"{base}_unix"),
        }

        self.file_label.config(text=f"C file: {self.c_file} ➜ mac / win / bsd / unix")
        self.btn_compile.config(state="normal")
        self.btn_run.config(state="disabled")
        self.log(f"[info] Selected C file: {self.c_file}")

    def compile_file(self):
        if not self.c_file:
            messagebox.showwarning("No file", "Select a C file first.")
            return

        if not self.outputs:
            messagebox.showwarning("No outputs", "Internal error: missing output names.")
            return

        # Try to build 4 binaries from the same source.
        # NOTE: On most systems this still builds native binaries; the
        # different filenames are mainly for packaging targets.
        results = {}
        for target, out_path in self.outputs.items():
            # You can tweak per‑target flags here if desired.
            cmd = ["gcc", "-std=c11", "-O2", "-Wall", self.c_file, "-o", out_path]
            self.log(f"[info] ({target}) Running: {' '.join(cmd)}")
            try:
                proc = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
            except FileNotFoundError:
                self.log("[error] gcc not found on PATH.")
                messagebox.showerror("gcc missing", "gcc executable not found on PATH.")
                return

            if proc.stdout.strip():
                self.log(proc.stdout.strip())
            results[target] = proc.returncode
            if proc.returncode == 0:
                self.log(f"[ok] ({target}) compilation succeeded → {out_path}")
            else:
                self.log(f"[fail] ({target}) gcc exited with code {proc.returncode}.")

        # Enable Run if at least one non‑Windows (mac/unix/bsd) build worked;
        # we will run the unix variant by default if it exists.
        if any(results.get(t) == 0 for t in ("unix", "mac", "bsd", "windows")):
            self.btn_run.config(state="normal")
        else:
            self.btn_run.config(state="disabled")

    def run_binary(self):
        if not self.outputs:
            messagebox.showwarning("No binary", "Compile first.")
            return

        # Prefer running the unix build, then mac, then bsd, then windows.
        for key in ("unix", "mac", "bsd", "windows"):
            candidate = self.outputs.get(key)
            if candidate and os.path.exists(candidate):
                exe_path = candidate
                break
        else:
            messagebox.showwarning("No binary", "No compiled binary found. Compile first.")
            return

        self.log(f"[info] Running: {exe_path}")
        try:
            proc = subprocess.Popen(
                [exe_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
        except Exception as e:
            self.log(f"[error] Failed to run: {e}")
            return

        out, _ = proc.communicate()
        self.log(out.strip())
        self.log(f"[info] Process exited with code {proc.returncode}")


def main():
    app = GCCFrontend()
    app.mainloop()


if __name__ == "__main__":
    main()

