/**
 * 开发监控页面
 * 
 * 实时监控多AI协作开发过程，深度集成现有的多AI系统
 */

import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  Button,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  Paper,
  Tab,
  Tabs,
  CircularProgress,
  Tooltip,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Code as CodeIcon,
  BugReport as BugIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  SmartToy as AIIcon,
  Visibility as ViewIcon,
  Chat as ChatIcon,
  ExpandMore as ExpandMoreIcon,
  Timeline as TimelineIcon,
  Memory as MemoryIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';
import { Line, Progress } from '@ant-design/charts';

import { useProject } from '../contexts/ProjectContext';
import { useWebSocket } from '../contexts/WebSocketContext';
import { useNotification } from '../contexts/NotificationContext';
import { 
  controlDevelopment, 
  getDevelopmentLogs,
  chatWithDocumentAI 
} from '../services/api';

// AI状态颜色映射
const AI_STATUS_COLORS = {
  idle: 'default',
  working: 'primary',
  waiting: 'warning',
  error: 'error',
  completed: 'success'
};

// AI图标映射
const AI_ICONS = {
  document_ai: '📄',
  development_ai: '💻',
  supervisor_ai: '👁️',
  test_ai: '🧪',
  frontend_ai: '🎨',
  deploy_ai: '🚀'
};

