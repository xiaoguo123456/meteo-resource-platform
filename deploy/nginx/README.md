# Nginx 访问策略

生产机当前 Open-Meteo Docker 端口曾绑定到 `0.0.0.0:8090`，并通过 Docker-USER 只放行一个 IP。平台上线后采用以下策略：

- Open-Meteo 改为只绑定 `127.0.0.1:8090`。
- 平台和 API 由 Nginx 统一从 80 端口提供。
- 已知办公出口 IP 通过 `allow` 免认证。
- 其他来源通过 Basic Auth 访问，满足“非白名单也可以访问”的需求。
- `/health` 保持无认证，便于监控；业务页面、API 和 Open-Meteo 代理均受认证保护。

启用前需要替换配置中的白名单 IP，并在服务器生成密码文件：

```bash
apt-get update
apt-get install -y nginx apache2-utils
htpasswd -c /etc/nginx/.htpasswd-meteo meteo
cp deploy/nginx/meteo-resource-platform.conf /etc/nginx/sites-available/meteo-resource-platform.conf
ln -s /etc/nginx/sites-available/meteo-resource-platform.conf /etc/nginx/sites-enabled/meteo-resource-platform.conf
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
```

Basic Auth 只作为入口保护。若绑定域名，下一步应加 HTTPS（Let's Encrypt），避免密码在 HTTP 链路中传输。
