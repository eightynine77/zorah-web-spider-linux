#!/bin/bash

# =========================================================
#  ZORAH WEB SPIDER - RUNNER SCRIPT
# =========================================================
#
# This script automatically finds the virtual environment,
# changes to the 'src' directory, and runs the main
# zorah.py application.
#

echo "--- Zorah Web Spider Runner ---"

# --- Get the absolute path of the directory where this script is located ---
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# --- Define paths based on the script's location ---
SRC_DIR="$SCRIPT_DIR/src"
VENV_PYTHON="$SRC_DIR/venv/bin/python3"
MAIN_SCRIPT="$SRC_DIR/zorah.py"


# --- [START] PRE-RUN CHECKS ---

# 1. Check if the 'src' directory exists
if [ ! -d "$SRC_DIR" ]; then
    echo ""
    echo "!--- ERROR: 'src' directory not found ---!"
    echo "Looked for it at: $SRC_DIR"
    echo "Please make sure this 'run.sh' script is in the main 'zorah-web-crawler' directory."
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# 2. Check if the virtual environment's Python executable exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo ""
    echo "!--- ERROR: Virtual environment not found ---!"
    echo "Looked for Python at: $VENV_PYTHON"
    echo "Did you run the './installer.sh' script successfully first?"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# 3. Check if the main 'zorah.py' script exists
if [ ! -f "$MAIN_SCRIPT" ]; then
    echo ""
    echo "!--- ERROR: Main script 'zorah.py' not found ---!"
    echo "Looked for it at: $MAIN_SCRIPT"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# --- [END] PRE-RUN CHECKS ---


# --- All checks passed. Run the application ---

# 1. Change to the 'src' directory.
# This is critical so zorah.py/engine.py can find the 'components' folder.
echo "Changing directory to '$SRC_DIR'..."
cd "$SRC_DIR"

# 2. Run the main script using the virtual environment's Python executable.
echo "Starting zorah.py..."
echo "Press 'q' in the application to quit."
echo "---------------------------------------------------------"

"$VENV_PYTHON" "$MAIN_SCRIPT"

echo "---------------------------------------------------------"
echo "Program exited. Returning to main shell."