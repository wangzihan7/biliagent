<template>
  <el-container class="app-layout">
    <!-- Top bar -->
    <el-header class="app-header">
      <div class="header-left">
        <div class="logo-mark">B</div>
        <div class="logo-text">BiliAgent Studio</div>
      </div>
      <div class="header-center">
        <div class="system-title">
          <span class="title-icon">📊</span>
          <span class="title-text">哔哩哔哩内容智能分析系统</span>
        </div>
      </div>
      <div class="header-right">
        <el-tag size="small" v-if="auth.isAdmin" type="success">管理员</el-tag>
        <el-button link type="primary" @click="router.push({ name: 'Profile' })">个人信息</el-button>
        <span class="user-name">{{ auth.userName }}</span>
        <el-button link type="primary" @click="handleLogout">退出</el-button>
      </div>
    </el-header>

    <el-container class="app-body">
      <!-- Sidebar -->
      <el-aside width="220px" class="app-aside">
        <el-menu :default-active="activeMenu" router class="app-menu">
          <el-menu-item index="/topics">课题工作台</el-menu-item>
          <el-menu-item index="/reports">课题报告</el-menu-item>
          <el-menu-item index="/chat">会话分析</el-menu-item>
          <el-menu-item index="/crawl">爬虫管理</el-menu-item>
          <el-menu-item index="/datasets">数据集管理</el-menu-item>
          <el-sub-menu v-if="auth.isAdmin" index="admin">
            <template #title>系统管理</template>
            <el-menu-item index="/admin/users">用户管理</el-menu-item>
            <el-menu-item index="/admin/logs">操作日志</el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-aside>

      <!-- Main content -->
      <el-main class="app-main">
        <div class="app-main-inner">
          <router-view />
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const activeMenu = computed(() => {
  if (route.path.startsWith('/admin')) return route.path;
  if (route.path.startsWith('/crawl')) return '/crawl';
  if (route.path.startsWith('/datasets')) return '/datasets';
  if (route.path.startsWith('/chat')) return '/chat';
  if (route.path.startsWith('/reports')) return '/reports';
  return '/topics';
});

const handleLogout = () => {
  auth.logout();
  router.push({ name: 'Login' });
};
</script>

<style scoped>
.app-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f3f5fb;
}

.app-body {
  flex: 1;
  min-height: 0;
}

.app-header {
  display: flex;
  align-items: center;
  padding: 0 20px;
  background: linear-gradient(90deg, #e0f2fe, #e9d5ff);
  border-bottom: 1px solid rgba(148, 163, 184, 0.35);
  color: #0f172a;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo-mark {
  width: 28px;
  height: 28px;
  border-radius: 999px;
  background: radial-gradient(circle at 30% 30%, #2f88ff, #8b5cf6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  color: #0b1120;
}

.logo-text {
  font-size: 14px;
  font-weight: 600;
}

.header-center {
  flex: 1;
  display: flex;
  justify-content: center;
  padding: 0 32px;
}

.system-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  font-size: 20px;
}

.title-text {
  font-size: 16px;
  font-weight: 600;
  background: linear-gradient(135deg, #1e40af 0%, #7c3aed 50%, #0891b2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 2px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.user-name {
  color: #0f172a;
}

.app-aside {
  background: linear-gradient(180deg, #eef4ff 0%, #f5f7fb 100%);
  border-right: 1px solid rgba(148, 163, 184, 0.35);
  height: 100%;
}

.app-menu {
  border-right: none;
  background-color: transparent;
}

:deep(.app-menu.el-menu) {
  --el-menu-bg-color: transparent;
  --el-menu-text-color: #64748b;
  --el-menu-active-color: #2f88ff;
  --el-menu-hover-bg-color: #e5f0ff;
  border-right: none;
}

:deep(.app-menu .el-menu-item) {
  height: 40px;
  line-height: 40px;
  margin: 4px 10px;
  border-radius: 999px;
  padding-inline: 18px;
  font-size: 14px;
}

:deep(.app-menu .el-menu-item.is-active) {
  background-color: #ffffff;
  color: #1f2937;
  box-shadow: 0 6px 18px rgba(148, 163, 184, 0.35);
}

:deep(.app-menu .el-sub-menu__title) {
  height: 40px;
  line-height: 40px;
  margin: 4px 10px;
  border-radius: 999px;
  padding-inline: 18px;
  font-size: 14px;
}

.app-main {
  padding: 16px 20px;
  background-color: #f3f5fb;
  height: 100%;
  overflow-y: auto;
}

.app-main-inner {
  max-width: none;
  width: 100%;
  margin: 0;
}
</style>
