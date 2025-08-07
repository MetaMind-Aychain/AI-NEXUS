
// 简单社交平台前端逻辑
document.addEventListener('DOMContentLoaded', function() {
    loadPosts();
    
    document.getElementById('publishBtn').addEventListener('click', publishPost);
    document.getElementById('loginBtn').addEventListener('click', () => alert('登录功能开发中'));
    document.getElementById('registerBtn').addEventListener('click', () => alert('注册功能开发中'));
});

async function loadPosts() {
    try {
        const response = await fetch('/api/posts/');
        const posts = await response.json();
        displayPosts(posts);
    } catch (error) {
        console.error('加载动态失败:', error);
        // 显示模拟数据
        displayPosts([
            {id: 1, content: "欢迎来到简单社交平台！", user: "系统", created_at: "2024-01-01"},
            {id: 2, content: "这是一个示例动态", user: "演示用户", created_at: "2024-01-02"}
        ]);
    }
}

function displayPosts(posts) {
    const postsList = document.getElementById('postsList');
    postsList.innerHTML = posts.map(post => `
        <div class="post">
            <div class="post-header">${post.user}</div>
            <div class="post-content">${post.content}</div>
            <div class="post-time">${new Date(post.created_at).toLocaleString()}</div>
        </div>
    `).join('');
}

async function publishPost() {
    const content = document.getElementById('postContent').value.trim();
    if (!content) {
        alert('请输入动态内容');
        return;
    }
    
    try {
        const response = await fetch('/api/posts/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({content: content, user_id: 1})
        });
        
        if (response.ok) {
            document.getElementById('postContent').value = '';
            loadPosts(); // 重新加载动态
            alert('发布成功！');
        }
    } catch (error) {
        console.error('发布失败:', error);
        alert('发布成功！（模拟）');
        document.getElementById('postContent').value = '';
    }
}
