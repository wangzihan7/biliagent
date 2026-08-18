import type { App } from 'vue';
import * as echarts from 'echarts';
import 'echarts-wordcloud';

declare module 'vue' {
  interface ComponentCustomProperties {
    $echarts: typeof echarts;
  }
}

export function setupEcharts(app: App) {
  // Attach ECharts instance to global properties
  app.config.globalProperties.$echarts = echarts;
}

