#!/usr/bin/env python3
"""
Project Dump Tool - A utility for creating comprehensive project dumps for analysis.

This tool provides both GUI and CLI interfaces to generate a consolidated text dump
of a software project's structure and file contents. It's designed to create suitable
input for AI code analysis and can exclude files based on patterns and directory names.

Features:
- Directory traversal with customizable exclusion patterns
- Support for .gitignore patterns
- Drag-and-drop support in GUI mode
- Custom prompt configuration
- CLI operation for automation/scripting
- Binary file detection and exclusion

Usage:
    GUI mode: python project_dump.py
    CLI mode: python project_dump.py /path/to/project --cli --output output.txt
"""

import argparse
import fnmatch
import json
import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from typing import List, Optional, Set

# Constants
EXCLUDE_DIRS: Set[str] = {"node_modules", ".git", "__pycache__"}
EXCLUDE_FILE_PATTERNS: Set[str] = {"*.log", "*.tmp", "*.pyc", ".gitignore"}
DEFAULT_PROMPT: str = """
You are an expert in analyzing software project structures and file contents. 
Based on the following code, please answer the question or perform the task as instructed.

# instruction


# code
"""
PROMPT_FILE = "custom_prompt.json"
BINARY_CHECK_BYTES = 1024

# TkDnD Availability
TKDND_AVAILABLE: bool = False
DND_FILES: str = "dummy"  # Default value if TkDnD is not available

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD

    TKDND_AVAILABLE = True
