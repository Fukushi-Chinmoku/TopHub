#!/usr/bin/env bash
# Deploy Codely (marchel_develop) on Ubuntu VPS — see README.md
set -euo pipefail

REPO_URL="${REPO_URL:-https://bitbucket.org/suvorov_labs/marchel_develop.git}"
INSTALL_DIR="${INSTALL_DIR:-/opt/marchel_develop}"
BRANCH="${BRANCH:-master}"

log() { echo "[deploy] $*"; }

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root: sudo bash deploy-vps.sh" >&2
  exit 1
fi

require_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "Docker not found. Install Docker + Compose plugin on Ubuntu 24.04 first." >&2
    exit 1
  fi
  if ! docker compose version >/dev/null 2>&1; then
    echo "docker compose (v2 plugin) not found. Install docker-compose-plugin." >&2
    exit 1
  fi
  log "Docker: $(docker --version); $(docker compose version)"
}

clone_or_update() {
  if [ -d "${INSTALL_DIR}/.git" ]; then
    log "Updating existing repo in ${INSTALL_DIR}"
    git -C "${INSTALL_DIR}" fetch origin "${BRANCH}"
    git -C "${INSTALL_DIR}" checkout "${BRANCH}"
    git -C "${INSTALL_DIR}" pull --ff-only origin "${BRANCH}"
  else
    log "Cloning ${REPO_URL} -> ${INSTALL_DIR}"
    mkdir -p "$(dirname "${INSTALL_DIR}")"
    git clone --branch "${BRANCH}" "${REPO_URL}" "${INSTALL_DIR}"
  fi
}

setup_env() {
  cd "${INSTALL_DIR}"
  if [ -f .env ]; then
    log ".env already exists, keeping it"
    return
  fi
  cp .env.example .env
  PG_PASS="$(openssl rand -hex 16)"
  sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=${PG_PASS}/" .env
  log "Created .env (random POSTGRES_PASSWORD)"
}

open_firewall() {
  if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
    ufw allow 80/tcp || true
    log "UFW: allowed port 80"
  fi
}

compose_up() {
  cd "${INSTALL_DIR}"
  log "Building and starting containers (may take several minutes)..."
  docker compose up -d --build
  log "Container status:"
  docker compose ps
}

health_check() {
  local tries=30
  log "Waiting for API health..."
  for i in $(seq 1 "${tries}"); do
    if curl -sf "http://127.0.0.1/api/health" >/dev/null; then
      log "Health OK: http://127.0.0.1/api/health"
      curl -s "http://127.0.0.1/api/health"
      echo
      log "App:      http://$(hostname -I | awk '{print $1}')/"
      log "API docs: http://$(hostname -I | awk '{print $1}')/docs"
      return 0
    fi
    sleep 5
  done
  log "Health check failed. Last logs:"
  docker compose -f "${INSTALL_DIR}/docker-compose.yml" logs --tail=50
  return 1
}

require_docker
clone_or_update
setup_env
open_firewall
compose_up
health_check
