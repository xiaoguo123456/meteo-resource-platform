<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { Cartesian2, Cartesian3, Color, EllipsoidTerrainProvider, LabelStyle, OpenStreetMapImageryProvider, Viewer } from 'cesium'
import 'cesium/Build/Cesium/Widgets/widgets.css'

const props = defineProps<{ latitude?: number; longitude?: number; label?: string }>()
const container = ref<HTMLElement | null>(null)
let viewer: Viewer | undefined

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
  const longitude = props.longitude ?? 121.47
  const latitude = props.latitude ?? 31.23
  viewer.entities.add({
    position: Cartesian3.fromDegrees(longitude, latitude, 0),
    point: { pixelSize: 12, color: Color.fromCssColorString('#216dea'), outlineColor: Color.WHITE, outlineWidth: 2 },
    label: { text: props.label ?? '关注点', font: '14px sans-serif', fillColor: Color.WHITE, style: LabelStyle.FILL_AND_OUTLINE, outlineColor: Color.fromCssColorString('#17345f'), outlineWidth: 3, pixelOffset: new Cartesian2(0, -28) },
  })
  viewer.camera.flyTo({ destination: Cartesian3.fromDegrees(longitude, latitude, 1800000) })
})

onBeforeUnmount(() => viewer?.destroy())
</script>

<template><div ref="container" class="cesium-surface"><div class="cesium-fallback">Cesium · {{ props.label ?? '空间图层' }}</div></div></template>
