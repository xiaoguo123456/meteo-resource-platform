# Nginx 访问策略

生产机当前 Open-Meteo Docker 端口曾绑定到 `0.0.0.0:8090`，平台上线后采用以下策略：

- Open-Meteo 改为只绑定 `127.0.0.1:8090`。
- 平台和 API 由 Nginx 统一从 80 端口提供。
- 网站、API 和 Open-Meteo 代理均由 Nginx 公开提供。
- `/health` 保持公开，便于监控。

启用配置：

```bash
apt-get update
apt-get install -y nginx
cp deploy/nginx/meteo-resource-platform.conf /etc/nginx/sites-available/meteo-resource-platform.conf
ln -s /etc/nginx/sites-available/meteo-resource-platform.conf /etc/nginx/sites-enabled/meteo-resource-platform.conf
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
```

若绑定域名，下一步应加 HTTPS（Let's Encrypt）。
