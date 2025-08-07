/**
 * 项目上下文 - 项目状态管理
 * 
 * 深度集成多AI协作系统的项目管理状态
 */

import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { useWebSocket } from './WebSocketContext';
import { useNotification } from './NotificationContext';
import { 
  getUserProjects, 
  getProject, 
  getDevelopmentStatus,
  getFrontendPreview,
  getDeploymentStatus 
} from '../services/api';

const ProjectContext = createContext();

export const useProject = () => {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
};

// 项目状态类型
const PROJECT_STATUS = {
  DOCUMENT_GENERATION: 'document_generation',
  DOCUMENT_REVIEW: 'document_review', 
  DOCUMENT_CONFIRMED: 'document_confirmed',
  DEVELOPMENT_STARTED: 'development_started',
  BACKEND_DEVELOPMENT: 'backend_development',
  TESTING_BACKEND: 'testing_backend',
  FRONTEND_DEVELOPMENT: 'frontend_development',
  FRONTEND_REVIEW: 'frontend_review',
  INTEGRATION: 'integration',
  FINAL_TESTING: 'final_testing',
  DEPLOYING: 'deploying',
  DEPLOYED: 'deployed',
  COMPLETED: 'completed',
  FAILED: 'failed'
};

// AI状态类型
const AI_STATUS = {
  IDLE: 'idle',
  WORKING: 'working',
  WAITING: 'waiting',
  ERROR: 'error',
  COMPLETED: 'completed'
};

// 初始状态
const initialState = {
  // 项目列表
  projects: [],
  projectsLoading: false,
  projectsError: null,
  
  // 当前项目
  currentProject: null,
  currentProjectLoading: false,
  currentProjectError: null,
  
  // 开发状态
  developmentStatus: null,
  developmentLoading: false,
  developmentError: null,
  
  // 前端预览
  frontendPreview: null,
  frontendPreviewLoading: false,
  frontendPreviewError: null,
  
  // 部署状态
  deploymentStatus: null,
  deploymentLoading: false,
  deploymentError: null,
  
  // AI状态
  aiStatuses: {
    document_ai: AI_STATUS.IDLE,
    development_ai: AI_STATUS.IDLE,
    supervisor_ai: AI_STATUS.IDLE,
    test_ai: AI_STATUS.IDLE,
    frontend_ai: AI_STATUS.IDLE,
    deploy_ai: AI_STATUS.IDLE
  },
  
  // 实时更新
  realTimeUpdates: [],
  
  // 选中的项目ID
  selectedProjectId: null,
};

// Action类型
const ActionTypes = {
  // 项目列表
  SET_PROJECTS_LOADING: 'SET_PROJECTS_LOADING',
  SET_PROJECTS_SUCCESS: 'SET_PROJECTS_SUCCESS',
  SET_PROJECTS_ERROR: 'SET_PROJECTS_ERROR',
  ADD_PROJECT: 'ADD_PROJECT',
  UPDATE_PROJECT: 'UPDATE_PROJECT',
  REMOVE_PROJECT: 'REMOVE_PROJECT',
  
  // 当前项目
  SET_CURRENT_PROJECT_LOADING: 'SET_CURRENT_PROJECT_LOADING',
  SET_CURRENT_PROJECT_SUCCESS: 'SET_CURRENT_PROJECT_SUCCESS',
  SET_CURRENT_PROJECT_ERROR: 'SET_CURRENT_PROJECT_ERROR',
  CLEAR_CURRENT_PROJECT: 'CLEAR_CURRENT_PROJECT',
  
  // 开发状态
  SET_DEVELOPMENT_STATUS_LOADING: 'SET_DEVELOPMENT_STATUS_LOADING',
  SET_DEVELOPMENT_STATUS_SUCCESS: 'SET_DEVELOPMENT_STATUS_SUCCESS',
  SET_DEVELOPMENT_STATUS_ERROR: 'SET_DEVELOPMENT_STATUS_ERROR',
  UPDATE_DEVELOPMENT_PROGRESS: 'UPDATE_DEVELOPMENT_PROGRESS',
  
  // 前端预览
  SET_FRONTEND_PREVIEW_LOADING: 'SET_FRONTEND_PREVIEW_LOADING',
  SET_FRONTEND_PREVIEW_SUCCESS: 'SET_FRONTEND_PREVIEW_SUCCESS',
  SET_FRONTEND_PREVIEW_ERROR: 'SET_FRONTEND_PREVIEW_ERROR',
  
  // 部署状态
  SET_DEPLOYMENT_STATUS_LOADING: 'SET_DEPLOYMENT_STATUS_LOADING',
  SET_DEPLOYMENT_STATUS_SUCCESS: 'SET_DEPLOYMENT_STATUS_SUCCESS',
  SET_DEPLOYMENT_STATUS_ERROR: 'SET_DEPLOYMENT_STATUS_ERROR',
  
  // AI状态
  UPDATE_AI_STATUS: 'UPDATE_AI_STATUS',
  
  // 实时更新
  ADD_REAL_TIME_UPDATE: 'ADD_REAL_TIME_UPDATE',
  CLEAR_REAL_TIME_UPDATES: 'CLEAR_REAL_TIME_UPDATES',
  
  // 选中项目
  SET_SELECTED_PROJECT: 'SET_SELECTED_PROJECT',
};

