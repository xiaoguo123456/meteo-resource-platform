<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { Cartesian3, Color, EllipsoidTerrainProvider, Viewer } from 'cesium'
import 'cesium/Build/Cesium/Widgets/widgets.css'

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
  viewer.camera.flyTo({ destination: Cartesian3.fromDegrees(121.47, 31.23, 1800000) })
})

onBeforeUnmount(() => viewer?.destroy())
</script>

<template><div ref="container" class="cesium-surface"><div class="cesium-fallback">空间图层加载中</div></div></template>
