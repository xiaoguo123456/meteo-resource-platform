# 生产部署

部署目标：Ubuntu 24.04 生产机、Open-Meteo Docker、Nginx、API systemd 服务和静态 Web。

## 本地构建

```bash
cd apps/web
npm run build
```

构建结果位于 `apps/web/dist`。API 依赖安装到生产机 `/opt/meteo-resource-platform/.venv`。

## API 服务

生产环境变量示例：

```dotenv
OPEN_METEO_BASE_URL=http://127.0.0.1:8090/v1
ALLOW_DEMO_DATA=false
CORS_ORIGINS=http://127.0.0.1
```

API 服务使用 `deploy/systemd/meteo-resource-api.service`，监听 `127.0.0.1:8000`，不直接暴露公网。

## Nginx 与访问控制

入口配置见 [`nginx/meteo-resource-platform.conf`](./nginx/meteo-resource-platform.conf)：

- 网站、API 和 Open-Meteo 代理公开访问。
- Open-Meteo 只绑定 `127.0.0.1:8090`。
- `/health` 保持无认证供监控使用。

当前服务器没有确认的域名和证书，因此配置暂以 HTTP 入口为基础。正式对外分享前应绑定域名并启用 HTTPS；Basic Auth 不应长期运行在明文 HTTP 上。
