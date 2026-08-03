#!/bin/bash
# Разовая настройка сервера под Ubuntu/Debian.
# Запускать один раз от root: bash server-setup.sh
#
# Что делает:
#   1. Ставит Docker + docker compose, git, ufw
#   2. Создаёт пользователя deploy (без пароля, только по SSH-ключу)
#   3. Генерирует SSH-ключ для CI/CD и добавляет deploy в группу docker
#   4. Настраивает firewall (22, 80, 443)
#   5. Клонирует репозиторий в /opt/sportapp
#
# После выполнения скрипт выведет ПРИВАТНЫЙ ключ — его нужно занести
# в GitHub Secrets репозитория как DEPLOY_SSH_KEY (см. deploy/README-deploy.md).

set -e

REPO_URL="https://github.com/MishaNyKarl/SportWebApp.git"
APP_DIR="/opt/sportapp"
DEPLOY_USER="deploy"

echo "==> Обновляем пакеты"
apt-get update -y && apt-get upgrade -y

echo "==> Ставим git, ufw, curl"
apt-get install -y git ufw curl

echo "==> Ставим Docker"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
fi

echo "==> Создаём пользователя ${DEPLOY_USER}"
if ! id "${DEPLOY_USER}" >/dev/null 2>&1; then
  adduser --disabled-password --gecos "" "${DEPLOY_USER}"
fi
usermod -aG docker "${DEPLOY_USER}"

echo "==> Генерируем SSH-ключ для CI/CD"
DEPLOY_HOME="/home/${DEPLOY_USER}"
KEY_PATH="${DEPLOY_HOME}/.ssh/github_deploy"
mkdir -p "${DEPLOY_HOME}/.ssh"
if [ ! -f "${KEY_PATH}" ]; then
  ssh-keygen -t ed25519 -f "${KEY_PATH}" -N "" -C "github-actions-deploy"
fi
cat "${KEY_PATH}.pub" >> "${DEPLOY_HOME}/.ssh/authorized_keys"
chown -R "${DEPLOY_USER}:${DEPLOY_USER}" "${DEPLOY_HOME}/.ssh"
chmod 700 "${DEPLOY_HOME}/.ssh"
chmod 600 "${DEPLOY_HOME}/.ssh/authorized_keys"

echo "==> Настраиваем firewall"
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "==> Клонируем репозиторий в ${APP_DIR}"
if [ ! -d "${APP_DIR}" ]; then
  git clone "${REPO_URL}" "${APP_DIR}"
fi
chown -R "${DEPLOY_USER}:${DEPLOY_USER}" "${APP_DIR}"

if [ ! -f "${APP_DIR}/.env" ]; then
  cp "${APP_DIR}/.env.example" "${APP_DIR}/.env"
  SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))" 2>/dev/null || openssl rand -base64 40)
  PGPASS=$(openssl rand -base64 24)
  SERVER_IP=$(curl -s -4 ifconfig.me || echo "127.0.0.1")
  sed -i "s#DJANGO_SECRET_KEY=.*#DJANGO_SECRET_KEY=${SECRET}#" "${APP_DIR}/.env"
  sed -i "s#DJANGO_ALLOWED_HOSTS=.*#DJANGO_ALLOWED_HOSTS=${SERVER_IP}#" "${APP_DIR}/.env"
  sed -i "s#POSTGRES_PASSWORD=.*#POSTGRES_PASSWORD=${PGPASS}#" "${APP_DIR}/.env"
  echo "==> Сгенерирован .env с реальными секретами (не в git)"
fi

echo ""
echo "======================================================================"
echo " ГОТОВО. Дальше вручную:"
echo ""
echo " 1) Первый запуск приложения:"
echo "      cd ${APP_DIR} && docker compose up -d --build"
echo ""
echo " 2) Скопируй приватный ключ ниже и добавь в GitHub Secrets"
echo "    (Settings → Secrets and variables → Actions) как DEPLOY_SSH_KEY:"
echo "----------------------------------------------------------------------"
cat "${KEY_PATH}"
echo "----------------------------------------------------------------------"
echo ""
echo " 3) Также добавь секреты:"
echo "      DEPLOY_HOST = $(curl -s -4 ifconfig.me || echo '<IP сервера>')"
echo "      DEPLOY_USER = ${DEPLOY_USER}"
echo ""
echo " 4) После этого рекомендуется отключить вход по паролю для root:"
echo "      passwd -l root"
echo "      sed -i 's/^#\\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config"
echo "      systemctl restart sshd"
echo "    (сначала убедись, что вход под deploy по ключу работает!)"
echo "======================================================================"
