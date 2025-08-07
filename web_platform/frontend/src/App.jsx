/**
 * 多AI协作开发平台 - 主应用组件
 * 
 * 现代化的React前端界面，支持实时通信和动态更新
 */

import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box, Alert, Snackbar } from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// 自定义组件
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import ProjectCreation from './pages/ProjectCreation';
import ProjectManagement from './pages/ProjectManagement';
import DocumentReview from './pages/DocumentReview';
import DevelopmentMonitor from './pages/DevelopmentMonitor';
import FrontendPreview from './pages/FrontendPreview';
import DeploymentPanel from './pages/DeploymentPanel';
import SystemSettings from './pages/SystemSettings';

// 服务和工具
import { WebSocketProvider } from './contexts/WebSocketContext';
import { ProjectProvider } from './contexts/ProjectContext';
import { AuthProvider } from './contexts/AuthContext';
import { NotificationProvider } from './contexts/NotificationContext';

// 样式和主题
import './styles/App.css';

// 创建主题
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
      light: '#42a5f5',
      dark: '#1565c0',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          borderRadius: 12,
        },
      },
    },
  },
});

// React Query客户端
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'info' });

  const handleSidebarToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const showNotification = (message, severity = 'info') => {
    setNotification({ open: true, message, severity });
  };

  const hideNotification = () => {
    setNotification({ ...notification, open: false });
  };

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AuthProvider>
          <NotificationProvider>
            <WebSocketProvider>
              <ProjectProvider>
                <Router>
                  <Box sx={{ display: 'flex', minHeight: '100vh' }}>
                    {/* 侧边栏 */}
                    <Sidebar open={sidebarOpen} onToggle={handleSidebarToggle} />
                    
                    {/* 主内容区域 */}
                    <Box
                      component="main"
                      sx={{
                        flexGrow: 1,
                        transition: 'margin 0.3s',
                        marginLeft: sidebarOpen ? '280px' : '70px',
                        minHeight: '100vh',
                        backgroundColor: 'background.default',
                      }}
                    >
                      {/* 顶部导航 */}
                      <Header onSidebarToggle={handleSidebarToggle} />
                      
                      {/* 路由内容 */}
                      <Box sx={{ p: 3 }}>
                        <Routes>
                          <Route path="/" element={<Navigate to="/dashboard" />} />
                          <Route path="/dashboard" element={<Dashboard />} />
                          <Route path="/create-project" element={<ProjectCreation />} />
                          <Route path="/projects" element={<ProjectManagement />} />
                          <Route path="/projects/:projectId/document" element={<DocumentReview />} />
                          <Route path="/projects/:projectId/development" element={<DevelopmentMonitor />} />
                          <Route path="/projects/:projectId/preview" element={<FrontendPreview />} />
                          <Route path="/projects/:projectId/deploy" element={<DeploymentPanel />} />
                          <Route path="/settings" element={<SystemSettings />} />
                        </Routes>
                      </Box>
                    </Box>
                  </Box>
                  
                  {/* 全局通知 */}
                  <Snackbar
                    open={notification.open}
                    autoHideDuration={6000}
                    onClose={hideNotification}
                    anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
                  >
                    <Alert 
                      onClose={hideNotification} 
                      severity={notification.severity}
                      sx={{ width: '100%' }}
                    >
                      {notification.message}
                    </Alert>
                  </Snackbar>
                </Router>
              </ProjectProvider>
            </WebSocketProvider>
          </NotificationProvider>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;