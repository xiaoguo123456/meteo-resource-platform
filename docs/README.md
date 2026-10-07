# 气象资源空间智能平台文档

文档以 **V0.2** 为当前产品基线，统一描述功能范围、数据边界、系统架构和 UI 设计。后续开发、评审和验收都以本目录为准，不再以 Notion 页面作为产品文档来源。

## 阅读顺序

1. [产品与功能](./01-product-and-function.md)
2. [Open-Meteo 数据与数据规范](./02-open-meteo-data.md)
3. [系统架构](./03-system-architecture.md)
4. [UI 设计](./04-ui-design.md)
5. [路线图与验收](./05-roadmap-and-acceptance.md)

## 目录结构

```text
docs/
├── README.md
├── 01-product-and-function.md
├── 02-open-meteo-data.md
├── 03-system-architecture.md
├── 04-ui-design.md
├── 05-roadmap-and-acceptance.md
    └── ui/
        ├── README.md
        └── v0.2/
            └── 01-unified-weather-resource-suite-v2.png
```

## 当前版本边界

- 唯一外部气象数据底座：自部署 Open-Meteo。
- 地图对象统一为用户维护的关注点、区域和自定义坐标。
- V0.2 做天气分析、风光资源评估、风险提醒、数据质量和报告导出。
- 当前不接入电站、SCADA、电表、逆变器或风机运行数据。
- 当前不输出实际发电量、功率偏差、弃电、调度动作和交易申报结果。
- 旧版涉及上述内容的视觉稿已删除，不再作为实现依据。

文档版本：V0.2｜2026-10-07
