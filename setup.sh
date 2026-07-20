#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"

SUDO=""
if command -v sudo >/dev/null 2>&1; then
  SUDO="sudo"
fi

echo "Checking Python..."
if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "Python not found. Installing..."
  if command -v apt-get >/dev/null 2>&1; then
    $SUDO apt-get update
    $SUDO apt-get install -y python3 python3-pip python3-venv
  elif command -v brew >/dev/null 2>&1; then
    brew install python
  elif command -v yum >/dev/null 2>&1; then
    $SUDO yum install -y python3 python3-pip python3-venv
  else
    echo "Could not install Python automatically. Please install it manually."
    exit 1
  fi

  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    echo "Python installation failed."
    exit 1
  fi
fi

echo "Checking pip..."
if ! "$PYTHON_BIN" -m pip --version >/dev/null 2>&1; then
  echo "pip not found. Installing..."
  "$PYTHON_BIN" -m ensurepip --upgrade || {
    if command -v apt-get >/dev/null 2>&1; then
      $SUDO apt-get install -y python3-pip
    elif command -v brew >/dev/null 2>&1; then
      brew install python
    elif command -v yum >/dev/null 2>&1; then
      $SUDO yum install -y python3-pip
    else
      echo "Could not install pip automatically."
      exit 1
    fi
  }
fi

echo "Checking venv support..."
if ! "$PYTHON_BIN" -m venv --help >/dev/null 2>&1; then
  echo "venv module not available. Installing..."
  if command -v apt-get >/dev/null 2>&1; then
    $SUDO apt-get install -y python3-venv
  elif command -v brew >/dev/null 2>&1; then
    brew install python
  elif command -v yum >/dev/null 2>&1; then
    $SUDO yum install -y python3-venv
  else
    echo "Could not install venv support automatically."
    exit 1
  fi
fi

echo "Checking ffmpeg..."
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg not found. Installing..."
  if command -v apt-get >/dev/null 2>&1; then
    $SUDO apt-get update
    $SUDO apt-get install -y ffmpeg
  elif command -v brew >/dev/null 2>&1; then
    brew install ffmpeg
  elif command -v yum >/dev/null 2>&1; then
    $SUDO yum install -y ffmpeg
  else
    echo "Could not install ffmpeg automatically. Please install it manually."
    exit 1
  fi
fi

echo "Creating virtual environment..."
"$PYTHON_BIN" -m venv "$VENV_DIR"

echo "Activating virtual environment..."
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "Upgrading pip..."
python -m pip install --upgrade pip

echo "Installing requirements from $REQUIREMENTS_FILE..."
pip install -r "$REQUIREMENTS_FILE"

echo "Setup complete."