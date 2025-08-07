// API客户端

const API_BASE_URL = '/api';

class APIClient {
    constructor(baseURL = API_BASE_URL) {
        this.baseURL = baseURL;
    }
    
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        const finalOptions = { ...defaultOptions, ...options };
        
        if (finalOptions.body && typeof finalOptions.body === 'object') {
            finalOptions.body = JSON.stringify(finalOptions.body);
        }
        
        try {
            const response = await fetch(url, finalOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            
            return await response.text();
            
        } catch (error) {
            console.error('API请求失败:', error);
            throw error;
        }
    }
    
    // 商品相关API
    async getProducts(queryParams = '') {
        const endpoint = queryParams ? `/products/?${queryParams}` : '/products/';
        return this.request(endpoint);
    }
    
    async getProduct(productId) {
        return this.request(`/products/${productId}`);
    }
    
    async getCategories() {
        return this.request('/products/categories/');
    }
    
    // 用户相关API
    async register(userData) {
        return this.request('/users/register', {
            method: 'POST',
            body: userData
        });
    }
    
    async login(credentials) {
        return this.request('/users/login', {
            method: 'POST',
            body: credentials
        });
    }
    
    async getUser(userId) {
        return this.request(`/users/${userId}`);
    }
    
    // 订单相关API
    async createOrder(orderData) {
        return this.request('/orders/', {
            method: 'POST',
            body: orderData
        });
    }
    
    async getOrder(orderId) {
        return this.request(`/orders/${orderId}`);
    }
    
    async getUserOrders(userId) {
        return this.request(`/orders/user/${userId}`);
    }
    
    async updateOrderStatus(orderId, status) {
        return this.request(`/orders/${orderId}/status`, {
            method: 'PUT',
            body: { status }
        });
    }
    
    // 健康检查
    async healthCheck() {
        return this.request('/health');
    }
}

// 创建全局API实例
const api = new APIClient();

// 导出供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = APIClient;
}