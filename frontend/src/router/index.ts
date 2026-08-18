import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';
import AppLayout from '@/views/layout/AppLayout.vue';
import { useAuthStore } from '@/stores/auth';

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/RegisterView.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: AppLayout,
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/topics' },
      {
        path: 'topics',
        name: 'TopicList',
        component: () => import('@/views/topics/TopicListView.vue'),
      },
      {
        path: 'reports',
        name: 'ReportsOverview',
        component: () => import('@/views/reports/ReportsOverviewView.vue'),
      },
      {
        path: 'topics/:topicId',
        name: 'TopicDetail',
        component: () => import('@/views/topics/TopicDetailView.vue'),
        props: true,
      },
      {
        path: 'datasets',
        name: 'Datasets',
        component: () => import('@/views/datasets/DatasetsPage.vue'),
      },

      {
        path: 'crawl',
        name: 'CrawlManage',
        component: () => import('@/views/crawl/CrawlPage.vue'),
      },
      {
        path: 'chat/:conversationId?',
        name: 'Chat',
        component: () => import('@/views/chat/ChatPage.vue'),
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/profile/ProfilePage.vue'),
      },
      {
        path: 'admin/users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/AdminUsersView.vue'),
        meta: { requiresAdmin: true },
      },
      {
        path: 'admin/logs',
        name: 'AdminLogs',
        component: () => import('@/views/admin/AdminLogsView.vue'),
        meta: { requiresAdmin: true },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/topics',
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, _from, next) => {
  const auth = useAuthStore();
  // 尝试从本地恢复登录态
  if (!auth.token) {
    auth.restore();
  }

  if (!to.meta.public && !auth.isAuthenticated) {
    return next({ name: 'Login', query: { redirect: to.fullPath } });
  }

  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return next({ name: 'TopicList' });
  }

  next();
});

export default router;
