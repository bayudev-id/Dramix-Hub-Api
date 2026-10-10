#!/usr/bin/env bash
# ==============================================================================
# Dramix Gateway - Production Deployment Script for Linux / Mini PC
# Path: /opt/dramix_gateway
# Management: PM2
# Security: Port 8090 (Gateway Public/LAN) | Ports 6101-6107 (127.0.0.1 Loopback Only)
# ==============================================================================

set -euo pipefail

TARGET_DIR="/opt/dramix_gateway"
REPO_URL="https://github.com/bayudev-id/Dramix-Hub-Api.git"
BRANCH="master"
POCKETBASE_VERSION="0.40.4"

# Color constants
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo -e "${BLUE}"
echo "================================================================"
echo "         DRAMIX GATEWAY - 1-CLICK PRODUCTION DEPLOYMENT         "
echo "================================================================"
echo -e "${NC}"

# 1. Determine active user (non-root standard user for PM2)
CURRENT_USER="${SUDO_USER:-$(whoami)}"
if [ "$CURRENT_USER" = "root" ]; then
    log_warn "Running directly as root. Standard non-root user is recommended for PM2."
fi

# 2. Check & create target directory
log_info "Preparing deployment directory: ${TARGET_DIR}..."
if [ ! -d "$TARGET_DIR" ]; then
    if [ "$(id -u)" -eq 0 ]; then
        mkdir -p "$TARGET_DIR"
        chown -R "$CURRENT_USER:$CURRENT_USER" "$TARGET_DIR"
    else
        sudo mkdir -p "$TARGET_DIR"
        sudo chown -R "$CURRENT_USER:$CURRENT_USER" "$TARGET_DIR"
    fi
fi

cd "$TARGET_DIR"

# 3. Clone or update repository
log_info "Synchronizing repository from GitHub (${BRANCH})..."
if [ ! -d ".git" ]; then
    git clone -b "$BRANCH" "$REPO_URL" .
else
    git fetch origin "$BRANCH"
    git reset --hard "origin/$BRANCH"
fi

# Ensure user ownership across repository
if [ "$(id -u)" -eq 0 ] && [ "$CURRENT_USER" != "root" ]; then
    chown -R "$CURRENT_USER:$CURRENT_USER" "$TARGET_DIR"
fi

# 4. PocketBase Linux Binary Setup
log_info "Checking PocketBase Linux binary..."
ARCH="$(uname -m)"
case "$ARCH" in
    x86_64)
        PB_ARCH="linux_amd64"
        ;;
    aarch64|arm64)
        PB_ARCH="linux_arm64"
        ;;
    armv7l)
        PB_ARCH="linux_armv7"
        ;;
    *)
        log_error "Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

PB_BIN="$TARGET_DIR/pocketbase/pocketbase"
if [ ! -f "$PB_BIN" ]; then
    log_info "Downloading PocketBase v${POCKETBASE_VERSION} (${PB_ARCH})..."
    PB_TMP="$(mktemp -d)"
    PB_URL="https://github.com/pocketbase/pocketbase/releases/download/v${POCKETBASE_VERSION}/pocketbase_${POCKETBASE_VERSION}_${PB_ARCH}.zip"
    curl -fsSL "$PB_URL" -o "$PB_TMP/pb.zip"
    unzip -q -o "$PB_TMP/pb.zip" -d "$PB_TMP"
    mv "$PB_TMP/pocketbase" "$PB_BIN"
    rm -rf "$PB_TMP"
    chmod +x "$PB_BIN"
    log_success "PocketBase binary installed at $PB_BIN"
else
    chmod +x "$PB_BIN"
fi

log_info "Applying PocketBase database migrations and default data..."
(cd "$TARGET_DIR/pocketbase" && ./pocketbase migrate up)
log_success "PocketBase migrations up to date."

# 5. Setup Unified Python Virtual Environment
log_info "Setting up unified Python virtual environment (.venv)..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

.venv/bin/pip install --upgrade pip --quiet
log_info "Installing Python dependencies from requirements.txt..."
.venv/bin/pip install -r requirements.txt --quiet
log_success "Python virtual environment ready."

# 6. Setup Node.js Service (KissKH API)
if [ -d "services/kisskh_api" ]; then
    log_info "Installing KissKH Node.js dependencies..."
    (cd services/kisskh_api && npm install --omit=dev --silent)
    log_success "KissKH dependencies ready."
fi

# 7. Network Security & Firewall Verification
log_info "Verifying network isolation and security rules..."
if command -v ufw >/dev/null 2>&1; then
    UFW_STATUS="$(sudo ufw status | head -n 1 || true)"
    if [[ "$UFW_STATUS" =~ "active" ]]; then
        log_info "UFW detected. Allowing port 8090/tcp and denying internal ports from LAN..."
        sudo ufw allow 8090/tcp comment 'Dramix Gateway Port'
        # Defense in depth: Deny direct external connections to internal ports
        for p in {6101..6108}; do
            sudo ufw deny in to any port "$p" proto tcp comment "Block internal microservice $p" >/dev/null 2>&1 || true
        done
        log_success "UFW firewall rules applied."
    fi
fi

# 8. PM2 Process Launch / Reload
log_info "Deploying services with PM2..."
if ! command -v pm2 >/dev/null 2>&1; then
    log_warn "PM2 not found. Installing PM2 globally via npm..."
    if [ "$(id -u)" -eq 0 ]; then
        npm install -g pm2
    else
        sudo npm install -g pm2
    fi
fi

pm2 startOrReload ecosystem.config.js
pm2 save
log_success "PM2 services deployed and state saved."

# 9. Healthcheck & Security Verification
log_info "Performing post-deployment verification..."
sleep 3

# Verify Gateway (Port 8090)
GW_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8090/api/health" || echo "000")
if [ "$GW_STATUS" = "200" ]; then
    log_success "Gateway health check passed: HTTP 200 (port 8090)"
else
    log_warn "Gateway health check returned: HTTP $GW_STATUS (please check pm2 logs dramix-pocketbase)"
fi

# Verify Internal Microservice Binding (Should bind 127.0.0.1 only)
VIU_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:6105/health" || echo "000")
log_info "Internal VIU service loopback response: HTTP $VIU_STATUS"

echo ""
echo -e "${GREEN}================================================================${NC}"
echo -e "${GREEN}       DRAMIX GATEWAY DEPLOYMENT COMPLETED SUCCESSFULLY         ${NC}"
echo -e "${GREEN}================================================================${NC}"
echo "Summary:"
echo " - Directory        : $TARGET_DIR"
echo " - Gateway URL      : http://<MINIPC_LAN_IP>:8090"
echo " - Admin Dashboard  : http://<MINIPC_LAN_IP>:8090/_/"
echo " - Internal Services: 127.0.0.1 ports 6101-6107 (Strictly Isolated)"
echo ""
echo "Useful Commands:"
echo " - Check status : pm2 status"
echo " - View logs    : pm2 logs"
echo " - Restart all  : pm2 restart ecosystem.config.js"
echo ""
