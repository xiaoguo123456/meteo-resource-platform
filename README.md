# 气象资源空间智能平台

基于自部署 Open-Meteo 和 Cesium 的气象资源分析平台。当前实现按 [V0.2 文档](./docs/README.md)开发，覆盖气象总览、空间图层、预报模型、风光资源、风险情景和数据报告。

## 开发环境

- Python 3.9+
- Node.js 20+
- Docker（可选，用于 PostgreSQL/PostGIS、Redis 和 MinIO）

## 启动 API

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## 启动 Web

```bash
cd apps/web
npm install
npm run dev
```

API 默认只读取 `OPEN_METEO_BASE_URL` 指定的自部署服务，失败返回错误。仅在显式设置 `ALLOW_DEMO_DATA=true` 时允许演示数据。演示结果标记为 `estimated` 和 `source=demo`。
