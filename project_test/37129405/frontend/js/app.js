// 电商平台前端JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // 初始化应用
    initializeApp();
    
    // 绑定事件
    bindEvents();
    
    // 加载数据
    loadInitialData();
});

function initializeApp() {
    console.log('电商平台初始化...');
    
    // 检查用户登录状态
    checkLoginStatus();
}

function bindEvents() {
    // 登录按钮
    const loginBtn = document.getElementById('loginBtn');
    const loginModal = document.getElementById('loginModal');
    const loginForm = document.getElementById('loginForm');
    
    loginBtn.addEventListener('click', () => {
        loginModal.style.display = 'block';
    });
    
    loginForm.addEventListener('submit', handleLogin);
    
    // 注册按钮
    const registerBtn = document.getElementById('registerBtn');
    const registerModal = document.getElementById('registerModal');
    const registerForm = document.getElementById('registerForm');
    
    registerBtn.addEventListener('click', () => {
        registerModal.style.display = 'block';
    });
    
    registerForm.addEventListener('submit', handleRegister);
    
    // 关闭模态框
    const closeButtons = document.querySelectorAll('.close');
    closeButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.target.closest('.modal').style.display = 'none';
        });
    });
    
    // 点击模态框外部关闭
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            e.target.style.display = 'none';
        }
    });
    
    // 搜索功能
    const searchBtn = document.getElementById('searchBtn');
    const searchInput = document.getElementById('searchInput');
    
    searchBtn.addEventListener('click', performSearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
    
    // 分类筛选
    const categoryFilter = document.getElementById('categoryFilter');
    categoryFilter.addEventListener('change', filterByCategory);
}

async function loadInitialData() {
    try {
        // 加载商品
        await loadProducts();
        
        // 加载分类
        await loadCategories();
        
    } catch (error) {
        console.error('加载初始数据失败:', error);
        showMessage('加载数据失败，请刷新页面重试', 'error');
    }
}

async function loadProducts(search = '', category = '') {
    try {
        showLoading();
        
        const params = new URLSearchParams();
        if (search) params.append('search', search);
        if (category) params.append('category', category);
        
        const products = await api.getProducts(params.toString());
        displayProducts(products);
        
    } catch (error) {
        console.error('加载商品失败:', error);
        showMessage('加载商品失败', 'error');
    } finally {
        hideLoading();
    }
}

async function loadCategories() {
    try {
        const categories = await api.getCategories();
        displayCategories(categories);
    } catch (error) {
        console.error('加载分类失败:', error);
    }
}

function displayProducts(products) {
    const productGrid = document.getElementById('productGrid');
    
    if (products.length === 0) {
        productGrid.innerHTML = '<div class="loading">暂无商品</div>';
        return;
    }
    
    productGrid.innerHTML = products.map(product => `
        <div class="product-card">
            <div class="product-image">
                ${product.image_url 
                    ? `<img src="${product.image_url}" alt="${product.name}" style="width:100%;height:100%;object-fit:cover;">` 
                    : '商品图片'
                }
            </div>
            <div class="product-info">
                <div class="product-name">${product.name}</div>
                <div class="product-description">${product.description || ''}</div>
                <div class="product-price">¥${product.price}</div>
                <div class="product-actions">
                    <button class="btn btn-primary" onclick="addToCart(${product.id})">
                        加入购物车
                    </button>
                    <button class="btn btn-outline" onclick="viewProduct(${product.id})">
                        查看详情
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

function displayCategories(categories) {
    const categoryFilter = document.getElementById('categoryFilter');
    
    categoryFilter.innerHTML = '<option value="">所有分类</option>' + 
        categories.map(category => 
            `<option value="${category}">${category}</option>`
        ).join('');
}

async function handleLogin(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const loginData = {
        username: formData.get('username'),
        password: formData.get('password')
    };
    
    try {
        const result = await api.login(loginData);
        
        if (result.message === '登录成功') {
            // 保存用户信息
            localStorage.setItem('currentUser', JSON.stringify({
                user_id: result.user_id,
                username: result.username
            }));
            
            showMessage('登录成功！', 'success');
            document.getElementById('loginModal').style.display = 'none';
            updateUIForLoggedInUser(result);
            
        } else {
            showMessage('登录失败', 'error');
        }
    } catch (error) {
        console.error('登录错误:', error);
        showMessage('登录失败，请检查用户名和密码', 'error');
    }
}

async function handleRegister(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const registerData = {
        username: formData.get('username'),
        email: formData.get('email'),
        password: formData.get('password'),
        full_name: formData.get('full_name'),
        phone: formData.get('phone')
    };
    
    try {
        const result = await api.register(registerData);
        
        showMessage('注册成功！请登录', 'success');
        document.getElementById('registerModal').style.display = 'none';
        document.getElementById('loginModal').style.display = 'block';
        
    } catch (error) {
        console.error('注册错误:', error);
        showMessage('注册失败，请检查输入信息', 'error');
    }
}

function checkLoginStatus() {
    const currentUser = localStorage.getItem('currentUser');
    if (currentUser) {
        const user = JSON.parse(currentUser);
        updateUIForLoggedInUser(user);
    }
}

function updateUIForLoggedInUser(user) {
    const authButtons = document.querySelector('.auth-buttons');
    authButtons.innerHTML = `
        <span>欢迎, ${user.username}</span>
        <button class="btn btn-outline" onclick="logout()">退出</button>
    `;
}

function logout() {
    localStorage.removeItem('currentUser');
    location.reload();
}

async function performSearch() {
    const searchInput = document.getElementById('searchInput');
    const categoryFilter = document.getElementById('categoryFilter');
    
    await loadProducts(searchInput.value, categoryFilter.value);
}

async function filterByCategory() {
    const categoryFilter = document.getElementById('categoryFilter');
    const searchInput = document.getElementById('searchInput');
    
    await loadProducts(searchInput.value, categoryFilter.value);
}

function addToCart(productId) {
    const currentUser = localStorage.getItem('currentUser');
    if (!currentUser) {
        showMessage('请先登录', 'error');
        document.getElementById('loginModal').style.display = 'block';
        return;
    }
    
    // 这里可以实现购物车逻辑
    showMessage('商品已加入购物车！', 'success');
}

function viewProduct(productId) {
    // 这里可以实现商品详情页面跳转
    showMessage(`查看商品 ${productId} 的详情`, 'success');
}

function showLoading() {
    const productGrid = document.getElementById('productGrid');
    productGrid.innerHTML = '<div class="loading">加载中...</div>';
}

function hideLoading() {
    // 由displayProducts函数处理
}

function showMessage(message, type = 'success') {
    // 移除现有消息
    const existingMessage = document.querySelector('.message');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    // 创建新消息
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = message;
    
    // 插入到页面顶部
    const main = document.querySelector('main');
    main.insertBefore(messageDiv, main.firstChild);
    
    // 3秒后自动移除
    setTimeout(() => {
        messageDiv.remove();
    }, 3000);
}