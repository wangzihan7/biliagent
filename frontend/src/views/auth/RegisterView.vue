<template>
  <div class="auth-page">
    <el-card class="auth-card">
      <h2 class="title">注册账号</h2>
      <el-form :model="form" :rules="rules" ref="formRef" label-position="top">
        <el-form-item label="用户名" prop="user_name">
          <el-input v-model="form.user_name" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            placeholder="请输入密码"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="onSubmit">注册</el-button>
          <el-button @click="goLogin">返回登录</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
import type { FormInstance, FormRules } from 'element-plus';
import { ElMessage } from 'element-plus';
import { useRouter } from 'vue-router';
import { registerApi } from '@/api/auth';

const router = useRouter();

const formRef = ref<FormInstance>();
const form = reactive({
  user_name: '',
  password: '',
});

const rules: FormRules = {
  user_name: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
};

const loading = ref(false);

const onSubmit = () => {
  if (!formRef.value) return;
  formRef.value.validate(async (valid) => {
    if (!valid) return;
    loading.value = true;
    try {
      await registerApi({
        user_name: form.user_name,
        password: form.password,
        role: 'user',
      });
      ElMessage.success('注册成功，请登录');
      router.push({ name: 'Login' });
    } catch (e: any) {
      const detail = e?.response?.data?.detail;
      ElMessage.error(detail || '注册失败');
    } finally {
      loading.value = false;
    }
  });
};

const goLogin = () => {
  router.push({ name: 'Login' });
};
</script>

<style scoped>
.auth-page {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
}
.auth-card {
  width: 400px;
}
.title {
  text-align: center;
  margin-bottom: 16px;
}
</style>

