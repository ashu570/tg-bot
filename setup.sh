```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"

SUDO=""
if [[ "$(id -u)" -ne 0 ]] && command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
fi

# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------

install_apt_package() {
    $SUDO apt-get update
    $SUDO apt-get install -y "$@"
}

# ------------------------------------------------------------
# Check / Install Python 3.12
# ------------------------------------------------------------

echo "Checking Python 3.12..."

if command -v python3.12 >/dev/null 2>&1; then
    PYTHON_BIN="python3.12"
else
    echo "Python 3.12 not found. Installing..."

    if command -v apt-get >/dev/null 2>&1; then
        install_apt_package python3.12 python3.12-venv python3.12-dev
        PYTHON_BIN="python3.12"
    else
        echo "Could not install Python 3.12 automatically."
        echo "Please install Python 3.12 manually."
        exit 1
    fi
fi

echo "Using Python: $("$PYTHON_BIN" --version)"

# ------------------------------------------------------------
# Check / Install pip
# ------------------------------------------------------------

echo "Checking pip..."

if ! "$PYTHON_BIN" -m pip --version >/dev/null 2>&1; then
    echo "pip not found. Installing..."

    if command -v apt-get >/dev/null 2>&1; then
        install_apt_package python3.12-pip 2>/dev/null || true
    fi
fi

# Python 3.12 on Ubuntu normally gets pip through ensurepip
if ! "$PYTHON_BIN" -m pip --version >/dev/null 2>&1; then
    echo "pip is still unavailable. Trying ensurepip..."

    "$PYTHON_BIN" -m ensurepip --upgrade
fi

if ! "$PYTHON_BIN" -m pip --version >/dev/null 2>&1; then
    echo "Failed to install pip for Python 3.12."
    exit 1
fi

echo "Using pip: $("$PYTHON_BIN" -m pip --version)"

# ------------------------------------------------------------
# Check / Install venv support
# ------------------------------------------------------------

echo "Checking venv support..."

if ! "$PYTHON_BIN" -c "import ensurepip" >/dev/null 2>&1; then
    echo "Python 3.12 venv support not found. Installing..."

    if command -v apt-get >/dev/null 2>&1; then
        install_apt_package python3.12-venv
    else
        echo "Could not install python3.12-venv automatically."
        exit 1
    fi
fi

# Verify that venv actually works
if ! "$PYTHON_BIN" -m venv --help >/dev/null 2>&1; then
    echo "Python 3.12 venv support is unavailable."
    echo "Please install python3.12-venv manually."
    exit 1
fi

# ------------------------------------------------------------
# Check / Install FFmpeg
# ------------------------------------------------------------

echo "Checking ffmpeg..."

if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "ffmpeg not found. Installing..."

    if command -v apt-get >/dev/null 2>&1; then
        install_apt_package ffmpeg
    elif command -v brew >/dev/null 2>&1; then
        brew install ffmpeg
    elif command -v yum >/dev/null 2>&1; then
        $SUDO yum install -y ffmpeg
    else
        echo "Could not install ffmpeg automatically."
        echo "Please install ffmpeg manually."
        exit 1
    fi
fi

echo "Using ffmpeg: $(ffmpeg -version | head -n 1)"

# ------------------------------------------------------------
# Create virtual environment
# ------------------------------------------------------------

echo "Creating virtual environment..."

if [[ -d "$VENV_DIR" ]]; then
    echo "Existing virtual environment found."

    # Verify that it is usable
    if [[ ! -x "$VENV_DIR/bin/python" ]]; then
        echo "Existing virtual environment is invalid. Recreating..."
        rm -rf "$VENV_DIR"
    fi
fi

if [[ ! -d "$VENV_DIR" ]]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# ------------------------------------------------------------
# Activate virtual environment
# ------------------------------------------------------------

echo "Activating virtual environment..."

source "$VENV_DIR/bin/activate"

echo "Virtual environment Python:"
python --version

python -m pip install --upgrade pip

if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
    echo "requirements.txt not found:"
    echo "$REQUIREMENTS_FILE"
    exit 1
fi

echo "Installing requirements from $REQUIREMENTS_FILE..."

python -m pip install -r "$REQUIREMENTS_FILE"

echo
echo "========================================"
echo "Setup complete!"
echo "========================================"
echo "Python: $(python --version)"
echo "Virtual environment: $VENV_DIR"
echo
echo "To activate it later:"
echo "source $VENV_DIR/bin/activate"
```
