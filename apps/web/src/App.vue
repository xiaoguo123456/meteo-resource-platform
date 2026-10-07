<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { getForecast, getQualitySummary, getWatchpoints, type Watchpoint, type WeatherPoint } from './api'

type NavItem = { key: string; label: string; icon: string; title: string; subtitle: string }
const navItems: NavItem[] = [
  { key: 'overview', label: '总览', icon: '⌂', title: '气象总览', subtitle: '把天气变化、洞察和资源潜力放在一起' },
  { key: 'space', label: '空间', icon: '⌖', title: '空间指挥台', subtitle: '多源图层叠合，查看关注点与区域天气' },
  { key: 'forecast', label: '预报', icon: '◌', title: '预报与模型', subtitle: '对比模型结果，查看不确定性分析' },
  { key: 'resources', label: '资源', icon: '▣', title: '风光资源评估', subtitle: '评估太阳能与风能资源潜力' },
  { key: 'risk', label: '风险', icon: '△', title: '风险与情景', subtitle: '识别天气风险，比较情景影响' },
  { key: 'data', label: '数据', icon: '▤', title: '数据与报告', subtitle: '监控数据质量并生成业务报告' },
]

const currentKey = ref('overview')
const watchpoints = ref<Watchpoint[]>([])
const selectedId = ref('wp-east')
const points = ref<WeatherPoint[]>([])
const sourceStatus = ref<{ name: string; status: string; freshness_minutes: number; coverage_percent: number }[]>([])
const loading = ref(true)
const error = ref('')
const active = computed(() => navItems.find((item) => item.key === currentKey.value) || navItems[0])
const selected = computed(() => watchpoints.value.find((item) => item.id === selectedId.value) || watchpoints.value[0])
const chartPoints = computed(() => points.value.slice(0, 24))
const averageTemp = computed(() => chartPoints.value.length ? (chartPoints.value.reduce((sum, item) => sum + (item.temperature_c || 0), 0) / chartPoints.value.length).toFixed(1) : '--')
const averageWind = computed(() => chartPoints.value.length ? (chartPoints.value.reduce((sum, item) => sum + (item.wind_speed_ms || 0), 0) / chartPoints.value.length).toFixed(1) : '--')
const averageRadiation = computed(() => chartPoints.value.length ? Math.round(chartPoints.value.reduce((sum, item) => sum + (item.shortwave_radiation_wm2 || 0), 0) / chartPoints.value.length) : 0)

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
      <div class="search">⌕ <span>搜索功能、数据...</span></div>
      <div class="top-actions"><span class="bell">♧</span><span class="avatar">U</span><span class="user-name">张伟<small>企业用户</small></span><span>⌄</span></div>
    </header>
    <aside class="sidebar">
      <nav>
        <button v-for="item in navItems" :key="item.key" :class="['nav-item', { active: currentKey === item.key }]" @click="currentKey = item.key">
          <span class="nav-icon">{{ item.icon }}</span><span>{{ item.label }}</span>
        </button>
      </nav>
      <div class="sidebar-footer">V0.2 · 数据健康 {{ sourceStatus.length ? '在线' : '检查中' }}</div>
    </aside>
    <main class="main-content">
      <div class="page-heading"><div><h1>{{ active.title }}</h1><p>{{ active.subtitle }}</p></div><div class="toolbar"><select v-model="selectedId"><option v-for="item in watchpoints" :key="item.id" :value="item.id">关注区域：{{ item.name }}</option></select><button class="date-btn">2026-10-07　⌄</button></div></div>
      <div v-if="error" class="error-banner">{{ error }} <button @click="loadData">重试</button></div>
      <section class="kpi-grid">
        <article class="kpi-card"><span class="kpi-icon temp">♨</span><div><strong>{{ averageTemp }}°C</strong><small>当前平均气温</small><em class="up">↑ 1.2°C　较昨日</em></div></article>
        <article class="kpi-card"><span class="kpi-icon wind">≋</span><div><strong>{{ averageWind }} m/s</strong><small>平均风速</small><em class="down">↓ 6%　较昨日</em></div></article>
        <article class="kpi-card"><span class="kpi-icon sun">☼</span><div><strong>{{ averageRadiation }} W/m²</strong><small>平均太阳辐照度</small><em class="up">↑ 8%　较昨日</em></div></article>
        <article class="kpi-card"><span class="kpi-icon water">◐</span><div><strong>62%</strong><small>平均湿度</small><em class="down">↓ 4%　较昨日</em></div></article>
      </section>
      <section class="content-grid">
        <article class="panel trend-panel"><div class="panel-title"><div><h2>{{ currentKey === 'space' ? '风场与关注点' : '气温变化（°C）' }}</h2><span>未来 24 小时 · {{ selected?.name }}</span></div><button class="ghost-btn">···</button></div><div class="chart-area"><div class="chart-y"><span>30</span><span>20</span><span>10</span><span>0</span></div><svg class="line-chart" viewBox="0 0 640 220" preserveAspectRatio="none"><defs><linearGradient id="fill" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#2d75e8" stop-opacity=".22"/><stop offset="1" stop-color="#2d75e8" stop-opacity="0"/></linearGradient></defs><path d="M0 180 C70 145 90 125 145 132 S220 88 280 104 S355 52 420 76 S490 110 560 65 S610 92 640 50 L640 220 L0 220Z" fill="url(#fill)"/><path d="M0 180 C70 145 90 125 145 132 S220 88 280 104 S355 52 420 76 S490 110 560 65 S610 92 640 50" fill="none" stroke="#2d75e8" stroke-width="4" stroke-linecap="round"/></svg></div><div class="chart-x"><span>10-07</span><span>10-08</span><span>10-09</span><span>10-10</span><span>10-11</span><span>10-12</span><span>10-13</span></div></article>
        <article class="panel risk-panel"><div class="panel-title"><div><h2>关注点风险</h2><span>需要关注的天气事件</span></div><button class="ghost-btn">···</button></div><div class="risk-list"><div class="risk-row"><span class="status-dot green"></span><span>预报接口</span><b>正常</b></div><div class="risk-row"><span class="status-dot green"></span><span>历史接口</span><b>正常</b></div><div class="risk-row"><span class="status-dot amber"></span><span>缓存任务</span><b class="amber-text">待处理</b></div><div class="risk-row"><span class="status-dot green"></span><span>报告任务</span><b>正常</b></div></div></article>
      </section>
      <section class="content-grid lower-grid">
        <article class="panel health-panel"><div class="panel-title"><div><h2>系统健康状态</h2><span>接口与分析任务</span></div><span class="health-badge">实时</span></div><div v-for="item in sourceStatus.slice(0, 4)" :key="item.name" class="health-row"><span>{{ item.name }}</span><div class="progress"><i :style="{ width: `${item.coverage_percent}%` }"></i></div><b>{{ item.coverage_percent }}%</b></div><div v-if="loading" class="empty-state">加载数据中...</div></article>
        <article class="panel map-panel"><div class="panel-title"><div><h2>空间指挥台</h2><span>Cesium 图层预览 · {{ selected?.name }}</span></div><button class="primary-btn" @click="currentKey = 'space'">打开空间</button></div><div class="map-preview"><div class="map-grid"></div><div class="map-orbit one"></div><div class="map-orbit two"></div><div class="map-pin pin-a">●</div><div class="map-pin pin-b">●</div><div class="map-label">风场 · 辐射 · 云量</div></div></article>
      </section>
      <section class="module-strip"><button v-for="item in navItems.slice(2)" :key="item.key" @click="currentKey = item.key"><span>{{ item.icon }}</span><b>{{ item.label }}</b><small>{{ item.subtitle }}</small><i>→</i></button></section>
    </main>
  </div>
</template>
