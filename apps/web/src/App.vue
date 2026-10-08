<script setup lang="ts">
import { computed, onMounted, ref, watch, type Component } from 'vue'
import { Bell, CloudSun, Database, Droplets, LayoutDashboard, Search, SunMedium, Thermometer, TriangleAlert, Wind } from 'lucide-vue-next'
import { createReport, evaluateRisks, getForecast, getQualitySummary, getWatchpoints, type Watchpoint, type WeatherPoint } from './api'
import CesiumSurface from './components/CesiumSurface.vue'

type NavItem = { key: string; label: string; icon: Component; title: string; subtitle: string }
const navItems: NavItem[] = [
  { key: 'overview', label: '总览', icon: LayoutDashboard, title: '气象总览', subtitle: '把天气变化、洞察和资源潜力放在一起' },
  { key: 'forecast', label: '预报', icon: CloudSun, title: '预报与模型', subtitle: '对比模型结果，查看不确定性分析' },
  { key: 'resources', label: '资源', icon: SunMedium, title: '风光资源评估', subtitle: '评估太阳能与风能资源潜力' },
  { key: 'risk', label: '风险', icon: TriangleAlert, title: '风险与情景', subtitle: '识别天气风险，比较情景影响' },
  { key: 'data', label: '数据', icon: Database, title: '数据与报告', subtitle: '监控数据质量并生成业务报告' },
]

const currentKey = ref('overview')
const watchpoints = ref<Watchpoint[]>([])
const selectedId = ref('wp-east')
const points = ref<WeatherPoint[]>([])
const sourceStatus = ref<{ name: string; status: string; freshness_minutes: number; coverage_percent: number }[]>([])
const loading = ref(true)
const error = ref('')
const notice = ref('')
const layerOptions = ['风场', '云量', '辐照度', '降水'] as const
const activeLayer = ref<(typeof layerOptions)[number]>('风场')
const active = computed(() => navItems.find((item) => item.key === currentKey.value) || navItems[0])
const selected = computed(() => watchpoints.value.find((item) => item.id === selectedId.value) || watchpoints.value[0])
const chartPoints = computed(() => points.value.slice(0, 24))
const averageTemp = computed(() => chartPoints.value.length ? (chartPoints.value.reduce((sum, item) => sum + (item.temperature_c || 0), 0) / chartPoints.value.length).toFixed(1) : '--')
const averageWind = computed(() => chartPoints.value.length ? (chartPoints.value.reduce((sum, item) => sum + (item.wind_speed_ms || 0), 0) / chartPoints.value.length).toFixed(1) : '--')
const averageRadiation = computed(() => chartPoints.value.length ? Math.round(chartPoints.value.reduce((sum, item) => sum + (item.shortwave_radiation_wm2 || 0), 0) / chartPoints.value.length) : 0)
const averageHumidity = computed(() => chartPoints.value.length ? Math.round(chartPoints.value.reduce((sum, item) => sum + (item.relative_humidity_pct || 0), 0) / chartPoints.value.length) : 0)

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    watchpoints.value = await getWatchpoints()
    if (!watchpoints.value.some((item) => item.id === selectedId.value)) selectedId.value = watchpoints.value[0]?.id || ''
    const [forecast, quality] = await Promise.all([getForecast(selectedId.value), getQualitySummary()])
    points.value = forecast.points
    sourceStatus.value = quality.sources
  } catch (err) {
    error.value = 'API 暂不可用，请检查 API 服务或环境变量配置。'
    console.error(err)
  } finally {
    loading.value = false
  }
}

async function runRiskEvaluation() {
  if (!selectedId.value) return
  try {
    const events = await evaluateRisks(selectedId.value)
    notice.value = events.length ? `已生成 ${events.length} 条风险提醒` : '当前没有新的风险提醒'
  } catch { error.value = '风险评估失败，请检查 API 服务。' }
}

