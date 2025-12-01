#!/bin/bash

# =========================================================
#  WEB SPIDER - DEVELOPER SOURCE INSTALLER (Linux Port)
# =========================================================
#
# This script will create a Python virtual environment
# in the 'src' folder and install dependencies into it.
#

echo "Changing directory to /src..."
cd src

# 1. Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
  echo ""
  echo "!--- ERROR: requirements.txt not found ---!"
  echo "This installer must be in the parent folder of \"src\"."
  echo "Your \"src\" folder must contain \"requirements.txt\"."
  echo ""
  read -p "Press Enter to exit..."
  exit 1
fi

# ... (other file checks for zorah.py/engine.py can remain here) ...

# 4. Create Virtual Environment
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment at '$VENV_DIR'..."
    python3 -m venv $VENV_DIR
    if [ $? -ne 0 ]; then
        echo ""
        echo "!--- FAILED TO CREATE VIRTUAL ENVIRONMENT ---!"
        echo "Please make sure 'python3-venv' is installed."
        echo "(On Debian/Ubuntu, try: sudo apt install python3-venv)"
        echo ""
        read -p "Press Enter to exit..."
        exit 1
    fi
else
    echo "Virtual environment '$VENV_DIR' already exists. Skipping creation."
fi

# 5. Activate and Install Packages
echo "Activating virtual environment and installing packages..."
source $VENV_DIR/bin/activate

# Upgrade pip inside the venv
python3 -m pip install --upgrade pip

# Install packages from requirements.txt
python3 -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
  echo ""
  echo "!--- FAILED TO INSTALL PACKAGES ---!"
  echo "Please check your internet connection or pip setup."
  read -p "Press Enter to exit..."
  deactivate
  exit 1
fi

# Deactivate after we're done
deactivate

# 6. Show success message
echo ""
echo "All packages installed successfully into '$VENV_DIR'!"
echo ""
echo "To run the program, you must first navigate to the 'src'"
echo "folder and activate the virtual environment:"
echo ""
echo "  cd src"
echo "  source $VENV_DIR/bin/activate"
echo ""
echo "Then, you can run the program:"
echo "  python3 zorah.py"
echo ""
echo "When you are finished, just type 'deactivate' to exit the environment."
echo ""
read -p "Press Enter to continue..."