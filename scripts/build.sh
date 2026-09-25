#!/bin/bash
# Build Lambda deployment ZIPs (layer + both functions) into dist/
#
# The layer is built from requirements.txt (hash-pinned) for python3.13 arm64
# and is NOT committed to git. intro_common is copied in from src/common.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOY_DIR="$PROJECT_ROOT/deploy"
DIST_DIR="$PROJECT_ROOT/dist"
LAYER_DIR="$PROJECT_ROOT/build/layer"

echo "🔧 Building Lambda deployment packages..."

rm -rf "$LAYER_DIR"
mkdir -p "$DIST_DIR" "$LAYER_DIR/python/intro_common" \
    "$DEPLOY_DIR/ui-lambda" "$DEPLOY_DIR/worker-lambda"
rm -f "$DIST_DIR"/*.zip

# Install third-party dependencies for the Lambda runtime (arm64, python3.13)
echo "📦 Installing layer dependencies from requirements.txt..."
python3 -m pip install \
    --quiet \
    --require-hashes \
    --no-deps \
    --platform manylinux2014_aarch64 \
    --implementation cp \
    --python-version 3.13 \
    --only-binary=:all: \
    --target "$LAYER_DIR/python" \
    -r "$PROJECT_ROOT/requirements.txt"

# Sync common code to layer and deploy folders
echo "📁 Syncing intro_common..."
cp -f "$PROJECT_ROOT/src/common/"*.py "$LAYER_DIR/python/intro_common/"
cp -f "$PROJECT_ROOT/src/ui_lambda/ui_entry.py" "$DEPLOY_DIR/ui-lambda/ui_entry.py"
cp -f "$PROJECT_ROOT/src/worker_lambda/worker_entry.py" "$DEPLOY_DIR/worker-lambda/worker_entry.py"

# Build UI Lambda ZIP
echo "📦 Building ui-lambda.zip..."
(cd "$DEPLOY_DIR/ui-lambda" && zip -qr "$DIST_DIR/ui-lambda.zip" . -x '__pycache__/*')

# Build Worker Lambda ZIP
echo "📦 Building worker-lambda.zip..."
(cd "$DEPLOY_DIR/worker-lambda" && zip -qr "$DIST_DIR/worker-lambda.zip" . -x '__pycache__/*')

# Build Layer ZIP
echo "📦 Building layer-python313-arm64.zip..."
(cd "$LAYER_DIR" && zip -qr "$DIST_DIR/layer-python313-arm64.zip" python -x '*__pycache__*')

echo ""
echo "✅ Build complete!"
ls -lh "$DIST_DIR"/*.zip