// Reducer
const projectReducer = (state, action) => {
  switch (action.type) {
    case ActionTypes.SET_PROJECTS_LOADING:
      return { ...state, projectsLoading: true, projectsError: null };
    
    case ActionTypes.SET_PROJECTS_SUCCESS:
      return { 
        ...state, 
        projects: action.payload, 
        projectsLoading: false, 
        projectsError: null 
      };
    
    case ActionTypes.SET_PROJECTS_ERROR:
      return { 
        ...state, 
        projectsLoading: false, 
        projectsError: action.payload 
      };
    
    case ActionTypes.ADD_PROJECT:
      return { 
        ...state, 
        projects: [action.payload, ...state.projects] 
      };
    
    case ActionTypes.UPDATE_PROJECT:
      return {
        ...state,
        projects: state.projects.map(project => 
          project.id === action.payload.id ? action.payload : project
        ),
        currentProject: state.currentProject?.id === action.payload.id 
          ? action.payload 
          : state.currentProject
      };
    
    case ActionTypes.REMOVE_PROJECT:
      return {
        ...state,
        projects: state.projects.filter(project => project.id !== action.payload),
        currentProject: state.currentProject?.id === action.payload 
          ? null 
          : state.currentProject
      };
    
    case ActionTypes.SET_CURRENT_PROJECT_LOADING:
      return { ...state, currentProjectLoading: true, currentProjectError: null };
    
    case ActionTypes.SET_CURRENT_PROJECT_SUCCESS:
      return { 
        ...state, 
        currentProject: action.payload, 
        currentProjectLoading: false, 
        currentProjectError: null 
      };
    
    case ActionTypes.SET_CURRENT_PROJECT_ERROR:
      return { 
        ...state, 
        currentProjectLoading: false, 
        currentProjectError: action.payload 
      };
    
    case ActionTypes.CLEAR_CURRENT_PROJECT:
      return { 
        ...state, 
        currentProject: null,
        developmentStatus: null,
        frontendPreview: null,
        deploymentStatus: null
      };
    
    case ActionTypes.SET_DEVELOPMENT_STATUS_LOADING:
      return { ...state, developmentLoading: true, developmentError: null };
    
    case ActionTypes.SET_DEVELOPMENT_STATUS_SUCCESS:
      return { 
        ...state, 
        developmentStatus: action.payload, 
        developmentLoading: false, 
        developmentError: null 
      };
    
    case ActionTypes.SET_DEVELOPMENT_STATUS_ERROR:
      return { 
        ...state, 
        developmentLoading: false, 
        developmentError: action.payload 
      };
    
    case ActionTypes.UPDATE_DEVELOPMENT_PROGRESS:
      return {
        ...state,
        developmentStatus: {
          ...state.developmentStatus,
          ...action.payload
        }
      };
    
    case ActionTypes.SET_FRONTEND_PREVIEW_LOADING:
      return { ...state, frontendPreviewLoading: true, frontendPreviewError: null };
    
    case ActionTypes.SET_FRONTEND_PREVIEW_SUCCESS:
      return { 
        ...state, 
        frontendPreview: action.payload, 
        frontendPreviewLoading: false, 
        frontendPreviewError: null 
      };
    
    case ActionTypes.SET_FRONTEND_PREVIEW_ERROR:
      return { 
        ...state, 
        frontendPreviewLoading: false, 
        frontendPreviewError: action.payload 
      };
    
    case ActionTypes.SET_DEPLOYMENT_STATUS_LOADING:
      return { ...state, deploymentLoading: true, deploymentError: null };
    
    case ActionTypes.SET_DEPLOYMENT_STATUS_SUCCESS:
      return { 
        ...state, 
        deploymentStatus: action.payload, 
        deploymentLoading: false, 
        deploymentError: null 
      };
    
    case ActionTypes.SET_DEPLOYMENT_STATUS_ERROR:
      return { 
        ...state, 
        deploymentLoading: false, 
        deploymentError: action.payload 
      };
    
    case ActionTypes.UPDATE_AI_STATUS:
      return {
        ...state,
        aiStatuses: {
          ...state.aiStatuses,
          [action.payload.aiType]: action.payload.status
        }
      };
    
    case ActionTypes.ADD_REAL_TIME_UPDATE:
      return {
        ...state,
        realTimeUpdates: [
          action.payload,
          ...state.realTimeUpdates.slice(0, 99) // 保留最近100条更新
        ]
      };
    
    case ActionTypes.CLEAR_REAL_TIME_UPDATES:
      return { ...state, realTimeUpdates: [] };
    
    case ActionTypes.SET_SELECTED_PROJECT:
      return { ...state, selectedProjectId: action.payload };
    
    default:
      return state;
  }
};

