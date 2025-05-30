# Project Dump Tool

This tool generates a comprehensive snapshot of your project's codebase, optimized for AI-powered analysis.
It consolidates all source files into a single, readable text file with an ASCII directory tree and clear separators between files.

![alt text](./assets/gui_image.png)

## Features

- **Directory Traversal:** Recursively traverses project directories.
- **Automatic `.gitignore` Exclusion:** Automatically excludes files and directories specified in `.gitignore` files within the project.
- **Customizable Exclusion:** Excludes directories and files based on user-defined patterns (applied in addition to `.gitignore`).
- **GUI and CLI:** Offers both a graphical user interface and a command-line interface for flexibility.
- **Drag-and-Drop (GUI):** Easily load projects by dragging and dropping folders onto the application window.
- **Custom Prompt:** Allows users to configure a custom prompt that prefixes the project dump.

## Setup

1.  **Prerequisites:** Ensure you have Python 3.10 or later installed on your system. You can check your Python version by running:
    ```bash
    python --version
    ```
    or
    ```bash
    python3 --version
    ```

2.  **(Recommended for GUI Drag-and-Drop):** Install the `tkinterdnd2` library using pip:
    ```bash
    pip install tkinterdnd2
    ```
    This library provides drag-and-drop functionality in the graphical user interface. If you intend to use the GUI and want drag-and-drop support, this step is recommended. The application will attempt to install it if it's not found, but manual installation beforehand can prevent potential issues.

3.  **Download the Script:** Save the provided Python code `src/project_dump.py` as `project_dump.py` or any other `.py` file name you prefer.

## Usage

### GUI Mode

1.  Run the script:
    ```bash
    python src/project_dump.py
    ```
2.  You can either:
    - Drag and drop a project folder onto the application window.
    - Click the "Browse..." button to select a project folder.
3.  The generated project dump will be displayed in the "Output" tab. Files larger than 5MB will be skipped, and a notification will be present in the output.
4.  Customize the prompt in the "Custom Prompt" tab and save it.
5.  Adjust additional exclusion settings in the "Settings" tab and apply them. These exclusions are applied on top of the rules defined in `.gitignore`.
6.  Use the "Copy to Clipboard" or "Save to File" buttons to handle the output.

### CLI Mode

1.  Run the script with the project directory as an argument and the `--cli` flag:
    ```bash
    python project_dump.py /path/to/your/project --cli
    ```
    This will print the project dump to the standard output. Files larger than 5MB will be skipped, and a notification will be printed to the console.

2.  To save the output to a file, use the `--output` option:
    ```bash
    python project_dump.py /path/to/your/project --cli --output output.txt
    ```

3.  To use a custom prompt from a file, use the `--prompt` option. The prompt file can be a plain text file or a JSON file with a `"custom_prompt"` key:
    ```bash
    python project_dump.py /path/to/your/project --cli --prompt custom_prompt.txt --output dump.txt
    python project_dump.py /path/to/your/project --cli --prompt custom_prompt.json --output dump.txt
    ```

## Command-Line Arguments

```
usage: project_dump.py [-h] [-p PROMPT] [-o OUTPUT] [--cli] [project_dir]

Project Dump Tool - Generate a dump of a software project

positional arguments:
  project_dir           Project directory to analyze (optional in GUI mode)

options:
  -h, --help            show this help message and exit
  -p PROMPT, --prompt PROMPT
                        Path to a custom prompt file
  -o OUTPUT, --output OUTPUT
                        Path to output file (stdout if not specified)
  --cli                 Run in CLI mode without GUI

Examples:
 # Run in GUI mode
 python project_dump.py

 # Process a project and print to stdout
 python project_dump.py /path/to/project --cli

 # Process a project with a custom prompt and save to file
 python project_dump.py /path/to/project --cli --prompt custom_prompt.txt --output dump.txt

 # Open GUI with a project pre-loaded
 python project_dump.py /path/to/project
```

## Default and `.gitignore` Exclusions

The tool automatically integrates exclusion rules from `.gitignore` files found in the project root. Additionally, the following directories and file patterns are excluded by default (and can be further customized in the GUI settings):

**Default Excluded Directories:**

- `node_modules`
- `.git`
- `__pycache__`

**Default Excluded File Patterns:**

- `*.log`
- `*.tmp`
- `*.pyc`

Files larger than 5MB are automatically skipped during the dump generation.

## License

This project is licensed under the **MIT License**. See the `LICENSE` file for more details.

## Attribution

If you use this tool in your work or research, attribution is appreciated. You can mention the project name "Project Dump Tool" and optionally link to the repository if you have obtained it from a public source. Your acknowledgement helps others discover and benefit from this tool.

## Dependencies

- Python 3.10 or later
- `tkinterdnd2` (optional, for drag-and-drop in GUI mode, install with `pip install tkinterdnd2`)
```