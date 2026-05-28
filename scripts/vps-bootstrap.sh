#!/usr/bin/env bash
# Run on VPS as root (pull from GitHub + docker compose)
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/Fukushi-Chinmoku/TopHub.git}"
INSTALL_DIR="${INSTALL_DIR:-/opt/marchel_develop}"
BRANCH="${BRANCH:-main}"

log() { echo "[vps-bootstrap] $*"; }

if ! command -v docker >/dev/null 2>&1; then
  log "Installing Docker..."
  apt-get update -qq
  apt-get install -y -qq ca-certificates curl git
  curl -fsSL https://get.docker.com | sh
fi

if ! docker compose version >/dev/null 2>&1; then
  apt-get install -y -qq docker-compose-plugin 2>/dev/null || true
fi

if [ -d "${INSTALL_DIR}/.git" ]; then
  log "Updating ${INSTALL_DIR}"
  git -C "${INSTALL_DIR}" fetch origin "${BRANCH}"
  git -C "${INSTALL_DIR}" checkout "${BRANCH}"
  git -C "${INSTALL_DIR}" pull --ff-only origin "${BRANCH}"
else
  log "Cloning ${REPO_URL} -> ${INSTALL_DIR}"
  mkdir -p "$(dirname "${INSTALL_DIR}")"
  git clone --branch "${BRANCH}" "${REPO_URL}" "${INSTALL_DIR}"
fi

cd "${INSTALL_DIR}"
if [ ! -f .env ]; then
  cp .env.example .env
  PG_PASS="$(openssl rand -hex 16)"
  sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=${PG_PASS}/" .env
  log "Created .env"
fi

if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q "Status: active"; then
  ufw allow 80/tcp || true
fi

log "Building containers..."
docker compose up -d --build
docker compose ps
log "Done. App: http://$(hostname -I | awk '{print $1}')/"
