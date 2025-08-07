
// 电商平台前端JavaScript
document.addEventListener('DOMContentLoaded', function() {
    loadProducts();
});

async function loadProducts() {
    try {
        const response = await fetch('/api/products');
        const data = await response.json();
        displayProducts(data.products);
    } catch (error) {
        console.error('加载商品失败:', error);
        displayProducts([
            {id: 1, name: "智能手机", price: 2999.0, stock: 100},
            {id: 2, name: "笔记本电脑", price: 5999.0, stock: 50},
            {id: 3, name: "无线耳机", price: 299.0, stock: 200}
        ]);
    }
}

function displayProducts(products) {
    const productGrid = document.getElementById('productGrid');
    
    productGrid.innerHTML = products.map(product => `
        <div class="product-card">
            <h4>${product.name}</h4>
            <div class="product-price">¥${product.price}</div>
            <p>库存: ${product.stock}</p>
            <button class="add-to-cart" onclick="addToCart(${product.id})">
                加入购物车
            </button>
        </div>
    `).join('');
}

function addToCart(productId) {
    alert(`商品 ${productId} 已加入购物车！`);
}
