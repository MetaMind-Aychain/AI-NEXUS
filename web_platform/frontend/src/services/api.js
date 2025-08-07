/**
 * API服务 - 与后端API通信
 * 
 * 深度集成多AI协作系统的API接口
 */

import axios from 'axios';

// API基础配置
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const API_VERSION = 'v1';

// 创建axios实例
const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/${API_VERSION}`,
  timeout: 30000, // 30秒超时
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器 - 添加认证token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    console.log(`🚀 API请求: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ API请求错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器 - 处理通用错误
apiClient.interceptors.response.use(
  (response) => {
    console.log(`✅ API响应: ${response.config.url} - ${response.status}`);
    return response;
  },
  (error) => {
    console.error('❌ API响应错误:', error);
    
    // 处理认证错误
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      window.location.href = '/login';
      return Promise.reject(new Error('认证失败，请重新登录'));
    }
    
    // 处理服务器错误
    if (error.response?.status >= 500) {
      return Promise.reject(new Error('服务器错误，请稍后重试'));
    }
    
    // 处理网络错误
    if (error.code === 'NETWORK_ERROR') {
      return Promise.reject(new Error('网络连接失败，请检查网络'));
    }
    
    // 其他错误
    const message = error.response?.data?.detail || error.message || '未知错误';
    return Promise.reject(new Error(message));
  }
);

// === 项目管理API ===

/**
 * 创建新项目
 * @param {Object} projectData 项目数据
 * @returns {Promise} 项目创建结果
 */
export const createProject = async (projectData) => {
  const response = await apiClient.post('/projects/create', projectData);
  return response.data;
};

/**
 * 获取用户项目列表
 * @returns {Promise} 项目列表
 */
export const getUserProjects = async () => {
  const response = await apiClient.get('/projects');
  return response.data;
};

/**
 * 获取项目详情
 * @param {string} projectId 项目ID
 * @returns {Promise} 项目详情
 */
export const getProject = async (projectId) => {
  const response = await apiClient.get(`/projects/${projectId}`);
  return response.data;
};

/**
 * 删除项目
 * @param {string} projectId 项目ID
 * @returns {Promise} 删除结果
 */
export const deleteProject = async (projectId) => {
  const response = await apiClient.delete(`/projects/${projectId}`);
  return response.data;
};

// === 文档管理API ===

/**
 * 获取项目文档
 * @param {string} projectId 项目ID
 * @param {number} version 文档版本（可选）
 * @returns {Promise} 项目文档
 */
export const getProjectDocument = async (projectId, version = null) => {
  const url = version 
    ? `/projects/${projectId}/document?version=${version}`
    : `/projects/${projectId}/document`;
  const response = await apiClient.get(url);
  return response.data;
};

/**
 * 更新项目文档
 * @param {string} projectId 项目ID
 * @param {Object} updateData 更新数据
 * @returns {Promise} 更新结果
 */
export const updateProjectDocument = async (projectId, updateData) => {
  const response = await apiClient.post(`/projects/${projectId}/document/update`, updateData);
  return response.data;
};

/**
 * 确认文档并开始开发
 * @param {string} projectId 项目ID
 * @returns {Promise} 开发启动结果
 */
export const confirmDocumentAndStartDevelopment = async (projectId) => {
  const response = await apiClient.post(`/projects/${projectId}/document/confirm`);
  return response.data;
};

// === 开发管理API ===

/**
 * 启动开发流程
 * @param {string} projectId 项目ID
 * @returns {Promise} 开发启动结果
 */
export const startDevelopment = async (projectId) => {
  const response = await apiClient.post(`/projects/${projectId}/development/start`);
  return response.data;
};

/**
 * 获取开发状态
 * @param {string} projectId 项目ID
 * @returns {Promise} 开发状态
 */
export const getDevelopmentStatus = async (projectId) => {
  const response = await apiClient.get(`/projects/${projectId}/development/status`);
  return response.data;
};

/**
 * 获取开发日志
 * @param {string} projectId 项目ID
 * @param {number} limit 日志条数限制
 * @returns {Promise} 开发日志
 */
export const getDevelopmentLogs = async (projectId, limit = 100) => {
  const response = await apiClient.get(`/projects/${projectId}/development/logs?limit=${limit}`);
  return response.data;
};

/**
 * 暂停/恢复开发
 * @param {string} projectId 项目ID
 * @param {string} action pause 或 resume
 * @returns {Promise} 操作结果
 */
export const controlDevelopment = async (projectId, action) => {
  const response = await apiClient.post(`/projects/${projectId}/development/${action}`);
  return response.data;
};

// === 前端预览API ===

/**
 * 获取前端预览
 * @param {string} projectId 项目ID
 * @returns {Promise} 前端预览数据
 */
export const getFrontendPreview = async (projectId) => {
  const response = await apiClient.get(`/projects/${projectId}/frontend/preview`);
  return response.data;
};

/**
 * 提交前端反馈
 * @param {string} projectId 项目ID
 * @param {Object} feedback 反馈数据
 * @returns {Promise} 反馈处理结果
 */
export const submitFrontendFeedback = async (projectId, feedback) => {
  const response = await apiClient.post(`/projects/${projectId}/frontend/feedback`, feedback);
  return response.data;
};

/**
 * 生成新的前端版本
 * @param {string} projectId 项目ID
 * @param {Object} requirements 新要求
 * @returns {Promise} 生成结果
 */
export const generateFrontendVersion = async (projectId, requirements) => {
  const response = await apiClient.post(`/projects/${projectId}/frontend/regenerate`, requirements);
  return response.data;
};

// === 部署管理API ===

/**
 * 部署项目
 * @param {string} projectId 项目ID
 * @param {Object} deploymentConfig 部署配置
 * @returns {Promise} 部署结果
 */
