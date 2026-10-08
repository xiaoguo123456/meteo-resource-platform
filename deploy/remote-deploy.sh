#!/usr/bin/env bash
set -euo pipefail

# 该脚本安装到服务器的 /usr/local/sbin/meteo-resource-deploy，由 GitHub Actions 调用。
release_file="${1:?缺少发布包路径}"
release_id="${2:?缺少发布编号}"
root_dir=/opt/meteo-resource-platform
release_dir="$root_dir/releases/$release_id"

test "$(id -u)" -eq 0
if ! id meteo >/dev/null 2>&1; then
  useradd --system --home-dir "$root_dir" --shell /usr/sbin/nologin meteo
fi
install -d -o root -g root -m 755 "$release_dir"
tar -xzf "$release_file" -C "$release_dir"

install -d -o meteo -g meteo -m 755 "$root_dir"
python3 -m venv "$root_dir/.venv"
"$root_dir/.venv/bin/pip" install --disable-pip-version-check -r "$release_dir/apps/api/requirements.txt"
ln -sfn "$release_dir/apps/api" "$root_dir/current-api"
ln -sfn "$release_dir/apps/web/dist" "$root_dir/current-web"

install -d -m 755 /etc/meteo-resource-platform
if [ ! -f /etc/meteo-resource-platform/api.env ]; then
  cat > /etc/meteo-resource-platform/api.env <<'EOF'
OPEN_METEO_BASE_URL=http://127.0.0.1:8090/v1
ALLOW_DEMO_DATA=false
CORS_ORIGINS=http://127.0.0.1
EOF
  chmod 640 /etc/meteo-resource-platform/api.env
fi

install -m 644 "$release_dir/deploy/systemd/meteo-resource-api.service" /etc/systemd/system/meteo-resource-api.service
sed "s#^root /var/www/meteo-resource-platform;#root $root_dir/current-web;#" \
  "$release_dir/deploy/nginx/meteo-resource-platform.conf" > /etc/nginx/sites-available/meteo-resource-platform.conf
ln -sfn /etc/nginx/sites-available/meteo-resource-platform.conf /etc/nginx/sites-enabled/meteo-resource-platform.conf
nginx -t
systemctl daemon-reload
systemctl enable --now meteo-resource-api.service
systemctl restart meteo-resource-api.service
systemctl reload nginx
curl --fail --silent http://127.0.0.1:8000/health >/dev/null
rm -f "$release_file"
