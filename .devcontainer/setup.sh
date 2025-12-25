#!/bin/bash
set -e  # Exit on error

echo "==> Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y curl build-essential procps file git

echo "==> Creating Python virtual environment..."
python3 -m venv venv

echo "==> Activating virtual environment..."
source venv/bin/activate

echo "==> Upgrading pip..."
pip install --upgrade pip

echo "==> Installing Python dependencies..."
pip install --no-cache-dir -r requirements.txt

echo "==> Installing Homebrew (this may take a while)..."
if ! command -v brew &> /dev/null; then
    NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || true
    
    # Add brew to PATH
    if [ -d "/home/linuxbrew/.linuxbrew" ]; then
        echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> ~/.bashrc
        eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
    fi
fi

echo "==> Installing Railway CLI..."
if command -v brew &> /dev/null; then
    brew install railway || echo "Warning: Railway CLI installation failed, but continuing..."
else
    echo "Warning: Homebrew not available, skipping Railway CLI installation"
fi

echo "==> Setup complete!"
