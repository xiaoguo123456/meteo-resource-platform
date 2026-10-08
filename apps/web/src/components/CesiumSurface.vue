<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Cartesian2, Cartesian3, Cartographic, Color, EllipsoidTerrainProvider, ImageryLayer, LabelStyle, Math as CesiumMath, OpenStreetMapImageryProvider, ScreenSpaceEventHandler, ScreenSpaceEventType, UrlTemplateImageryProvider, Viewer } from 'cesium'
import 'cesium/Build/Cesium/Widgets/widgets.css'
import { getWeatherGrid, type WeatherGridPoint } from '../api'

const props = defineProps<{ latitude?: number; longitude?: number; label?: string; layer?: string }>()
const emit = defineEmits<{ select: [latitude: number, longitude: number] }>()
const container = ref<HTMLElement | null>(null)
let viewer: Viewer | undefined
let handler: ScreenSpaceEventHandler | undefined
let radarLayer: ImageryLayer | undefined
let markerEntity: ReturnType<Viewer['entities']['add']> | undefined
let radarRequestId = 0
let gridRequestId = 0
let windEntities: ReturnType<Viewer['entities']['add']>[] = []

function updateMarker() {
  if (!viewer) return
  if (markerEntity) viewer.entities.remove(markerEntity)
  if (props.latitude == null || props.longitude == null) return
  markerEntity = viewer.entities.add({
    position: Cartesian3.fromDegrees(props.longitude, props.latitude, 0),
    point: { pixelSize: 12, color: Color.fromCssColorString('#216dea'), outlineColor: Color.WHITE, outlineWidth: 2 },
    label: { text: props.label ?? '地图选点', font: '14px sans-serif', fillColor: Color.WHITE, style: LabelStyle.FILL_AND_OUTLINE, outlineColor: Color.fromCssColorString('#17345f'), outlineWidth: 3, pixelOffset: new Cartesian2(0, -28) },
  })
}

function clearWindLayer() {
  if (!viewer) return
  for (const entity of windEntities) viewer.entities.remove(entity)
  windEntities = []
}

async function updateWindLayer() {
  clearWindLayer()
  const requestId = ++gridRequestId
  if (!viewer || props.layer !== '风场') return
  try {
    const points = await getWeatherGrid()
    if (!viewer || requestId !== gridRequestId) return
    for (const point of points as WeatherGridPoint[]) {
      if (point.wind_speed_ms == null || point.wind_direction_deg == null) continue
      const length = Math.min(4, Math.max(0.7, point.wind_speed_ms * 0.12))
      const direction = CesiumMath.toRadians(point.wind_direction_deg)
      const endLatitude = point.latitude + Math.cos(direction) * length
      const endLongitude = point.longitude + Math.sin(direction) * length
      windEntities.push(viewer.entities.add({
        position: Cartesian3.fromDegrees(point.longitude, point.latitude, 20000),
        polyline: {
          positions: Cartesian3.fromDegreesArray([point.longitude, point.latitude, endLongitude, endLatitude]),
          width: 2.5,
          material: Color.fromCssColorString('#216dea').withAlpha(0.82),
        },
        label: { text: `${point.wind_speed_ms.toFixed(1)} m/s`, font: '11px sans-serif', fillColor: Color.WHITE, style: LabelStyle.FILL_AND_OUTLINE, outlineColor: Color.fromCssColorString('#17345f'), outlineWidth: 2, pixelOffset: new Cartesian2(4, -8) },
      }))
    }
  } catch (error) {
    if (requestId === gridRequestId) console.error('风场网格加载失败', error)
  }
}

async function updateRadarLayer() {
  if (!viewer) return
  const requestId = ++radarRequestId
  if (radarLayer) {
    viewer.imageryLayers.remove(radarLayer, true)
    radarLayer = undefined
  }
  if (props.layer !== '降水') return
  try {
    const response = await fetch('https://api.rainviewer.com/public/weather-maps.json')
    const payload = await response.json() as { host?: string; radar?: { past?: { path: string }[]; nowcast?: { path: string }[] } }
    const frames = [...(payload.radar?.past ?? []), ...(payload.radar?.nowcast ?? [])]
    const frame = frames[frames.length - 1]
    if (!frame || !payload.host || !viewer || requestId !== radarRequestId) return
    radarLayer = viewer.imageryLayers.addImageryProvider(new UrlTemplateImageryProvider({
      url: `${payload.host}${frame.path}/256/{z}/{x}/{y}/2/1_1.png`,
      maximumLevel: 10,
      credit: 'Weather data by RainViewer',
    }))
  } catch (error) {
    if (requestId === radarRequestId) console.error('RainViewer 图层加载失败', error)
  }
}

onMounted(() => {
  if (!container.value) return
  viewer = new Viewer(container.value, {
    baseLayer: false,
    terrainProvider: new EllipsoidTerrainProvider(),
    skyBox: false,
    skyAtmosphere: false,
    animation: false,
    baseLayerPicker: false,
    fullscreenButton: false,
    geocoder: false,
    homeButton: false,
    infoBox: false,
    navigationHelpButton: false,
    sceneModePicker: false,
    selectionIndicator: false,
    timeline: false,
  })
  viewer.scene.globe.baseColor = Color.fromCssColorString('#b9d9de')
  viewer.imageryLayers.addImageryProvider(new OpenStreetMapImageryProvider({ url: 'https://tile.openstreetmap.org/' }))
  const longitude = props.longitude ?? 110
  const latitude = props.latitude ?? 30
  updateMarker()
  viewer.camera.setView({ destination: Cartesian3.fromDegrees(longitude, latitude, props.longitude == null ? 4500000 : 1800000) })
  handler = new ScreenSpaceEventHandler(viewer.scene.canvas)
  handler.setInputAction((movement: { position: Cartesian2 }) => {
    if (!viewer) return
    const cartesian = viewer.camera.pickEllipsoid(movement.position, viewer.scene.globe.ellipsoid)
    if (!cartesian) return
    const coordinate = Cartographic.fromCartesian(cartesian)
    emit('select', CesiumMath.toDegrees(coordinate.latitude), CesiumMath.toDegrees(coordinate.longitude))
  }, ScreenSpaceEventType.LEFT_CLICK)
  void updateRadarLayer()
  void updateWindLayer()
})

watch(() => [props.latitude, props.longitude] as const, ([latitude, longitude]) => {
  if (!viewer || latitude == null || longitude == null) return
  updateMarker()
  viewer.camera.setView({ destination: Cartesian3.fromDegrees(longitude, latitude, 1800000) })
})

watch(() => props.layer, (layer) => {
  if (!viewer || !layer) return
  const colors: Record<string, string> = { 风场: '#6ca8d8', 云量: '#a8c8d8', 辐照度: '#e2bd68', 降水: '#6e9fd1' }
  viewer.scene.globe.baseColor = Color.fromCssColorString(colors[layer] ?? '#b9d9de')
  void updateRadarLayer()
  void updateWindLayer()
})

onBeforeUnmount(() => {
  handler?.destroy()
  radarRequestId += 1
  gridRequestId += 1
  clearWindLayer()
  viewer?.destroy()
})
</script>

<template><div ref="container" class="cesium-surface" /></template>
