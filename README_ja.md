
# Project Dump Tool

**概要**

Project Dump Toolは、ソフトウェアプロジェクトの構造とファイル内容を包括的なテキスト形式でダンプするためのユーティリティです。このツールは、AIによるコード解析のための入力データ作成を主な目的としており、GUIとCLIの両方のインターフェースを提供します。除外パターンやディレクトリ名を指定することで、特定のファイルやディレクトリをダンプから除外することも可能です。

**主な機能**

* **ディレクトリトラバーサル:** カスタマイズ可能な除外パターンを用いたディレクトリの再帰的な探索。
* **.gitignoreサポート:** プロジェクトルートの`.gitignore`ファイルに記述されたパターンを自動的に適用。
* **GUIモード:** ドラッグ＆ドロップによるプロジェクト選択、設定変更、出力の表示。
* **カスタムプロンプト:** AI解析に含めるためのカスタムプロンプトの設定と保存。
* **CLIモード:** 自動化やスクリプトからの利用に適したコマンドラインインターフェース。
* **バイナリファイル検出:** バイナリファイルを自動的に検出し、出力から除外。
* **出力のコピー＆保存:** 生成されたダンプをクリップボードにコピーしたり、ファイルに保存したりする機能。
* **設定:** 除外するディレクトリやファイルパターンをGUIから設定可能。

**動作環境**

* Python 3.x
* (GUIモードの場合) tkinter
* (GUIでのドラッグ＆ドロップ機能を利用する場合) tkinterdnd2

**インストール**

GUIモードでドラッグ＆ドロップ機能を利用する場合は、`tkinterdnd2`のインストールが必要です。

```bash
pip install tkinterdnd2
```

**使用方法**

**GUIモード**

ターミナルで以下のコマンドを実行します。

```bash
python project_dump.py
```

アプリケーションが起動したら、以下のいずれかの方法でプロジェクトを選択します。

1.  **Browse...** ボタンをクリックして、プロジェクトのルートディレクトリを選択します。
2.  プロジェクトのルートディレクトリをウィンドウ内の指定の領域（「Generated Project Dump: (Drag & Drop folder here)」と表示された領域や、プロジェクトのパスを入力するテキストボックスなど）にドラッグ＆ドロップします。

プロジェクトが読み込まれると、その構造とファイル内容が「Output」タブのテキストエリアに表示されます。

* **Copy to Clipboard:** 生成されたダンプの内容をクリップボードにコピーします。
* **Save to File:** 生成されたダンプの内容をテキストファイルに保存します。
* **Custom Promptタブ:** AI解析に含めるためのカスタムプロンプトを編集・保存・デフォルトに戻すことができます。
* **Settingsタブ:** 除外するディレクトリ名やファイルパターンを設定できます。

**CLIモード**

ターミナルで以下のコマンドを実行します。

```bash
python project_dump.py /path/to/project --cli --output output.txt
```

* `/path/to/project`: 解析したいプロジェクトのルートディレクトリを指定します。
* `--cli`: CLIモードで実行することを指定します。
* `--output output.txt`: 生成されたダンプを`output.txt`というファイルに保存します。このオプションを省略すると、標準出力に結果が表示されます。
* `-p` または `--prompt custom_prompt.txt`: カスタムプロンプトが記述されたファイルを指定します。JSON形式またはプレーンテキスト形式のファイルが利用できます。

**例**

* GUIモードで起動:
    ```bash
    python project_dump.py
    ```
* CLIモードで`/home/user/my_project`を解析し、標準出力に表示:
    ```bash
    python project_dump.py /home/user/my_project --cli
    ```
* CLIモードで`/Users/user/my_project`を解析し、`dump.txt`に保存:
    ```bash
    python project_dump.py /Users/user/my_project --cli --output dump.txt
    ```
* CLIモードで`/mnt/c/projects/my_project`を解析し、`custom_prompt.txt`のプロンプトを使用して`analysis_data.txt`に保存:
    ```bash
    python project_dump.py /mnt/c/projects/my_project --cli --prompt custom_prompt.txt --output analysis_data.txt
    ```

**設定**

* **除外ディレクトリ:** デフォルトで`node_modules`, `.git`, `__pycache__`ディレクトリは解析から除外されます。GUIの「Settings」タブまたはコード内の`EXCLUDE_DIRS`定数を変更することで、除外するディレクトリを追加・変更できます。
* **除外ファイルパターン:** デフォルトで`*.log`, `*.tmp`, `*.pyc`パターンに一致するファイルは除外されます。GUIの「Settings」タブまたはコード内の`EXCLUDE_FILE_PATTERNS`定数を変更することで、除外するパターンを追加・変更できます。
* **.gitignore:** プロジェクトルートに`.gitignore`ファイルが存在する場合、そのファイルに記述されたパターンも自動的に除外ルールとして適用されます。
* **カスタムプロンプト:** GUIの「Custom Prompt」タブで編集・保存できます。保存されたカスタムプロンプトは`custom_prompt.json`ファイルに保存され、次回起動時にも読み込まれます。「Reset to Default」ボタンでデフォルトのプロンプトに戻すことができます。CLIモードでは、`--prompt`オプションでカスタムプロンプトファイルを指定できます。

**貢献**

バグ報告や機能提案など、コントリビューションは大歓迎です。

**ライセンス**

MIT Licens)
