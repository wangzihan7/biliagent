<template>
  <div class="space-y-5">
    <el-breadcrumb separator="/">
      <el-breadcrumb-item :to="{ name: 'TopicList' }">首页</el-breadcrumb-item>
      <el-breadcrumb-item>个人信息</el-breadcrumb-item>
    </el-breadcrumb>

    <el-card shadow="never" class="!rounded-2xl !border-none !bg-white max-w-3xl">
      <template #header>
        <div class="flex items-center justify-between">
          <div class="text-sm font-medium text-slate-900">账户信息</div>
          <span v-if="loading" class="text-xs text-slate-400">加载中...</span>
        </div>
      </template>
      <el-skeleton v-if="loading" :rows="5" animated />
      <el-form
        v-else
        :model="form"
        label-width="100px"
        class="max-w-xl profile-form"
        :rules="rules"
        ref="formRef"
      >
        <el-form-item label="用户名">
          <el-input :value="auth.userName || user?.user_name" disabled />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="输入新的邮箱" clearable />
        </el-form-item>
        <el-divider>修改密码（可选，不改可留空）</el-divider>
        <el-form-item label="旧密码" prop="old_password">
          <el-input v-model="form.old_password" type="password" show-password placeholder="输入旧密码" />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="form.new_password" type="password" show-password placeholder="输入新密码，至少6位" />
        </el-form-item>
        <div class="flex gap-3">
          <el-button type="primary" :loading="submitting" @click="handleSubmit">保存</el-button>
          <el-button @click="reset">重置</el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import { ElMessage, ElForm } from 'element-plus';
import { useAuthStore } from '@/stores/auth';
import { getMe, updateMe } from '@/api/user';
import type { UserResponse } from '@/types/api';

const auth = useAuthStore();
const user = ref<UserResponse | null>(null);
const loading = ref(true);

const form = reactive({
  email: '',
  old_password: '',
  new_password: '',
});

const rules = {
  email: [
    { type: 'email', message: '请输入有效邮箱', trigger: 'blur' },
  ],
  new_password: [
    { min: 6, message: '新密码至少 6 位', trigger: 'blur' },
  ],
};

const formRef = ref<InstanceType<typeof ElForm> | null>(null);
const submitting = ref(false);

const reset = (source?: UserResponse | null) => {
  const src = source || user.value;
  form.email = src?.email || auth.email || '';
  form.old_password = '';
  form.new_password = '';
  formRef.value?.clearValidate();
};

const fetchProfile = async () => {
  loading.value = true;
  try {
    const { data } = await getMe();
    user.value = data;
    auth.setUser(data);
    reset(data);
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '获取账户信息失败');
    reset(null);
  } finally {
    loading.value = false;
  }
};

const handleSubmit = async () => {
  if (!formRef.value) return;
  await formRef.value.validate();
  submitting.value = true;
  try {
    const { data } = await updateMe({
      email: form.email || undefined,
      old_password: form.old_password || undefined,
      new_password: form.new_password || undefined,
    });
    auth.setUser(data);
    ElMessage.success('保存成功');
    reset();
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败');
  } finally {
    submitting.value = false;
  }
};

onMounted(() => {
  fetchProfile();
});
</script>

<style scoped>
.profile-form :deep(.el-input__inner),
.profile-form :deep(.el-input__wrapper) {
  border-radius: 10px;
}
.profile-form :deep(.el-form-item__label) {
  font-weight: 500;
  color: #475569;
}
</style>