export const ProjectProvider = ({ children }) => {
  const [state, dispatch] = useReducer(projectReducer, initialState);
  const { registerMessageHandler, subscribeToProject, unsubscribeFromProject } = useWebSocket();
  const { showNotification } = useNotification();

  // 注册WebSocket消息处理器
  useEffect(() => {
    const handlers = [
      // 项目创建成功
      registerMessageHandler('project_created', (data) => {
        dispatch({ type: ActionTypes.ADD_PROJECT, payload: data.project });
        showNotification('项目创建成功', 'success');
      }),
      
      // 开发进度更新
      registerMessageHandler('progress_update', (data) => {
        dispatch({ 
          type: ActionTypes.UPDATE_DEVELOPMENT_PROGRESS, 
          payload: data.progress 
        });
        
        dispatch({
          type: ActionTypes.ADD_REAL_TIME_UPDATE,
          payload: {
            type: 'progress',
            message: `开发进度更新: ${data.progress.stage}`,
            timestamp: new Date().toISOString(),
            data: data.progress
          }
        });
      }),
      
      // AI状态更新
      registerMessageHandler('ai_status_update', (data) => {
        dispatch({
          type: ActionTypes.UPDATE_AI_STATUS,
          payload: {
            aiType: data.ai_type,
            status: data.status
          }
        });
        
        dispatch({
          type: ActionTypes.ADD_REAL_TIME_UPDATE,
          payload: {
            type: 'ai_status',
            message: `${data.ai_type} 状态: ${data.status}`,
            timestamp: new Date().toISOString(),
            data: data
          }
        });
      }),
      
      // 前端预览就绪
      registerMessageHandler('frontend_preview_ready', (data) => {
        showNotification('前端预览已生成', 'success');
        
        // 重新加载前端预览
        if (state.currentProject?.id === data.project_id) {
          loadFrontendPreview(data.project_id);
        }
      }),
      
      // 开发完成
      registerMessageHandler('development_completed', (data) => {
        dispatch({
          type: ActionTypes.UPDATE_DEVELOPMENT_PROGRESS,
          payload: { status: 'completed' }
        });
        
        showNotification('开发已完成', 'success');
      }),
      
      // 部署完成
      registerMessageHandler('deployment_completed', (data) => {
        dispatch({
          type: ActionTypes.SET_DEPLOYMENT_STATUS_SUCCESS,
          payload: data.deployment_status
        });
        
        showNotification('部署完成', 'success');
      }),
      
      // 测试完成
      registerMessageHandler('final_test_completed', (data) => {
        showNotification(`最终测试完成，评分: ${data.result.score}`, 'info');
      })
    ];
    
    // 返回清理函数
    return () => {
      handlers.forEach(cleanup => cleanup());
    };
  }, [registerMessageHandler, showNotification, state.currentProject?.id]);

  // === Action Creators ===

  // 加载项目列表
  const loadProjects = async () => {
    dispatch({ type: ActionTypes.SET_PROJECTS_LOADING });
    
    try {
      const projects = await getUserProjects();
      dispatch({ type: ActionTypes.SET_PROJECTS_SUCCESS, payload: projects });
    } catch (error) {
      dispatch({ type: ActionTypes.SET_PROJECTS_ERROR, payload: error.message });
    }
  };

  // 选择项目
  const selectProject = async (projectId) => {
    if (projectId === state.selectedProjectId) return;
    
    // 取消之前项目的订阅
    if (state.selectedProjectId) {
      unsubscribeFromProject(state.selectedProjectId);
    }
    
    dispatch({ type: ActionTypes.SET_SELECTED_PROJECT, payload: projectId });
    
    if (projectId) {
      // 订阅新项目
      subscribeToProject(projectId);
      
      // 加载项目详情
      await loadProject(projectId);
    } else {
      dispatch({ type: ActionTypes.CLEAR_CURRENT_PROJECT });
    }
  };

  // 加载项目详情
  const loadProject = async (projectId) => {
    dispatch({ type: ActionTypes.SET_CURRENT_PROJECT_LOADING });
    
    try {
      const project = await getProject(projectId);
      dispatch({ type: ActionTypes.SET_CURRENT_PROJECT_SUCCESS, payload: project });
      
      // 根据项目状态加载相应数据
      await loadProjectRelatedData(project);
      
    } catch (error) {
      dispatch({ type: ActionTypes.SET_CURRENT_PROJECT_ERROR, payload: error.message });
    }
  };

  // 加载项目相关数据
  const loadProjectRelatedData = async (project) => {
    const projectId = project.id;
    
    try {
      // 如果项目正在开发，加载开发状态
      if ([
        PROJECT_STATUS.DEVELOPMENT_STARTED,
        PROJECT_STATUS.BACKEND_DEVELOPMENT,
        PROJECT_STATUS.TESTING_BACKEND,
        PROJECT_STATUS.FRONTEND_DEVELOPMENT,
        PROJECT_STATUS.INTEGRATION
      ].includes(project.status)) {
        await loadDevelopmentStatus(projectId);
      }
      
      // 如果项目有前端预览，加载前端预览
      if ([
        PROJECT_STATUS.FRONTEND_DEVELOPMENT,
        PROJECT_STATUS.FRONTEND_REVIEW,
        PROJECT_STATUS.INTEGRATION,
        PROJECT_STATUS.FINAL_TESTING,
        PROJECT_STATUS.DEPLOYING,
        PROJECT_STATUS.DEPLOYED,
        PROJECT_STATUS.COMPLETED
      ].includes(project.status)) {
        await loadFrontendPreview(projectId);
      }
      
      // 如果项目正在部署或已部署，加载部署状态
      if ([
        PROJECT_STATUS.DEPLOYING,
        PROJECT_STATUS.DEPLOYED,
        PROJECT_STATUS.COMPLETED
      ].includes(project.status)) {
        await loadDeploymentStatus(projectId);
      }
      
    } catch (error) {
      console.error('加载项目相关数据失败:', error);
    }
  };

  // 加载开发状态
  const loadDevelopmentStatus = async (projectId) => {
    dispatch({ type: ActionTypes.SET_DEVELOPMENT_STATUS_LOADING });
    
    try {
      const status = await getDevelopmentStatus(projectId);
      dispatch({ type: ActionTypes.SET_DEVELOPMENT_STATUS_SUCCESS, payload: status });
    } catch (error) {
      dispatch({ type: ActionTypes.SET_DEVELOPMENT_STATUS_ERROR, payload: error.message });
    }
  };

  // 加载前端预览
  const loadFrontendPreview = async (projectId) => {
    dispatch({ type: ActionTypes.SET_FRONTEND_PREVIEW_LOADING });
    
    try {
      const preview = await getFrontendPreview(projectId);
      dispatch({ type: ActionTypes.SET_FRONTEND_PREVIEW_SUCCESS, payload: preview });
    } catch (error) {
      dispatch({ type: ActionTypes.SET_FRONTEND_PREVIEW_ERROR, payload: error.message });
    }
  };

  // 加载部署状态
  const loadDeploymentStatus = async (projectId) => {
    dispatch({ type: ActionTypes.SET_DEPLOYMENT_STATUS_LOADING });
    
    try {
      const status = await getDeploymentStatus(projectId);
      dispatch({ type: ActionTypes.SET_DEPLOYMENT_STATUS_SUCCESS, payload: status });
    } catch (error) {
      dispatch({ type: ActionTypes.SET_DEPLOYMENT_STATUS_ERROR, payload: error.message });
    }
  };

  // 更新项目
  const updateProject = (project) => {
    dispatch({ type: ActionTypes.UPDATE_PROJECT, payload: project });
  };

  // 添加项目
  const addProject = (project) => {
    dispatch({ type: ActionTypes.ADD_PROJECT, payload: project });
  };

  // 删除项目
  const removeProject = (projectId) => {
    dispatch({ type: ActionTypes.REMOVE_PROJECT, payload: projectId });
    
    if (state.selectedProjectId === projectId) {
      dispatch({ type: ActionTypes.SET_SELECTED_PROJECT, payload: null });
    }
  };

  // 清除实时更新
  const clearRealTimeUpdates = () => {
    dispatch({ type: ActionTypes.CLEAR_REAL_TIME_UPDATES });
  };

  // 获取项目状态文本
  const getProjectStatusText = (status) => {
    const statusMap = {
      [PROJECT_STATUS.DOCUMENT_GENERATION]: '生成文档中',
      [PROJECT_STATUS.DOCUMENT_REVIEW]: '文档审核中',
      [PROJECT_STATUS.DOCUMENT_CONFIRMED]: '文档已确认',
      [PROJECT_STATUS.DEVELOPMENT_STARTED]: '开发已启动',
      [PROJECT_STATUS.BACKEND_DEVELOPMENT]: '后端开发中',
      [PROJECT_STATUS.TESTING_BACKEND]: '后端测试中',
      [PROJECT_STATUS.FRONTEND_DEVELOPMENT]: '前端开发中',
      [PROJECT_STATUS.FRONTEND_REVIEW]: '前端审核中',
      [PROJECT_STATUS.INTEGRATION]: '前后端集成中',
      [PROJECT_STATUS.FINAL_TESTING]: '最终测试中',
      [PROJECT_STATUS.DEPLOYING]: '部署中',
      [PROJECT_STATUS.DEPLOYED]: '已部署',
      [PROJECT_STATUS.COMPLETED]: '已完成',
      [PROJECT_STATUS.FAILED]: '失败'
    };
    
    return statusMap[status] || '未知状态';
  };

  // 获取AI状态文本
  const getAIStatusText = (status) => {
    const statusMap = {
      [AI_STATUS.IDLE]: '空闲',
      [AI_STATUS.WORKING]: '工作中',
      [AI_STATUS.WAITING]: '等待中',
      [AI_STATUS.ERROR]: '错误',
      [AI_STATUS.COMPLETED]: '已完成'
    };
    
    return statusMap[status] || '未知';
  };

  const contextValue = {
    // 状态
    ...state,
    
    // Actions
    loadProjects,
    selectProject,
    loadProject,
    loadDevelopmentStatus,
    loadFrontendPreview,
    loadDeploymentStatus,
    updateProject,
    addProject,
    removeProject,
    clearRealTimeUpdates,
    
    // 工具函数
    getProjectStatusText,
    getAIStatusText,
    
    // 常量
    PROJECT_STATUS,
    AI_STATUS,
  };

  return (
    <ProjectContext.Provider value={contextValue}>
      {children}
    </ProjectContext.Provider>
  );
};