function DevelopmentMonitor() {
  const { projectId } = useParams();
  const { 
    currentProject, 
    developmentStatus, 
    aiStatuses, 
    realTimeUpdates,
    loadProject,
    loadDevelopmentStatus,
    getProjectStatusText,
    getAIStatusText 
  } = useProject();
  
  const { sendAIChat, requestProjectStatus } = useWebSocket();
  const { showNotification } = useNotification();

  // 本地状态
  const [tabValue, setTabValue] = useState(0);
  const [logs, setLogs] = useState([]);
  const [logsLoading, setLogsLoading] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [chatMessage, setChatMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [performanceData, setPerformanceData] = useState([]);
  
  // 引用
  const logsEndRef = useRef(null);
  const refreshIntervalRef = useRef(null);

  // 加载项目数据
  useEffect(() => {
    if (projectId) {
      loadProject(projectId);
      loadDevelopmentStatus(projectId);
      loadDevelopmentLogs();
    }
  }, [projectId]);

  // 自动刷新状态
  useEffect(() => {
    if (projectId && currentProject) {
      // 设置定时刷新
      refreshIntervalRef.current = setInterval(() => {
        requestProjectStatus(projectId);
      }, 10000); // 每10秒刷新一次

      return () => {
        if (refreshIntervalRef.current) {
          clearInterval(refreshIntervalRef.current);
        }
      };
    }
  }, [projectId, currentProject, requestProjectStatus]);

  // 滚动到日志底部
  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, realTimeUpdates]);

  // 更新性能数据
  useEffect(() => {
    if (developmentStatus) {
      const newDataPoint = {
        time: new Date().toLocaleTimeString(),
        progress: developmentStatus.progress || 0,
        aiActivity: Object.values(aiStatuses).filter(status => status === 'working').length,
        memory: Math.random() * 100, // 模拟内存使用
      };
      
      setPerformanceData(prev => [...prev.slice(-19), newDataPoint]); // 保留最近20个数据点
    }
  }, [developmentStatus, aiStatuses]);

  // 加载开发日志
  const loadDevelopmentLogs = async () => {
    if (!projectId) return;
    
    setLogsLoading(true);
    try {
      const logsData = await getDevelopmentLogs(projectId);
      setLogs(logsData.logs || []);
    } catch (error) {
      showNotification(`加载日志失败: ${error.message}`, 'error');
    } finally {
      setLogsLoading(false);
    }
  };

  // 控制开发流程
  const handleDevelopmentControl = async (action) => {
    try {
      await controlDevelopment(projectId, action);
      showNotification(`开发${action === 'pause' ? '暂停' : '恢复'}成功`, 'success');
      loadDevelopmentStatus(projectId);
    } catch (error) {
      showNotification(`操作失败: ${error.message}`, 'error');
    }
  };

  // 发送AI聊天消息
  const handleSendChatMessage = async () => {
    if (!chatMessage.trim()) return;

    const userMessage = {
      role: 'user',
      content: chatMessage,
      timestamp: new Date().toISOString()
    };

    setChatHistory(prev => [...prev, userMessage]);
    setChatMessage('');

    try {
      // 通过WebSocket发送消息（实时性更好）
      const success = sendAIChat(projectId, chatMessage, 'development');
      
      if (!success) {
        // WebSocket失败，使用HTTP API作为备选
        const response = await chatWithDocumentAI(projectId, chatMessage);
        
        const aiMessage = {
          role: 'assistant',
          content: response.reply,
          timestamp: new Date().toISOString()
        };
        
        setChatHistory(prev => [...prev, aiMessage]);
      }
      
    } catch (error) {
      showNotification(`AI对话失败: ${error.message}`, 'error');
    }
  };

  // 渲染AI状态卡片
  const renderAIStatusCards = () => {
    return Object.entries(aiStatuses).map(([aiType, status]) => (
      <Grid item xs={12} sm={6} md={4} key={aiType}>
        <Card sx={{ height: '100%' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" sx={{ mr: 1 }}>
                {AI_ICONS[aiType] || '🤖'}
              </Typography>
              <Typography variant="h6" sx={{ flexGrow: 1 }}>
                {aiType.replace('_', ' ').toUpperCase()}
              </Typography>
              <Chip 
                label={getAIStatusText(status)}
                color={AI_STATUS_COLORS[status]}
                size="small"
              />
            </Box>
            
            <Typography variant="body2" color="text.secondary">
              状态: {getAIStatusText(status)}
            </Typography>
            
            {status === 'working' && (
              <LinearProgress sx={{ mt: 1 }} />
            )}
            
            <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
              <Tooltip title="查看详情">
                <IconButton size="small">
                  <ViewIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="与AI对话">
                <IconButton size="small" onClick={() => setChatOpen(true)}>
                  <ChatIcon />
                </IconButton>
              </Tooltip>
            </Box>
          </CardContent>
        </Card>
      </Grid>
    ));
  };

  // 渲染进度图表
  const renderProgressChart = () => {
    const config = {
      data: performanceData,
      xField: 'time',
      yField: 'progress',
      smooth: true,
      color: '#1976d2',
      point: {
        size: 3,
        shape: 'circle',
      },
      tooltip: {
        formatter: (datum) => ({
          name: '进度',
          value: `${datum.progress.toFixed(1)}%`
        })
      }
    };

    return <Line {...config} height={200} />;
  };

  // 渲染活动监控
  const renderActivityMonitor = () => {
    return (
      <Box>
        <Typography variant="h6" gutterBottom>
          实时活动监控
        </Typography>
        
        <Paper sx={{ p: 2, maxHeight: 400, overflow: 'auto' }}>
          <List dense>
            {realTimeUpdates.slice(0, 20).map((update, index) => (
              <React.Fragment key={index}>
                <ListItem>
                  <ListItemIcon>
                    {update.type === 'progress' && <TimelineIcon color="primary" />}
                    {update.type === 'ai_status' && <AIIcon color="secondary" />}
                    {update.type === 'error' && <ErrorIcon color="error" />}
                    {update.type === 'success' && <CheckIcon color="success" />}
                  </ListItemIcon>
                  <ListItemText
                    primary={update.message}
                    secondary={new Date(update.timestamp).toLocaleString()}
                  />
                </ListItem>
                {index < realTimeUpdates.length - 1 && <Divider />}
              </React.Fragment>
            ))}
            
            {realTimeUpdates.length === 0 && (
              <ListItem>
                <ListItemText
                  primary="暂无活动记录"
                  secondary="系统活动将在此处显示"
                />
              </ListItem>
            )}
            <div ref={logsEndRef} />
          </List>
        </Paper>
      </Box>
    );
  };

  // 渲染开发日志
  const renderDevelopmentLogs = () => {
    return (
      <Box>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">
            开发日志
          </Typography>
          <Button
            startIcon={<RefreshIcon />}
            onClick={loadDevelopmentLogs}
            disabled={logsLoading}
          >
            刷新
          </Button>
        </Box>
        
        <Paper sx={{ p: 2, maxHeight: 500, overflow: 'auto' }}>
          {logsLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
              <CircularProgress />
            </Box>
          ) : (
            <List dense>
              {logs.map((log, index) => (
                <React.Fragment key={index}>
                  <ListItem>
                    <ListItemIcon>
                      {log.level === 'error' && <ErrorIcon color="error" />}
                      {log.level === 'warning' && <WarningIcon color="warning" />}
                      {log.level === 'info' && <CodeIcon color="primary" />}
                      {log.level === 'success' && <CheckIcon color="success" />}
                    </ListItemIcon>
                    <ListItemText
                      primary={log.message}
                      secondary={`${log.source} - ${new Date(log.timestamp).toLocaleString()}`}
                    />
                  </ListItem>
                  {index < logs.length - 1 && <Divider />}
                </React.Fragment>
              ))}
              
              {logs.length === 0 && (
                <ListItem>
                  <ListItemText
                    primary="暂无日志记录"
                    secondary="开发日志将在此处显示"
                  />
                </ListItem>
              )}
            </List>
          )}
        </Paper>
      </Box>
    );
  };

  // Tab面板内容
  const renderTabContent = () => {
    switch (tabValue) {
      case 0: // 概览
        return (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    开发进度
                  </Typography>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      当前阶段: {getProjectStatusText(currentProject?.status)}
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={developmentStatus?.progress || 0}
                      sx={{ mt: 1, height: 8, borderRadius: 4 }}
                    />
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      {(developmentStatus?.progress || 0).toFixed(1)}% 完成
                    </Typography>
                  </Box>
                  
                  {developmentStatus?.current_stage_details && (
                    <Typography variant="body2">
                      当前任务: {developmentStatus.current_stage_details.description}
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
            
            {/* AI状态卡片 */}
            {renderAIStatusCards()}
            
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    进度趋势
                  </Typography>
                  {renderProgressChart()}
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  {renderActivityMonitor()}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        );
        
      case 1: // AI状态
        return (
          <Grid container spacing={3}>
            {renderAIStatusCards()}
            
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    AI协作流程
                  </Typography>
                  
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mt: 2 }}>
                    {Object.entries(aiStatuses).map(([aiType, status], index) => (
                      <Box key={aiType} sx={{ display: 'flex', alignItems: 'center' }}>
                        <Box
                          sx={{
                            width: 40,
                            height: 40,
                            borderRadius: '50%',
                            backgroundColor: status === 'working' ? 'primary.main' : 'grey.300',
                            color: 'white',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: 20
                          }}
                        >
                          {AI_ICONS[aiType]}
                        </Box>
                        
                        {index < Object.keys(aiStatuses).length - 1 && (
                          <Box
                            sx={{
                              width: 30,
                              height: 2,
                              backgroundColor: 'grey.300',
                              mx: 1
                            }}
                          />
                        )}
                      </Box>
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        );
        
      case 2: // 日志
        return (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              {renderDevelopmentLogs()}
            </Grid>
          </Grid>
        );
        
      case 3: // 性能
        return (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    系统性能
                  </Typography>
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="body2">CPU使用率</Typography>
                    <LinearProgress variant="determinate" value={65} sx={{ mt: 1 }} />
                    
                    <Typography variant="body2" sx={{ mt: 2 }}>内存使用</Typography>
                    <LinearProgress variant="determinate" value={45} sx={{ mt: 1 }} />
                    
                    <Typography variant="body2" sx={{ mt: 2 }}>网络活动</Typography>
                    <LinearProgress variant="determinate" value={30} sx={{ mt: 1 }} />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    AI活动统计
                  </Typography>
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="body2">
                      活跃AI数量: {Object.values(aiStatuses).filter(s => s === 'working').length}
                    </Typography>
                    <Typography variant="body2">
                      待机AI数量: {Object.values(aiStatuses).filter(s => s === 'idle').length}
                    </Typography>
                    <Typography variant="body2">
                      错误AI数量: {Object.values(aiStatuses).filter(s => s === 'error').length}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        );
        
      default:
        return null;
    }
  };

  if (!currentProject) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>加载项目信息...</Typography>
      </Box>
    );
  }

  return (
    <Box>
      {/* 页面标题和控制按钮 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          开发监控 - {currentProject.name}
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            startIcon={<PlayIcon />}
            onClick={() => handleDevelopmentControl('resume')}
            disabled={developmentStatus?.status === 'running'}
            color="success"
          >
            继续
          </Button>
          <Button
            startIcon={<PauseIcon />}
            onClick={() => handleDevelopmentControl('pause')}
            disabled={developmentStatus?.status !== 'running'}
            color="warning"
          >
            暂停
          </Button>
          <Button
            startIcon={<ChatIcon />}
            onClick={() => setChatOpen(true)}
            color="primary"
          >
            AI对话
          </Button>
          <Button
            startIcon={<RefreshIcon />}
            onClick={() => {
              loadProject(projectId);
              loadDevelopmentStatus(projectId);
            }}
          >
            刷新
          </Button>
        </Box>
      </Box>

      {/* 状态摘要 */}
      <Alert severity="info" sx={{ mb: 3 }}>
        项目状态: {getProjectStatusText(currentProject.status)} | 
        开发进度: {(developmentStatus?.progress || 0).toFixed(1)}% | 
        活跃AI: {Object.values(aiStatuses).filter(s => s === 'working').length}个
      </Alert>

      {/* 选项卡 */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
          <Tab label="概览" />
          <Tab label="AI状态" />
          <Tab label="开发日志" />
          <Tab label="性能监控" />
        </Tabs>
      </Paper>

      {/* 选项卡内容 */}
      {renderTabContent()}

      {/* AI对话弹窗 */}
      <Dialog open={chatOpen} onClose={() => setChatOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>与AI对话</DialogTitle>
        <DialogContent>
          <Box sx={{ height: 400, overflow: 'auto', mb: 2, p: 1, backgroundColor: 'grey.50' }}>
            {chatHistory.map((message, index) => (
              <Box key={index} sx={{ mb: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  {message.role === 'user' ? '您' : 'AI'} - {new Date(message.timestamp).toLocaleTimeString()}
                </Typography>
                <Paper sx={{ p: 1, backgroundColor: message.role === 'user' ? 'primary.light' : 'white' }}>
                  <Typography variant="body2">
                    {message.content}
                  </Typography>
                </Paper>
              </Box>
            ))}
          </Box>
          
          <TextField
            fullWidth
            multiline
            rows={3}
            placeholder="输入您的问题或指令..."
            value={chatMessage}
            onChange={(e) => setChatMessage(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendChatMessage();
              }
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setChatOpen(false)}>关闭</Button>
          <Button onClick={handleSendChatMessage} variant="contained">
            发送
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default DevelopmentMonitor;