async function generateReport(type: 'weather_brief' | 'resource_assessment' | 'risk_review') {
  if (!selectedId.value) return
  try {
    const report = await createReport(type, selectedId.value)
    notice.value = `${report.title}已生成`
  } catch { error.value = '报告生成失败，请检查 API 服务。' }
}

watch(selectedId, async () => {
  if (!selectedId.value) return
  try { points.value = (await getForecast(selectedId.value)).points } catch (err) { console.error(err) }
})
onMounted(loadData)
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="brand"><span class="brand-mark">气象</span><span>能源</span></div>
      <div class="search"><Search :size="16" /><span>搜索功能、数据...</span></div>
      <div class="top-actions"><Bell :size="18" /></div>
    </header>
    <aside class="sidebar">
      <nav>
        <button v-for="item in navItems" :key="item.key" :class="['nav-item', { active: currentKey === item.key }]" @click="currentKey = item.key">
          <component :is="item.icon" class="nav-icon" :size="18" :stroke-width="1.8" /><span>{{ item.label }}</span>
        </button>
      </nav>
      <div class="sidebar-footer">V0.2</div>
    </aside>
    <main class="main-content">
      <div class="page-heading"><div><h1>{{ active.title }}</h1><p>{{ active.subtitle }}</p></div><div class="toolbar"><select v-model="selectedId"><option v-for="item in watchpoints" :key="item.id" :value="item.id">关注区域：{{ item.name }}</option></select><button class="date-btn">2026-10-07　⌄</button></div></div>
      <div v-if="error" class="error-banner">{{ error }} <button @click="loadData">重试</button></div>
      <div v-if="notice" class="notice-banner" @click="notice = ''">{{ notice }}</div>
      <section v-if="currentKey === 'overview'" class="overview-map panel"><div class="overview-map-head"><div><h2>空间总览</h2><span>实时关注区域 · {{ selected?.name }} · 当前图层：{{ activeLayer }}</span></div></div><div class="overview-map-layout"><div class="overview-map-stage"><div class="map-layer-tabs"><button v-for="layer in layerOptions" :key="layer" :class="{ selected: activeLayer === layer }" @click="activeLayer = layer">{{ layer }}</button></div><CesiumSurface :latitude="selected?.latitude" :longitude="selected?.longitude" :label="selected?.name" :layer="activeLayer" /></div><aside class="overview-map-summary"><div class="summary-location"><span class="summary-pin">●</span><div><strong>{{ selected?.name }}</strong><small>{{ selected?.latitude }}°N, {{ selected?.longitude }}°E</small></div></div><div class="summary-metric"><b>{{ averageTemp }}°C</b><span>近地面气温</span></div><div class="summary-metric"><b>{{ averageWind }} m/s</b><span>10 米风速</span></div><div class="summary-metric"><b>{{ averageRadiation }} W/m²</b><span>水平面辐照度</span></div><div class="summary-metric"><b>{{ averageHumidity }}%</b><span>相对湿度</span></div></aside></div></section>
      <section v-else-if="currentKey === 'forecast'" class="panel module-page"><div class="module-page-head"><div><h2>预报与模型</h2><span>未来 7 天 · {{ selected?.name }}</span></div><div class="model-pills"><span class="model blue">ECMWF</span><span class="model green">GFS</span><span class="model orange">ICON</span></div></div><div class="forecast-chart"><svg viewBox="0 0 900 230" preserveAspectRatio="none"><path d="M0 190 C80 140 120 145 175 115 S270 145 330 96 S430 112 500 82 S590 96 655 72 S760 100 900 55" fill="none" stroke="#216dea" stroke-width="4"/><path d="M0 200 C80 168 130 160 175 134 S270 160 330 115 S430 137 500 103 S590 115 655 98 S760 120 900 75" fill="none" stroke="#28b487" stroke-width="4"/><path d="M0 207 C80 188 120 177 175 155 S270 182 330 136 S430 155 500 122 S590 140 655 116 S760 146 900 95" fill="none" stroke="#f3a52f" stroke-width="4"/></svg></div><div class="data-table"><div class="table-row table-head"><span>模型</span><span>运行时间</span><span>状态</span><span>预报时长</span></div><div v-for="item in ['ECMWF', 'GFS', 'ICON']" :key="item" class="table-row"><b>{{ item }}</b><span>2026-10-07 06:00</span><span class="tag warning">待校验</span><span>7 天</span></div></div></section>
      <section v-else-if="currentKey === 'resources'" class="panel module-page"><div class="module-page-head"><div><h2>风光资源评估</h2><span>基于天气资源的区域潜力分析</span></div><button class="primary-btn">新建评估</button></div><div class="resource-grid"><div class="resource-map solar-map"><span>水平面总辐照度 GHI</span><b>{{ averageRadiation }} W/m²</b></div><div class="resource-map wind-map"><span>100 米高度平均风速</span><b>{{ averageWind }} m/s</b></div><div class="resource-summary"><h3>资源概览</h3><div><span>太阳能潜力</span><strong>{{ Math.min(100, Math.round(averageRadiation / 6)) }}<small>/100</small></strong></div><div><span>风能潜力</span><strong>{{ Math.min(100, Math.round(Number(averageWind) * 6)) }}<small>/100</small></strong></div><div><span>评估周期</span><b>未来 72 小时</b></div></div></div></section>
      <section v-else-if="currentKey === 'risk'" class="panel module-page"><div class="module-page-head"><div><h2>风险与情景</h2><span>阈值天气预警 · 影响范围 · 情景分析</span></div><button class="primary-btn" @click="runRiskEvaluation">运行评估</button></div><div class="risk-stats"><div><b>3</b><span>高风险提醒</span></div><div><b>5</b><span>中风险提醒</span></div><div><b>8</b><span>关注事件</span></div><div><b>0</b><span>已删除</span></div></div><div class="data-table"><div class="table-row table-head"><span>事件类型</span><span>发生时间</span><span>风险状态</span><span>操作</span></div><div v-for="item in [['大风','2026-10-08 ~ 10-09','待确认'],['降水','2026-10-10 ~ 10-11','已确认'],['高温','2026-10-12 ~ 10-13','待确认']]" :key="item[0]" class="table-row"><b>{{ item[0] }}</b><span>{{ item[1] }}</span><span class="tag warning">{{ item[2] }}</span><button class="text-btn">查看证据</button></div></div></section>
      <section v-else-if="currentKey === 'data'" class="panel module-page"><div class="module-page-head"><div><h2>数据与报告</h2><span>接口健康、模型运行、质量事件和报告生成</span></div><button class="primary-btn" @click="generateReport('weather_brief')">生成报告</button></div><div class="data-table"><div class="table-row table-head"><span>数据源</span><span>最后更新时间</span><span>状态</span><span>覆盖率</span></div><div v-for="item in sourceStatus" :key="item.name" class="table-row"><b>{{ item.name }}</b><span>{{ item.freshness_minutes == null ? '未核验' : `${item.freshness_minutes} 分钟前` }}</span><span :class="['tag', item.status === 'healthy' ? 'success' : 'warning']">{{ item.status === 'healthy' ? '正常' : '待核验' }}</span><span>{{ item.coverage_percent == null ? '—' : `${item.coverage_percent}%` }}</span></div></div><div class="report-cards"><button @click="generateReport('weather_brief')"><b>气象简报</b><small>区域天气与变化</small><span>生成报告 →</span></button><button @click="generateReport('resource_assessment')"><b>资源评估报告</b><small>风光资源潜力</small><span>生成报告 →</span></button><button @click="generateReport('risk_review')"><b>风险复盘</b><small>事件与触发证据</small><span>生成报告 →</span></button></div></section>
      <section v-if="currentKey === 'overview'" class="module-strip"><button v-for="item in navItems.slice(1)" :key="item.key" @click="currentKey = item.key"><component :is="item.icon" :size="19" /><b>{{ item.label }}</b><small>{{ item.subtitle }}</small><i>→</i></button></section>
    </main>
  </div>
</template>
