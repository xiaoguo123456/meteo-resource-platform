# Open-Meteo 数据与数据规范

## 1. 数据能力与产品映射

| 数据能力 | 主要变量或内容 | 产品用途 |
| --- | --- | --- |
| Forecast | 当前、小时、15 分钟、日尺度；温度、湿度、降水、云量、气压、能见度、天气码 | 总览、预报、风险 |
| Wind | 10/80/120/180m 风速、风向、阵风和高空变量 | 风能资源、风场图层、大风风险 |
| Solar radiation | GHI、DNI、DHI、GTI、地外辐射，支持倾角和方位角 | 太阳能资源评估、辐射图层 |
| Historical / reanalysis | ERA5、ERA5-Land、ERA5-Ensemble、IFS、CERRA 等 | 历史回看、资源基线和异常分析 |
| Models / ensemble | ECMWF、GFS、ICON、CMA、JMA、KMA 等模型及集合结果 | 模型对比、离散度和置信范围 |
| Air quality | PM2.5、PM10、臭氧、NO₂、SO₂、CO、AQI、花粉和沙尘 | 环境风险和沙尘提醒 |
| Marine | 波高、波向、周期、涌浪、海温、海流、潮位 | 沿海区域和海上资源分析 |
| Flood | 河流流量、集合均值和分位数 | 洪水风险图层和提醒 |
| Spatial | 地理编码、时区、海拔和约 90m DEM | 关注点建档、地形修正和地图定位 |

## 2. 数据边界

Open-Meteo 提供气象和环境条件，不提供某个电站、风机或光伏阵列的实际功率。V0.2 的所有资源结果都应标注为天气资源评估，不能命名为实际发电量或功率预测。

每次请求保留以下元数据：`provider`、`api_family`、`model`、`run_time`、`valid_time`、`resolution`、`quality_flag`、`source_url`。

## 3. 统一时空与单位

- 内部统一使用 UTC 存储，按照关注点时区展示。
- 温度：`°C`；风速：`m/s`；降水：`mm`；辐射：`W/m²`；河流流量：`m³/s`。
- 经纬度采用 WGS84；空间查询的距离单位在接口层明确为米或千米。
- 15 分钟、小时和日尺度数据不得在没有标记的情况下混用。

## 4. 数据质量状态

统一使用以下状态：

| 状态 | 含义 | 展示方式 |
| --- | --- | --- |
| `raw` | 接口原始值 | 可用于分析 |
| `interpolated` | 按规则插值 | 显示插值标记 |
| `estimated` | 估算值 | 显示估算标记 |
| `missing` | 没有值 | 显示缺失和影响范围 |
| `corrected` | 经过人工或规则修正 | 保留修正记录 |

数据接口异常时，需要同时记录最后成功时间、影响变量、影响区域和恢复任务。页面直接展示过期、缺失或降级状态；变量口径和算法细节放入字段说明或数据字典。

## 5. 采集与质量流程

```text
定时拉取 → 保存原始 JSON → 标准化变量/单位/时间
        → 去重与质量检查 → 写入时序库
        → 生成空间查询数据 → 更新页面和报告
```

去重键建议为 `model + run_time + location_id + valid_at + variable`。原始快照和处理结果分开保存，便于回放和审计。

## 6. 参考接口

- [Weather Forecast API](https://open-meteo.com/en/docs)
- [Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)
- [Air Quality API](https://open-meteo.com/en/docs/air-quality-api)
- [Marine Weather API](https://open-meteo.com/en/docs/marine-weather-api)
- [Flood API](https://open-meteo.com/en/docs/flood-api)
- [Elevation API](https://open-meteo.com/en/docs/elevation-api)
- [Geocoding API](https://open-meteo.com/en/docs/geocoding-api)
