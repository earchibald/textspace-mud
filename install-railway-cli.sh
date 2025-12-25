#!/bin/bash
# Manual Railway CLI Installation for devcontainer
# Run this if npm install failed

echo "🚀 Installing Railway CLI manually..."

# Detect architecture
ARCH=$(uname -m)
OS=$(uname -s | tr '[:upper:]' '[:lower:]')

echo "Detected: $OS / $ARCH"

# Map architecture names
case "$ARCH" in
    x86_64)
        ARCH_NAME="x86_64"
        ;;
    aarch64|arm64)
        ARCH_NAME="aarch64"
        ;;
    *)
        echo "❌ Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

# Build download URL
VERSION="v3.17.4"  # Use a stable version
BINARY="railway-${VERSION}-${ARCH_NAME}-unknown-${OS}-gnu"
URL="https://github.com/railwayapp/cli/releases/download/${VERSION}/${BINARY}.tar.gz"

echo "Downloading from: $URL"

# Download and install
cd /tmp || exit 1
curl -fsSL "$URL" -o railway.tar.gz

if [ $? -ne 0 ]; then
    echo "❌ Download failed. Trying alternative method..."
    
    # Try direct binary download without tar
    BINARY_URL="https://github.com/railwayapp/cli/releases/download/${VERSION}/${BINARY}"
    curl -fsSL "$BINARY_URL" -o railway
    
    if [ $? -eq 0 ]; then
        chmod +x railway
        sudo mv railway /usr/local/bin/
        echo "✅ Railway CLI installed successfully (direct binary)"
        railway --version
        exit 0
    else
        echo "❌ Alternative download also failed"
        echo ""
        echo "Manual installation options:"
        echo "1. Use Railway Dashboard for configuration"
        echo "2. Install on your local machine (outside devcontainer)"
        echo "3. Check: https://railway.app/cli for latest instructions"
        exit 1
    fi
fi

tar -xzf railway.tar.gz
chmod +x railway
sudo mv railway /usr/local/bin/

echo "✅ Railway CLI installed successfully"
railway --version