export const deployProject = async (projectId, deploymentConfig) => {
  const response = await apiClient.post(`/projects/${projectId}/deploy`, deploymentConfig);
  return response.data;
};

/**
 * 获取部署状态
 * @param {string} projectId 项目ID
 * @returns {Promise} 部署状态
 */
export const getDeploymentStatus = async (projectId) => {
  const response = await apiClient.get(`/projects/${projectId}/deployment/status`);
  return response.data;
};

/**
 * 获取部署日志
 * @param {string} projectId 项目ID
 * @returns {Promise} 部署日志
 */
export const getDeploymentLogs = async (projectId) => {
  const response = await apiClient.get(`/projects/${projectId}/deployment/logs`);
  return response.data;
};

// === 测试管理API ===

/**
 * 执行最终测试
 * @param {string} projectId 项目ID
 * @returns {Promise} 测试结果
 */
export const runFinalTest = async (projectId) => {
  const response = await apiClient.get(`/projects/${projectId}/final-test`);
  return response.data;
};

/**
 * 获取测试报告
 * @param {string} projectId 项目ID
 * @returns {Promise} 测试报告
 */
export const getTestReport = async (projectId) => {
  const response = await apiClient.get(`/projects/${projectId}/test/report`);
  return response.data;
};

// === AI聊天API ===

/**
 * 与文档AI对话
 * @param {string} projectId 项目ID
 * @param {string} message 用户消息
 * @returns {Promise} AI回复
 */
export const chatWithDocumentAI = async (projectId, message) => {
  const response = await apiClient.post(`/projects/${projectId}/chat/document`, {
    message,
    timestamp: new Date().toISOString()
  });
  return response.data;
};

/**
 * 与前端AI对话
 * @param {string} projectId 项目ID
 * @param {string} message 用户消息
 * @returns {Promise} AI回复
 */
export const chatWithFrontendAI = async (projectId, message) => {
  const response = await apiClient.post(`/projects/${projectId}/chat/frontend`, {
    message,
    timestamp: new Date().toISOString()
  });
  return response.data;
};

// === 系统管理API ===

/**
 * 获取系统状态
 * @returns {Promise} 系统状态
 */
export const getSystemStatus = async () => {
  const response = await apiClient.get('/system/status');
  return response.data;
};

/**
 * 获取AI服务状态
 * @returns {Promise} AI服务状态
 */
export const getAIServicesStatus = async () => {
  const response = await apiClient.get('/system/ai-services');
  return response.data;
};

/**
 * 获取平台统计信息
 * @returns {Promise} 统计信息
 */
export const getPlatformStats = async () => {
  const response = await apiClient.get('/system/stats');
  return response.data;
};

// === 用户管理API ===

/**
 * 用户登录
 * @param {Object} credentials 登录凭据
 * @returns {Promise} 登录结果
 */
export const login = async (credentials) => {
  const response = await apiClient.post('/auth/login', credentials);
  
  // 保存token
  if (response.data.access_token) {
    localStorage.setItem('authToken', response.data.access_token);
  }
  
  return response.data;
};

/**
 * 用户登出
 * @returns {Promise} 登出结果
 */
export const logout = async () => {
  try {
    const response = await apiClient.post('/auth/logout');
    return response.data;
  } finally {
    // 无论请求是否成功都清除本地token
    localStorage.removeItem('authToken');
  }
};

/**
 * 获取当前用户信息
 * @returns {Promise} 用户信息
 */
export const getCurrentUser = async () => {
  const response = await apiClient.get('/auth/me');
  return response.data;
};

// === 文件管理API ===

/**
 * 上传文件
 * @param {string} projectId 项目ID
 * @param {File} file 文件对象
 * @param {Function} onProgress 进度回调
 * @returns {Promise} 上传结果
 */
export const uploadFile = async (projectId, file, onProgress = null) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('project_id', projectId);
  
  const config = {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  };
  
  if (onProgress) {
    config.onUploadProgress = (progressEvent) => {
      const percentCompleted = Math.round(
        (progressEvent.loaded * 100) / progressEvent.total
      );
      onProgress(percentCompleted);
    };
  }
  
  const response = await apiClient.post('/files/upload', formData, config);
  return response.data;
};

/**
 * 下载文件
 * @param {string} fileId 文件ID
 * @returns {Promise} 文件blob
 */
export const downloadFile = async (fileId) => {
  const response = await apiClient.get(`/files/${fileId}/download`, {
    responseType: 'blob',
  });
  return response.data;
};

// === 错误处理工具 ===

/**
 * 处理API错误
 * @param {Error} error 错误对象
 * @param {string} context 错误上下文
 * @returns {string} 用户友好的错误消息
 */
export const handleApiError = (error, context = '') => {
  console.error(`API错误 ${context}:`, error);
  
  if (error.message) {
    return error.message;
  }
  
  if (error.response?.data?.detail) {
    return error.response.data.detail;
  }
  
  return '操作失败，请稍后重试';
};

// === 工具函数 ===

/**
 * 检查API连接状态
 * @returns {Promise<boolean>} 连接状态
 */
export const checkApiConnection = async () => {
  try {
    await apiClient.get('/health');
    return true;
  } catch (error) {
    console.error('API连接检查失败:', error);
    return false;
  }
};

/**
 * 设置认证token
 * @param {string} token 认证token
 */
export const setAuthToken = (token) => {
  localStorage.setItem('authToken', token);
};

/**
 * 清除认证token
 */
export const clearAuthToken = () => {
  localStorage.removeItem('authToken');
};

/**
 * 获取认证token
 * @returns {string|null} 认证token
 */
export const getAuthToken = () => {
  return localStorage.getItem('authToken');
};

// 导出默认API客户端
export default apiClient;