except ImportError:
    print("TkinterDnD2 is not installed. Installing it with pip...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "tkinterdnd2"])
        from tkinterdnd2 import DND_FILES, TkinterDnD

        print("TkinterDnD2 has been installed successfully.")
        TKDND_AVAILABLE = True
    except Exception as e:
        print(f"Error installing TkinterDnD2: {e}")
        print("Please install it manually using: pip install tkinterdnd2")
        print("Drag and drop functionality will be disabled.")

        class TkinterDnD:
            @staticmethod
            def Tk() -> tk.Tk:
                """Create a basic Tk window when TkinterDnD is not available."""
                return tk.Tk()


class ProjectDumper:
    """
    Core logic for processing a project directory and generating a dump.
    """

    def __init__(
        self,
        exclude_dirs: Optional[Set[str]] = None,
        exclude_file_patterns: Optional[Set[str]] = None,
    ):
        """
        Initialize the ProjectDumper with exclusion rules.
        """
        self.exclude_dirs = exclude_dirs if exclude_dirs is not None else EXCLUDE_DIRS
        self.exclude_file_patterns = (
            exclude_file_patterns
            if exclude_file_patterns is not None
            else EXCLUDE_FILE_PATTERNS
        )

    def process_project(self, src: Path, prompt: str) -> str:
        """
        Process project directory into a single text output.
        """
        gitignore_patterns = self._load_gitignore(src)
        tree_lines = [src.name]
        tree_lines += self._generate_tree_lines(
            src, gitignore_patterns=gitignore_patterns
        )
        files = self._collect_files(src, gitignore_patterns)

        result = [prompt.strip(), "", "## Project Structure", "\n".join(tree_lines), ""]

        for path in files:
            relative_path = str(path.relative_to(src)).replace("\\", "/")

            file_size_mb = path.stat().st_size / (1024 * 1024)
            if file_size_mb > 5:  # skip >5MB
                print(f"Skipping large file: {relative_path} ({file_size_mb:.2f} MB)")
                result.append(f"# [Skipped large file] File: {relative_path}")
                continue

            if self._is_binary(path):
                continue

            result.append(f"# ===== File: {relative_path} =====")
            try:
                result.append(path.read_text(encoding="utf-8"))
            except Exception as e:
                result.append(f"# [Error reading file: {e}]")
        return "\n\n".join(result)

    def _load_gitignore(self, src: Path) -> Set[str]:
        """
        Load .gitignore patterns from the project root.
        """
        patterns = set()
        gitignore = src / ".gitignore"
        if gitignore.is_file():
            for line in gitignore.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.add(line)
        return patterns

    def _should_exclude(self, name: str, gitignore_patterns: Set[str]) -> bool:
        """
        Check whether a file or directory should be excluded based on patterns.
        """
        patterns = self.exclude_file_patterns.union(gitignore_patterns)
        return (
            any(fnmatch.fnmatch(name, pat) for pat in patterns)
            or name in self.exclude_dirs
        )

    def _generate_tree_lines(
        self, dir_path: Path, prefix: str = "", gitignore_patterns: Set[str] = set()
    ) -> List[str]:
        """
        Generate tree structure lines of the project.
        """
        lines: List[str] = []
        entries = sorted(
            [
                p
                for p in dir_path.iterdir()
                if not self._should_exclude(p.name, gitignore_patterns)
            ],
            key=lambda p: (not p.is_dir(), p.name.lower()),
        )
        pointers = ["├── "] * (len(entries) - 1) + ["└── "] if entries else []
        for pointer, path in zip(pointers, entries):
            lines.append(f"{prefix}{pointer}{path.name}")
            if path.is_dir():
                extension = "│   " if pointer == "├── " else "    "
                lines += self._generate_tree_lines(
                    path, prefix + extension, gitignore_patterns
                )
        return lines

    def _collect_files(
        self, dir_path: Path, gitignore_patterns: Set[str]
    ) -> List[Path]:
        """
        Collect all file paths to be included in the output.
        """
        files: List[Path] = []
        for root, dirs, filenames in os.walk(dir_path):
            root_path = Path(root)
            dirs[:] = [
                d for d in dirs if not self._should_exclude(d, gitignore_patterns)
            ]
            for fname in filenames:
                if not self._should_exclude(fname, gitignore_patterns):
                    files.append(root_path / fname)
        return files

    # def _is_binary(self, path: Path) -> bool:
    #     """
    #     Detect if a file is binary.
    #     """
    #     try:
    #         with path.open("rb") as f:
    #             chunk = f.read(BINARY_CHECK_BYTES)
    #         return b"\0" in chunk
    #     except Exception:
    # return True  # Consider it binary if there's an error reading it

    def _is_binary(self, path: Path, check_bytes: int = 4096) -> bool:
        """
        Detect if a file is binary using more robust heuristics.
        """
        try:
            with path.open("rb") as f:
                chunk = f.read(check_bytes)
        except Exception:
            return True  # Consider it binary if there's an error reading it

        if b"\0" in chunk:
            return True  # Null byte found, likely binary

        # Check for a high frequency of non-printable characters (excluding common ones)
        non_printable_threshold = 0.1  # If > 10% are non-printable, consider binary
        non_printable_count = 0
        printable_ascii = set(range(32, 127))  # Space to tilde
        common_control = {9, 10, 13}  # Tab, Line Feed, Carriage Return

        for byte in chunk:
            if byte not in printable_ascii and byte not in common_control:
                non_printable_count += 1

        if chunk and non_printable_count / len(chunk) > non_printable_threshold:
            return True

        # Check for unusual byte patterns (e.g., high byte values in text files)
        high_byte_threshold = 0.8  # If > 80% have the high bit set, might be binary
        high_byte_count = 0
        for byte in chunk:
            if byte > 127:
                high_byte_count += 1

        if chunk and high_byte_count / len(chunk) > high_byte_threshold:
            return True

        # If none of the binary indicators are strong, assume it's text
        return False


class PromptManager:
    """
    Manages loading and saving the custom prompt.
    """

    def load_custom_prompt(self) -> Optional[str]:
        """
        Load the custom prompt from a file, if it exists.
        """
        if Path(PROMPT_FILE).exists():
            try:
                with open(PROMPT_FILE, "r", encoding="utf-8") as f:
                    return json.load(f).get("custom_prompt")
            except Exception as e:
                print(f"Error loading custom prompt: {e}")
        return None

    def save_custom_prompt(self, prompt: str) -> None:
        """
        Save the custom prompt to a file.
        """
        try:
            with open(PROMPT_FILE, "w", encoding="utf-8") as f:
                json.dump({"custom_prompt": prompt}, f)
        except Exception as e:
            print(f"Error saving custom prompt: {e}")


class App(TkinterDnD.Tk):
    """
    Main GUI Application for project dump tool.
    """

    def __init__(self) -> None:
        """Initialize the application and set up the UI."""
        super().__init__()
        self.title("Project Dump Tool")
        self.geometry("900x700")

        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")  # Use a modern looking theme
        except tk.TclError:
            pass

        self.style.configure("TButton", font=("Helvetica", 10))
        self.style.configure("TLabel", font=("Helvetica", 11))
        self.style.configure("Header.TLabel", font=("Helvetica", 12, "bold"))

        self.prompt_manager = PromptManager()
        self.custom_prompt = self.prompt_manager.load_custom_prompt() or DEFAULT_PROMPT
        self.project_dumper = ProjectDumper()

        self.status_var = tk.StringVar(value="Ready")
        self.generated_output = ""
        self.folder_path_var = tk.StringVar()
        self.excluded_dirs_var = tk.StringVar(value=", ".join(EXCLUDE_DIRS))
        self.excluded_patterns_var = tk.StringVar(
            value=", ".join(EXCLUDE_FILE_PATTERNS)
        )

        self.setup_ui()

    def setup_ui(self) -> None:
        """
        Set up the main user interface with improved layout.
        """
        main_container = ttk.Frame(self, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)

        action_frame = ttk.Frame(main_container)
        action_frame.pack(fill=tk.X, pady=(0, 10))

        project_frame = ttk.LabelFrame(action_frame, text="Project", padding="5")
        project_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        folder_entry = ttk.Entry(
            project_frame, textvariable=self.folder_path_var, width=40
        )
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        if TKDND_AVAILABLE:
            folder_entry.drop_target_register(DND_FILES)
            folder_entry.dnd_bind("<<Drop>>", self._on_drop_folder)

        btn_select = ttk.Button(
            project_frame, text="Browse...", command=self._select_folder
        )
        btn_select.pack(side=tk.LEFT)

        dnd_hint = ttk.Label(
            project_frame,
            text="✓ Drag & Drop Enabled",
            foreground="green" if TKDND_AVAILABLE else "gray",
        )
        dnd_hint.pack(side=tk.LEFT, padx=(5, 0))

        buttons_frame = ttk.Frame(action_frame)
        buttons_frame.pack(side=tk.RIGHT, padx=(10, 0))

        btn_copy = ttk.Button(
            buttons_frame, text="Copy to Clipboard", command=self._copy_to_clipboard
        )
        btn_copy.pack(side=tk.LEFT, padx=(0, 5))

        btn_save = ttk.Button(
            buttons_frame, text="Save to File", command=self._save_to_file
        )
        btn_save.pack(side=tk.LEFT)

        notebook = ttk.Notebook(main_container)
        notebook.pack(fill=tk.BOTH, expand=True)

        output_frame = ttk.Frame(notebook, padding="5")
        notebook.add(output_frame, text="Output")

        drop_frame = ttk.Frame(output_frame, padding="2")
        drop_frame.pack(fill=tk.BOTH, expand=True)
        if TKDND_AVAILABLE:
            drop_frame.drop_target_register(DND_FILES)
            drop_frame.dnd_bind("<<Drop>>", self._on_drop_folder)
            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<Drop>>", self._on_drop_folder)

        output_label = ttk.Label(
            drop_frame,
            text="Generated Project Dump: (Drag & Drop folder here)",
            style="Header.TLabel",
        )
        output_label.pack(anchor=tk.W, pady=(0, 5))
        if TKDND_AVAILABLE:
            output_label.drop_target_register(DND_FILES)
            output_label.dnd_bind("<<Drop>>", self._on_drop_folder)

        self.text_area = ScrolledText(drop_frame, wrap=tk.WORD, font=("Consolas", 10))
        self.text_area.pack(expand=True, fill=tk.BOTH)
        if TKDND_AVAILABLE:
            self.text_area.drop_target_register(DND_FILES)
            self.text_area.dnd_bind("<<Drop>>", self._on_drop_folder)

        prompt_frame = ttk.Frame(notebook, padding="5")
        notebook.add(prompt_frame, text="Custom Prompt")

        prompt_label = ttk.Label(
            prompt_frame, text="Enter your custom AI prompt:", style="Header.TLabel"
        )
        prompt_label.pack(anchor=tk.W, pady=(0, 5))

        self.custom_prompt_text = ScrolledText(
            prompt_frame, height=10, font=("Consolas", 10)
        )
        self.custom_prompt_text.insert(tk.END, self.custom_prompt)
        self.custom_prompt_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        prompt_buttons_frame = ttk.Frame(prompt_frame)
        prompt_buttons_frame.pack(fill=tk.X)

        btn_save_custom = ttk.Button(
            prompt_buttons_frame,
            text="Save Custom Prompt",
            command=self._save_custom_prompt,
        )
        btn_save_custom.pack(side=tk.LEFT, padx=(0, 5))

        btn_reset = ttk.Button(
            prompt_buttons_frame,
            text="Reset to Default",
            command=self._reset_to_default,
        )
        btn_reset.pack(side=tk.LEFT)

        settings_frame = ttk.Frame(notebook, padding="5")
        notebook.add(settings_frame, text="Settings")

        exclusion_label = ttk.Label(
            settings_frame, text="File Exclusion Settings:", style="Header.TLabel"
        )
        exclusion_label.pack(anchor=tk.W, pady=(0, 5))

        dir_frame = ttk.Frame(settings_frame)
        dir_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(dir_frame, text="Excluded Directories:").pack(side=tk.LEFT)
        excluded_dirs_entry = ttk.Entry(
            dir_frame, textvariable=self.excluded_dirs_var, width=40
        )
        excluded_dirs_entry.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)

        patterns_frame = ttk.Frame(settings_frame)
        patterns_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(patterns_frame, text="Excluded File Patterns:").pack(side=tk.LEFT)
        excluded_patterns_entry = ttk.Entry(
            patterns_frame, textvariable=self.excluded_patterns_var, width=40
        )
        excluded_patterns_entry.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)

        ttk.Button(
            settings_frame, text="Apply Settings", command=self._apply_settings
        ).pack(anchor=tk.W)

        status_bar = ttk.Label(
            self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _select_folder(self) -> None:
        """
        Open folder picker dialog and process the selected project.
        """
        folder = filedialog.askdirectory(title="Select a Project Folder")
        if folder:
            self.folder_path_var.set(folder)
            self._load_project(Path(folder))

    def _on_drop_folder(self, event) -> None:
        """
        Handle drop events for drag-and-drop functionality.
        """
        folder_path = event.data.strip("{}").strip('"')
        self.status_var.set(f"Folder dropped: {folder_path}")
        src = Path(folder_path)
        if not src.is_dir():
            self.status_var.set("Dropped item is not a directory")

            messagebox.showerror("Error", "Please drop a folder")
            return
        self.folder_path_var.set(str(src))
        self._load_project(src)

    def _load_project(self, path: Path) -> None:
        """
        Process and display the selected project.
        """
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert(
            tk.END, "Loading project... This may take a moment for large projects."
        )
        self.update()

        try:
            output = self.project_dumper.process_project(path, self.custom_prompt)
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, output)
            self.generated_output = output
            self.status_var.set(f"Project loaded: {path}")
        except Exception as e:
            self.status_var.set(f"Error: {e}")
            messagebox.showerror("Error", str(e))

    def _copy_to_clipboard(self) -> None:
        """
        Copy the generated output to the system clipboard.
        """
        if self.generated_output:
            self.clipboard_clear()
            self.clipboard_append(self.generated_output)
            self.update()
            self.status_var.set("Output copied to clipboard")
            messagebox.showinfo("Copied", "Output copied to clipboard.")
        else:
            self.status_var.set("No output to copy")
            messagebox.showwarning(
                "No Output", "No project output has been generated yet."
            )

    def _save_to_file(self) -> None:
        """
        Save the generated output to a text file.
        """
        if self.generated_output:
            out_path = filedialog.asksaveasfilename(
                title="Save Output File",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt")],
            )
            if out_path:
                Path(out_path).write_text(self.generated_output, encoding="utf-8")
                self.status_var.set(f"Output saved to {out_path}")
                messagebox.showinfo("Saved", f"Output saved to {out_path}")
        else:
            self.status_var.set("No output to save")
            messagebox.showwarning(
                "No Output", "No project output has been generated yet."
            )

    def _save_custom_prompt(self) -> None:
        """
        Save the custom prompt entered by the user.
        """
        custom_prompt = self.custom_prompt_text.get("1.0", tk.END).strip()
        if custom_prompt:
            self.custom_prompt = custom_prompt
            self.prompt_manager.save_custom_prompt(custom_prompt)
            self.status_var.set("Custom prompt saved")
            messagebox.showinfo(
                "Custom Prompt Saved", "Custom prompt saved successfully!"
            )
        else:
            messagebox.showwarning(
                "Invalid Input", "Please enter a valid custom prompt."
            )

    def _reset_to_default(self) -> None:
        """
        Reset the prompt to the default value.
        """
        self.custom_prompt = DEFAULT_PROMPT
        self.custom_prompt_text.delete("1.0", tk.END)
        self.custom_prompt_text.insert(tk.END, self.custom_prompt)
        self.prompt_manager.save_custom_prompt(DEFAULT_PROMPT)
        self.status_var.set("Prompt reset to default")
        messagebox.showinfo("Prompt Reset", "Prompt reset to default.")

    def _apply_settings(self) -> None:
        """
        Apply the settings from the settings tab.
        """
        excluded_dirs = {
            d.strip() for d in self.excluded_dirs_var.get().split(",") if d.strip()
        }
        excluded_patterns = {
            p.strip() for p in self.excluded_patterns_var.get().split(",") if p.strip()
        }
        self.project_dumper = ProjectDumper(excluded_dirs, excluded_patterns)
        self.status_var.set("Settings applied")
        messagebox.showinfo("Settings", "Settings have been applied.")


