# Деплой на сервер

Сервер: `169.255.57.42` (Ubuntu/Debian предполагается).

⚠️ **Пароль root, который был отправлен в чат, теперь считается скомпрометированным**
(он проходит через переписку в открытом виде). Ниже настройка сразу переводит доступ
на SSH-ключ и позволяет отключить вход по паролю — сделай это в конце.

## Шаг 1. Разово настроить сервер

Подключись с компьютера по SSH (единственный раз с паролем):

```bash
ssh root@169.255.57.42
```

Скачай и запусти скрипт настройки (он в репозитории, `deploy/server-setup.sh`):

```bash
curl -fsSL https://raw.githubusercontent.com/MishaNyKarl/SportWebApp/main/deploy/server-setup.sh -o server-setup.sh
bash server-setup.sh
```

Если репозиторий ещё не запушен — просто скопируй содержимое `deploy/server-setup.sh`
в файл на сервере (`nano server-setup.sh`, вставь, `Ctrl+O`, `Ctrl+X`) и запусти `bash server-setup.sh`.

Скрипт поставит Docker, git, ufw, создаст пользователя `deploy` с SSH-ключом для CI/CD,
склонирует репозиторий в `/opt/sportapp` и сгенерирует `.env` с реальными секретами.
В конце выведет **приватный ключ** — он понадобится на следующем шаге.

## Шаг 2. Первый запуск

```bash
cd /opt/sportapp
docker compose up -d --build
```

Проверь: `http://169.255.57.42` должен открыть приложение.
Создай администратора Django (по желанию):

```bash
docker compose exec web python manage.py createsuperuser
```

## Шаг 3. Настроить GitHub Actions (автодеплой на каждый push в main)

В репозитории на GitHub: **Settings → Secrets and variables → Actions → New repository secret**.
Добавь три секрета:

| Имя | Значение |
|---|---|
| `DEPLOY_HOST` | `169.255.57.42` |
| `DEPLOY_USER` | `deploy` |
| `DEPLOY_SSH_KEY` | приватный ключ, который вывел `server-setup.sh` (весь текст, включая `-----BEGIN...` и `-----END...`) |

После этого любой `git push` в ветку `main` будет автоматически собирать и
выкладывать приложение на сервер (workflow: `.github/workflows/deploy.yml`).

## Шаг 4. Закрыть доступ по паролю (рекомендуется)

Убедись, что вход `ssh deploy@169.255.57.42` по ключу работает, затем на сервере:

```bash
passwd -l root
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd
```

## Шаг 5. Домен и HTTPS (когда пришлёшь домен)

1. Направь A-запись домена на `169.255.57.42`.
2. В `deploy/nginx.conf` замени `server_name _;` на `server_name твой-домен.ru;`.
3. Поставь certbot и получи сертификат:
   ```bash
   apt-get install -y certbot python3-certbot-nginx
   docker compose stop nginx
   certbot certonly --standalone -d твой-домен.ru
   ```
4. Обновим `nginx.conf` под 443/SSL и `DJANGO_SSL_REDIRECT=True` в `.env` — сделаем этот
   шаг вместе, как только пришлёшь домен.
