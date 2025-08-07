/**
 * 项目创建页面
 * 
 * 用户输入项目需求，说明要开发什么样的网站和功能
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Grid,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Paper,
  Alert,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Add as AddIcon,
  Description as DescriptionIcon,
  Code as CodeIcon,
  Domain as DomainIcon,
  Timeline as TimelineIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';

import { useNotification } from '../contexts/NotificationContext';
import { useWebSocket } from '../contexts/WebSocketContext';
import { createProject } from '../services/api';

const PROJECT_TYPES = [
  { value: 'web_application', label: 'Web应用程序' },
  { value: 'e_commerce', label: '电商网站' },
  { value: 'blog_cms', label: '博客/内容管理' },
  { value: 'portfolio', label: '作品集网站' },
  { value: 'business_website', label: '企业官网' },
  { value: 'api_service', label: 'API服务' },
  { value: 'dashboard', label: '管理后台' },
  { value: 'landing_page', label: '落地页' },
  { value: 'other', label: '其他' },
];

const TECH_STACKS = [
  { value: 'react_node', label: 'React + Node.js' },
  { value: 'vue_express', label: 'Vue.js + Express' },
  { value: 'react_python', label: 'React + Python' },
  { value: 'nextjs', label: 'Next.js 全栈' },
  { value: 'django', label: 'Django + HTML' },
  { value: 'flask', label: 'Flask + HTML' },
  { value: 'spring_react', label: 'Spring Boot + React' },
  { value: 'auto', label: '让AI自动选择' },
];

const COMPLEXITY_LEVELS = [
  { value: 'simple', label: '简单', description: '基础功能，快速开发' },
  { value: 'medium', label: '中等', description: '标准功能，平衡性能' },
  { value: 'complex', label: '复杂', description: '高级功能，完整体验' },
];

const steps = [
  '基本信息',
  '功能需求',
  '技术配置',
  '确认创建'
];

function ProjectCreation() {
  const navigate = useNavigate();
  const { showNotification } = useNotification();
  const { subscribeToProject } = useWebSocket();

  // 步骤控制
  const [activeStep, setActiveStep] = useState(0);
  const [completed, setCompleted] = useState(false);
  
  // 表单数据
  const [formData, setFormData] = useState({
    // 基本信息
    name: '',
    description: '',
    projectType: 'web_application',
    complexityLevel: 'medium',
    
    // 功能需求
    features: [],
    customFeatures: '',
    targetAudience: '',
    specialRequirements: [],
    
    // 技术配置
    technologyPreference: 'auto',
    domainPreference: '',
    expectedTimeline: '',
    budgetRange: '',
    
    // 高级选项
    includeAdmin: false,
    includeMobile: false,
    includeAnalytics: false,
    includeSEO: true,
  });

  // 常用功能列表
  const [availableFeatures] = useState([
    '用户注册登录',
    '个人资料管理',
    '内容发布',
    '搜索功能',
    '评论系统',
    '文件上传',
    '在线支付',
    '邮件通知',
    '数据导出',
    '多语言支持',
    '响应式设计',
    '暗黑模式',
  ]);

  // 特殊需求
  const [specialRequirementOptions] = useState([
    '高并发支持',
    '实时通信',
    '第三方集成',
    '数据分析',
    '安全加密',
    '国际化',
    '离线支持',
    'API接口',
  ]);

  // 创建项目的API调用
  const createProjectMutation = useMutation({
    mutationFn: createProject,
    onSuccess: (data) => {
      console.log('项目创建成功:', data);
      setCompleted(true);
      
      // 订阅项目更新
      if (data.project_id) {
        subscribeToProject(data.project_id);
      }
      
      showNotification('项目创建成功！', 'success');
      
      // 3秒后跳转到项目管理页面
      setTimeout(() => {
        navigate(`/projects/${data.project_id}/document`);
      }, 3000);
    },
    onError: (error) => {
      console.error('项目创建失败:', error);
      showNotification(`项目创建失败: ${error.message}`, 'error');
    },
  });

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleFeatureToggle = (feature) => {
    setFormData(prev => ({
      ...prev,
      features: prev.features.includes(feature)
        ? prev.features.filter(f => f !== feature)
        : [...prev.features, feature]
    }));
  };

  const handleSpecialRequirementToggle = (requirement) => {
    setFormData(prev => ({
      ...prev,
      specialRequirements: prev.specialRequirements.includes(requirement)
        ? prev.specialRequirements.filter(r => r !== requirement)
        : [...prev.specialRequirements, requirement]
    }));
  };

  const handleNext = () => {
    if (activeStep < steps.length - 1) {
      setActiveStep(activeStep + 1);
    }
  };

  const handleBack = () => {
    if (activeStep > 0) {
      setActiveStep(activeStep - 1);
    }
  };

  const handleSubmit = () => {
    // 构建项目创建请求
    const projectRequest = {
      description: formData.description,
      requirements: {
        project_type: formData.projectType,
        complexity_level: formData.complexityLevel,
        features: formData.features,
        custom_features: formData.customFeatures,
        target_audience: formData.targetAudience,
        special_requirements: formData.specialRequirements,
        include_admin: formData.includeAdmin,
        include_mobile: formData.includeMobile,
        include_analytics: formData.includeAnalytics,
        include_seo: formData.includeSEO,
      },
      technology_preference: formData.technologyPreference,
      domain_preference: formData.domainPreference,
    };

    console.log('提交项目创建请求:', projectRequest);
    createProjectMutation.mutate(projectRequest);
  };

  const isStepValid = (step) => {
    switch (step) {
      case 0: // 基本信息
        return formData.name.trim() && formData.description.trim().length >= 10;
      case 1: // 功能需求
        return formData.features.length > 0 || formData.customFeatures.trim();
      case 2: // 技术配置
        return true; // 技术配置都有默认值
      case 3: // 确认创建
        return true;
      default:
        return false;
    }
  };

  const renderStepContent = (step) => {
    switch (step) {
      case 0:
        return (
          <Box sx={{ mt: 2 }}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="项目名称"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  placeholder="例如：我的在线商城"
                  required
                />
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  label="项目描述"
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  placeholder="详细描述您想要开发的网站功能和特点..."
                  required
                  helperText="请尽可能详细地描述您的需求，这将帮助AI更好地理解和实现您的想法"
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>项目类型</InputLabel>
                  <Select
                    value={formData.projectType}
                    onChange={(e) => handleInputChange('projectType', e.target.value)}
                    label="项目类型"
                  >
                    {PROJECT_TYPES.map((type) => (
                      <MenuItem key={type.value} value={type.value}>
                        {type.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>复杂度</InputLabel>
                  <Select
                    value={formData.complexityLevel}
                    onChange={(e) => handleInputChange('complexityLevel', e.target.value)}
                    label="复杂度"
                  >
                    {COMPLEXITY_LEVELS.map((level) => (
                      <MenuItem key={level.value} value={level.value}>
                        <Box>
                          <Typography variant="body1">{level.label}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {level.description}
                          </Typography>
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </Box>
        );

      case 1:
        return (
          <Box sx={{ mt: 2 }}>
            <Typography variant="h6" gutterBottom>
              选择功能模块
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              选择您需要的功能，也可以在下方描述自定义功能
            </Typography>
            
            <Grid container spacing={1} sx={{ mb: 3 }}>
              {availableFeatures.map((feature) => (
                <Grid item key={feature}>
                  <Chip
                    label={feature}
                    clickable
                    color={formData.features.includes(feature) ? 'primary' : 'default'}
                    onClick={() => handleFeatureToggle(feature)}
                    variant={formData.features.includes(feature) ? 'filled' : 'outlined'}
                  />
                </Grid>
              ))}
            </Grid>
            
            <TextField
              fullWidth
              multiline
              rows={3}
              label="自定义功能需求"
              value={formData.customFeatures}
              onChange={(e) => handleInputChange('customFeatures', e.target.value)}
              placeholder="描述上面列表中没有的特殊功能需求..."
              sx={{ mb: 3 }}
            />
            
            <TextField
              fullWidth
              label="目标用户群体"
              value={formData.targetAudience}
              onChange={(e) => handleInputChange('targetAudience', e.target.value)}
              placeholder="例如：企业用户、个人消费者、学生群体等"
              sx={{ mb: 3 }}
            />
            
            <Typography variant="h6" gutterBottom>
              特殊技术需求
            </Typography>
            <Grid container spacing={1}>
              {specialRequirementOptions.map((requirement) => (
                <Grid item key={requirement}>
                  <Chip
                    label={requirement}
                    clickable
                    color={formData.specialRequirements.includes(requirement) ? 'secondary' : 'default'}
                    onClick={() => handleSpecialRequirementToggle(requirement)}
                    variant={formData.specialRequirements.includes(requirement) ? 'filled' : 'outlined'}
                  />
                </Grid>
              ))}
            </Grid>
          </Box>
        );

      case 2:
        return (
          <Box sx={{ mt: 2 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>技术栈偏好</InputLabel>
                  <Select
                    value={formData.technologyPreference}
                    onChange={(e) => handleInputChange('technologyPreference', e.target.value)}
                    label="技术栈偏好"
                  >
                    {TECH_STACKS.map((stack) => (
                      <MenuItem key={stack.value} value={stack.value}>
                        {stack.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="域名偏好"
                  value={formData.domainPreference}
                  onChange={(e) => handleInputChange('domainPreference', e.target.value)}
                  placeholder="例如：mywebsite.com"
                  helperText="可选，用于部署配置"
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="预期完成时间"
                  value={formData.expectedTimeline}
                  onChange={(e) => handleInputChange('expectedTimeline', e.target.value)}
                  placeholder="例如：1周内、尽快"
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="预算范围"
                  value={formData.budgetRange}
                  onChange={(e) => handleInputChange('budgetRange', e.target.value)}
                  placeholder="例如：无限制、经济型"
                />
              </Grid>
              
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  高级选项
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={formData.includeAdmin}
                          onChange={(e) => handleInputChange('includeAdmin', e.target.checked)}
                        />
                      }
                      label="包含管理后台"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={formData.includeMobile}
                          onChange={(e) => handleInputChange('includeMobile', e.target.checked)}
                        />
                      }
                      label="移动端适配"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={formData.includeAnalytics}
                          onChange={(e) => handleInputChange('includeAnalytics', e.target.checked)}
                        />
                      }
                      label="数据统计分析"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={formData.includeSEO}
                          onChange={(e) => handleInputChange('includeSEO', e.target.checked)}
                        />
                      }
                      label="SEO优化"
                    />
                  </Grid>
                </Grid>
              </Grid>
            </Grid>
          </Box>
        );

      case 3:
        return (
          <Box sx={{ mt: 2 }}>
            <Alert severity="info" sx={{ mb: 3 }}>
              请确认以下信息无误，点击"创建项目"后将开始自动生成项目文档。
            </Alert>
            
            <Paper sx={{ p: 2, mb: 2 }}>
              <Typography variant="h6" gutterBottom>项目概览</Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">项目名称</Typography>
                  <Typography variant="body1">{formData.name}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">项目类型</Typography>
                  <Typography variant="body1">
                    {PROJECT_TYPES.find(t => t.value === formData.projectType)?.label}
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="body2" color="text.secondary">项目描述</Typography>
                  <Typography variant="body1">{formData.description}</Typography>
                </Grid>
              </Grid>
            </Paper>
            
            <Paper sx={{ p: 2, mb: 2 }}>
              <Typography variant="h6" gutterBottom>功能需求</Typography>
              <Box sx={{ mb: 2 }}>
                {formData.features.map((feature) => (
                  <Chip key={feature} label={feature} size="small" sx={{ mr: 1, mb: 1 }} />
                ))}
              </Box>
              {formData.customFeatures && (
                <Typography variant="body2">
                  自定义功能：{formData.customFeatures}
                </Typography>
              )}
            </Paper>
            
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>技术配置</Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">技术栈</Typography>
                  <Typography variant="body1">
                    {TECH_STACKS.find(t => t.value === formData.technologyPreference)?.label}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">复杂度</Typography>
                  <Typography variant="body1">
                    {COMPLEXITY_LEVELS.find(l => l.value === formData.complexityLevel)?.label}
                  </Typography>
                </Grid>
              </Grid>
            </Paper>
          </Box>
        );

      default:
        return null;
    }
  };

  if (completed) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '60vh',
          textAlign: 'center',
        }}
      >
        <CheckCircleIcon sx={{ fontSize: 80, color: 'success.main', mb: 2 }} />
        <Typography variant="h4" gutterBottom>
          项目创建成功！
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          AI正在分析您的需求并生成项目文档，请稍候...
        </Typography>
        <LinearProgress sx={{ width: '300px', mb: 2 }} />
        <Typography variant="body2">
          即将跳转到项目文档页面
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto' }}>
      <Card>
        <CardContent sx={{ p: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <AddIcon sx={{ mr: 2, fontSize: 32, color: 'primary.main' }} />
            <Typography variant="h4" component="h1">
              创建新项目
            </Typography>
          </Box>
          
          <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
            详细描述您的项目需求，AI将为您生成完整的开发方案
          </Typography>

          <Stepper activeStep={activeStep} orientation="vertical">
            {steps.map((label, index) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
                <StepContent>
                  {renderStepContent(index)}
                  
                  <Box sx={{ mt: 3 }}>
                    <Button
                      variant="contained"
                      onClick={index === steps.length - 1 ? handleSubmit : handleNext}
                      disabled={!isStepValid(index) || createProjectMutation.isLoading}
                      sx={{ mr: 1 }}
                    >
                      {index === steps.length - 1 ? 
                        (createProjectMutation.isLoading ? '创建中...' : '创建项目') : 
                        '下一步'
                      }
                    </Button>
                    
                    {index > 0 && (
                      <Button onClick={handleBack} sx={{ mr: 1 }}>
                        上一步
                      </Button>
                    )}
                  </Box>
                </StepContent>
              </Step>
            ))}
          </Stepper>
        </CardContent>
      </Card>
    </Box>
  );
}

export default ProjectCreation;