#!/usr/bin/env bash
# One-time setup on a fresh Ubuntu VM (Oracle Cloud Always Free). Run as the default user:
#   curl -fsSL https://raw.githubusercontent.com/DavBao-dev/Dysgraphia-Screening-Prototype/main/deploy/oracle/setup.sh | bash
# Re-running it updates the code and rebuilds the app.
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype.git}"
REPO_REF="${REPO_REF:-main}"
APP_DIR="${APP_DIR:-$HOME/dysgraphia}"

echo "==> Installing Docker"
if ! command -v docker >/dev/null; then
  sudo apt-get update -y
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y docker.io docker-compose-v2 git curl iptables-persistent
  sudo systemctl enable --now docker
fi

echo "==> Opening ports 80 and 443 in the VM firewall"
# Oracle's Ubuntu images ship iptables rules that reject everything except SSH.
for port in 80 443; do
  if ! sudo iptables -C INPUT -p tcp -m state --state NEW --dport "$port" -j ACCEPT 2>/dev/null; then
    sudo iptables -I INPUT 6 -p tcp -m state --state NEW --dport "$port" -j ACCEPT
  fi
done
sudo netfilter-persistent save

echo "==> Fetching the code"
if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" fetch --depth 1 origin "$REPO_REF"
  git -C "$APP_DIR" checkout -q FETCH_HEAD
else
  git clone --depth 1 --branch "$REPO_REF" "$REPO_URL" "$APP_DIR"
fi

PUBLIC_IP="$(curl -fsS https://ifconfig.me)"
DOMAIN="${DOMAIN:-${PUBLIC_IP//./-}.sslip.io}"
echo "==> Public IP $PUBLIC_IP, domain $DOMAIN"

cd "$APP_DIR/deploy/oracle"
# --no-cache on the app image so a rebuild always clones the latest $REPO_REF.
sudo DOMAIN="$DOMAIN" REPO_REF="$REPO_REF" docker compose build --no-cache app
sudo DOMAIN="$DOMAIN" REPO_REF="$REPO_REF" docker compose up -d

echo "==> Waiting for the app"
for _ in $(seq 1 90); do
  if curl -fsS "https://$DOMAIN/api/health" >/dev/null 2>&1; then
    echo "Ready: https://$DOMAIN"
    exit 0
  fi
  sleep 5
done
echo "Not reachable yet. Check: sudo docker compose -f $APP_DIR/deploy/oracle/docker-compose.yml logs" >&2
exit 1
