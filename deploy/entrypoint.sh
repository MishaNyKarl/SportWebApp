#!/bin/sh
set -e

echo "Ждём базу данных..."
if [ -n "$POSTGRES_HOST" ]; then
  until python -c "
import socket, os, sys
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2)
try:
    s.connect((os.environ.get('POSTGRES_HOST'), int(os.environ.get('POSTGRES_PORT', 5432))))
    sys.exit(0)
except Exception:
    sys.exit(1)
"; do
    sleep 1
  done
fi

echo "Применяем миграции..."
python manage.py migrate --noinput

echo "Собираем статику..."
python manage.py collectstatic --noinput

echo "Запускаем: $@"
exec "$@"