def run_cli_mode(args: argparse.Namespace) -> None:
    """
    Run the tool in command-line interface mode.
    """
    if not args.project_dir:
        print("Error: Project directory is required in CLI mode", file=sys.stderr)
        sys.exit(1)

    project_path = Path(args.project_dir)
    if not project_path.is_dir():
        print(f"Error: {args.project_dir} is not a valid directory", file=sys.stderr)
        sys.exit(1)

    # prompt_manager = PromptManager()
    custom_prompt = DEFAULT_PROMPT
    if args.prompt:
        prompt_path = Path(args.prompt)
        if prompt_path.is_file():
            try:
                if prompt_path.suffix.lower() == ".json":
                    with open(prompt_path, "r", encoding="utf-8") as f:
                        custom_prompt = json.load(f).get(
                            "custom_prompt", DEFAULT_PROMPT
                        )
                else:
                    custom_prompt = prompt_path.read_text(encoding="utf-8").strip()
            except Exception as e:
                print(f"Error loading prompt file: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            print(
                f"Warning: Prompt file {args.prompt} not found, using default prompt",
                file=sys.stderr,
            )

    project_dumper = ProjectDumper()
    try:
        output = project_dumper.process_project(project_path, custom_prompt)

        if args.output:
            try:
                Path(args.output).write_text(output, encoding="utf-8")
                print(f"Project dump saved to {args.output}")
            except Exception as e:
                print(f"Error writing to output file: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            print(output)

    except Exception as e:
        print(f"Error processing project: {e}", file=sys.stderr)
        sys.exit(1)


def run_gui_mode(args: argparse.Namespace) -> None:
    """
    Run the tool in graphical user interface mode.
    """
    app = App()

    if args.project_dir:
        project_path = Path(args.project_dir)
        if project_path.is_dir():
            app.folder_path_var.set(str(project_path))
            app._load_project(project_path)
        else:
            app.status_var.set(f"Invalid directory: {args.project_dir}")
    else:
        app.status_var.set(
            "Ready - Drag and drop a project folder or use Browse button"
        )

    if args.prompt:
        prompt_path = Path(args.prompt)
        if prompt_path.is_file():
            # prompt_manager = PromptManager()
            try:
                if prompt_path.suffix.lower() == ".json":
                    with open(prompt_path, "r", encoding="utf-8") as f:
                        custom_prompt = json.load(f).get(
                            "custom_prompt", DEFAULT_PROMPT
                        )
                else:
                    custom_prompt = prompt_path.read_text(encoding="utf-8").strip()

                app.custom_prompt = custom_prompt
                app.custom_prompt_text.delete("1.0", tk.END)
                app.custom_prompt_text.insert(tk.END, custom_prompt)
                app.status_var.set(f"Custom prompt loaded from {args.prompt}")
            except Exception as e:
                app.status_var.set(f"Error loading prompt file: {e}")

    app.mainloop()


def main() -> None:
    """
    Parse arguments and run the application in CLI or GUI mode.
    """
    parser = argparse.ArgumentParser(
        description="Project Dump Tool - Generate a dump of a software project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
    Examples:
    # Run in GUI mode
    python project_dump.py
    
    # Process a project and print to stdout
    python project_dump.py /path/to/project --cli
    
    # Process a project with a custom prompt and save to file
    python project_dump.py /path/to/project --cli --prompt custom_prompt.txt --output dump.txt
    
    # Open GUI with a project pre-loaded
    python project_dump.py /path/to/project
    """,
    )
    parser.add_argument(
        "project_dir",
        nargs="?",
        help="Project directory to analyze (optional in GUI mode)",
    )
    parser.add_argument("-p", "--prompt", help="Path to a custom prompt file")
    parser.add_argument(
        "-o", "--output", help="Path to output file (stdout if not specified)"
    )
    parser.add_argument(
        "--cli", action="store_true", help="Run in CLI mode without GUI"
    )
    args = parser.parse_args()

    if args.cli or args.project_dir:
        run_cli_mode(args)
    else:
        run_gui_mode(args)


if __name__ == "__main__":
    main()
