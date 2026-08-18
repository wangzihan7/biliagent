import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import router from './router';
import { setupElementPlus } from './plugins/element-plus';
import { setupEcharts } from './plugins/echarts';
import './styles/index.css';

const app = createApp(App);

const pinia = createPinia();
app.use(pinia);
app.use(router);

setupElementPlus(app);
setupEcharts(app);

app.mount('#app');
