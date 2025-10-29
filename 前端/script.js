// 返回顶部按钮
const backToTop = document.getElementById('backToTop');

if (backToTop) {
    window.addEventListener('scroll', () => {
        if (window.scrollY > 200) {
            backToTop.classList.add('show');
        } else {
            backToTop.classList.remove('show');
        }
    });

    backToTop.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// 导航栏点击事件
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        // 移除其他项目的活动状态
        document.querySelectorAll('.nav-item').forEach(navItem => {
            navItem.style.backgroundColor = 'white';
        });
        // 设置当前项目的活动状态
        item.style.backgroundColor = '#F3F0EB';
    });
});

// 聊天功能（智能体对话网站风格，纯文本左对齐）
document.addEventListener('DOMContentLoaded', function() {
    const chatBox = document.getElementById('chatBox');
    const messageInput = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');
    const newChatBtn = document.getElementById('newChatBtn');
    const historyContainer = document.getElementById('historyContainer');

    // 存储对话历史
    let chatHistory = [];
    let currentChatId = null;

    // 获取对话中的第一条用户消息
    function getFirstUserMessage(chatContent) {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = chatContent;
        const messages = tempDiv.querySelectorAll('div');
        for (const message of messages) {
            if (message.textContent.startsWith('用户：')) {
                return message.textContent.replace('用户：', '').trim();
            }
        }
        return '新对话';
    }

    // 初始化欢迎语
    if (chatBox && !chatBox.innerHTML.trim()) {
        chatBox.innerHTML = '<div class="welcome-message" style="color:#888;margin:20px 0;">欢迎来到公共艺术设计交流平台。请提出您关于公共艺术设计的问题...</div>';
    }

    // 保存当前对话
    function saveCurrentChat() {
        if (chatBox.innerHTML.trim() && !chatBox.querySelector('.welcome-message')) {
            // 如果当前对话已经有ID，说明已经保存过，更新内容
            if (currentChatId) {
                const existingChatIndex = chatHistory.findIndex(c => c.id === currentChatId);
                if (existingChatIndex !== -1) {
                    chatHistory[existingChatIndex].content = chatBox.innerHTML;
                    chatHistory[existingChatIndex].timestamp = new Date().toLocaleString();
                }
            } else {
                // 如果是新对话，创建新的历史记录
                const currentChat = {
                    id: Date.now(),
                    content: chatBox.innerHTML,
                    timestamp: new Date().toLocaleString(),
                    title: getFirstUserMessage(chatBox.innerHTML)
                };
                chatHistory.push(currentChat);
                currentChatId = currentChat.id;
            }
            updateHistoryList();
        }
    }

    // 创建新对话
    function createNewChat() {
        // 保存当前对话
        saveCurrentChat();

        // 清空当前对话
        chatBox.innerHTML = '<div class="welcome-message" style="color:#888;margin:20px 0;">欢迎来到公共艺术设计交流平台。请提出您关于公共艺术设计的问题...</div>';
        currentChatId = null;
    }

    // 更新历史记录列表
    function updateHistoryList() {
        historyContainer.innerHTML = '';
        chatHistory.forEach(chat => {
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item';
            historyItem.innerHTML = `
                <div class="history-content">
                    <span class="history-title">${chat.title || '新对话'}</span>
                    <span class="history-time">${chat.timestamp}</span>
                </div>
                <button class="delete-btn" title="删除对话">
                    <i class="fas fa-trash"></i>
                </button>
            `;
            
            // 点击历史记录项加载对话
            historyItem.querySelector('.history-content').addEventListener('click', () => {
                // 保存当前对话
                saveCurrentChat();
                // 加载选中的历史对话
                loadChat(chat.id);
            });

            // 点击删除按钮删除对话
            const deleteBtn = historyItem.querySelector('.delete-btn');
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation(); // 阻止事件冒泡，避免触发加载对话
                if (confirm('确定要删除这条对话记录吗？')) {
                    // 如果删除的是当前对话，清空聊天框
                    if (currentChatId === chat.id) {
                        chatBox.innerHTML = '<div class="welcome-message" style="color:#888;margin:20px 0;">欢迎来到公共艺术设计交流平台。请提出您关于公共艺术设计的问题...</div>';
                        currentChatId = null;
                    }
                    // 从历史记录中删除
                    chatHistory = chatHistory.filter(c => c.id !== chat.id);
                    updateHistoryList();
                }
            });
            
            historyContainer.appendChild(historyItem);
        });
    }

    // 加载历史对话
    function loadChat(chatId) {
        const chat = chatHistory.find(c => c.id === chatId);
        if (chat) {
            chatBox.innerHTML = chat.content;
            currentChatId = chatId;
        }
    }

    // 添加新对话按钮事件监听
    if (newChatBtn) {
        newChatBtn.addEventListener('click', createNewChat);
    }

    async function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;

        // 清除欢迎语
        const welcome = chatBox.querySelector('.welcome-message');
        if (welcome) {
            chatBox.innerHTML = '';
            // 如果是新对话，创建新的历史记录
            if (!currentChatId) {
                currentChatId = Date.now();
                chatHistory.push({
                    id: currentChatId,
                    content: '',
                    timestamp: new Date().toLocaleString(),
                    title: message // 使用第一条消息作为标题
                });
                updateHistoryList();
            }
        }

        // 用户文本
        appendTextLine(`用户：${message}`);
        messageInput.value = '';

        // 调用AI回复
        try {
            const aiReply = await fetchAIReply(message);
            appendTextLine(`公共艺术设计师：${aiReply}`);
            // 每次对话后更新历史记录
            saveCurrentChat();
        } catch (error) {
            console.error('发送消息时出错:', error);
            appendTextLine(`系统：抱歉，处理您的请求时出现错误，请稍后重试。`);
        }
    }

    function appendTextLine(text) {
        const line = document.createElement('div');
        line.textContent = text;
        line.style.textAlign = 'left';
        line.style.fontSize = '16px';
        line.style.margin = '2px 0';
        line.style.lineHeight = '1.1';
        chatBox.appendChild(line);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // 占位API函数，后续你可替换为真实API
    async function fetchAIReply(userMsg) {
        try {
            // 显示加载状态
            const loadingDiv = document.createElement('div');
            loadingDiv.textContent = '公共艺术设计师：正在思考中...';
            loadingDiv.style.textAlign = 'left';
            loadingDiv.style.fontSize = '16px';
            loadingDiv.style.margin = '2px 0';
            loadingDiv.style.lineHeight = '1.1';
            loadingDiv.style.color = '#888';
            loadingDiv.id = 'loading-message';
            chatBox.appendChild(loadingDiv);
            chatBox.scrollTop = chatBox.scrollHeight;

            // 调用后端API
            const response = await fetch('http://localhost:5000/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: userMsg
                })
            });

            // 移除加载状态
            const loadingMessage = document.getElementById('loading-message');
            if (loadingMessage) {
                loadingMessage.remove();
            }

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.success) {
                return data.response;
            } else {
                throw new Error(data.error || '未知错误');
            }
        } catch (error) {
            console.error('API调用失败:', error);
            
            // 移除加载状态
            const loadingMessage = document.getElementById('loading-message');
            if (loadingMessage) {
                loadingMessage.remove();
            }
            
            // 返回错误信息
            return `抱歉，处理您的请求时出现错误：${error.message}。请检查后端服务是否正在运行，或稍后重试。`;
        }
    }

    if (sendBtn && messageInput) {
        sendBtn.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    // 关键词气泡功能 - 精简版（只保留前10个）
    const keywordBubbles = document.getElementById('keywordBubbles');
    if (keywordBubbles) {
        // 设置容器样式
        keywordBubbles.style.display = 'flex';
        keywordBubbles.style.flexWrap = 'wrap';
        keywordBubbles.style.gap = '4.5px'; 
        keywordBubbles.style.padding = '5px';
        
        // 只保留前10个关键词
        const keywords = [
            ["暗黑", "dark"], 
            ["会动的艺术", "animating"], 
            ["机械", "mechanical"], 
            ["废土风", "dystopian"], 
            ["自然", "nature"], 
            ["复古彩虹爆炸", "rainbow explosion"], 
            ["极简性冷淡", "minimal cold"], 
            ["魔幻", "fantasy"], 
            ["写实", "realism"], 
            ["光影", "light and shadow"]
        ]; // 只保留前10个
        
        keywords.forEach(([word, en]) => {
            const bubble = document.createElement('div');
            bubble.className = 'bubble';
            bubble.textContent = word;
            bubble.setAttribute('data-keyword', en);
            
            // 基础样式
            bubble.style.padding = '2px 8px';
            bubble.style.borderRadius = '13px';
            bubble.style.cursor = 'pointer';
            bubble.style.transition = 'all 0.3s ease';
            bubble.style.fontSize = '14px';
            bubble.style.backgroundColor = 'white';
            bubble.style.color = 'black';
            bubble.style.border = '1px solid #ddd';
            
            // 点击效果
            bubble.addEventListener('click', function() {
                const isActive = bubble.classList.contains('active');
                bubble.style.backgroundColor = isActive ? 'white' : 'black';
                bubble.style.color = isActive ? 'black' : 'white';
                bubble.style.border = isActive ? '1px solid #ddd' : '1px solid black';
                bubble.classList.toggle('active');
            });
            
            keywordBubbles.appendChild(bubble);
        });
    }

    // 侧边栏折叠/展开
    const toggleBtn = document.getElementById('toggleSidebar');
    const sidebar = document.querySelector('.sidebar');
    
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            const icon = toggleBtn.querySelector('i');
            if (sidebar.classList.contains('collapsed')) {
                icon.classList.remove('fa-chevron-left');
                icon.classList.add('fa-chevron-right');
            } else {
                icon.classList.remove('fa-chevron-right');
                icon.classList.add('fa-chevron-left');
            }
        });
    }

    // 初始化日历
    const artCalendar = document.getElementById('artCalendar');
    if (artCalendar) {
        initializeCalendar();
    }
    
    function initializeCalendar() {
        // 获取当前日期信息
        const date = new Date();
        const currentMonth = date.getMonth();
        const currentYear = date.getFullYear();
        const currentDay = date.getDate();
        
        // 月份名称
        const monthNames = ['一月', '二月', '三月', '四月', '五月', '六月', 
                          '七月', '八月', '九月', '十月', '十一月', '十二月'];
        
        // 添加月份标题
        const monthTitle = document.createElement('div');
        monthTitle.className = 'calendar-month-title';
        monthTitle.textContent = `${monthNames[currentMonth]} ${currentYear}`;
        artCalendar.appendChild(monthTitle);
        
        // 获取当月第一天和最后一天
        const firstDay = new Date(currentYear, currentMonth, 1);
        const lastDay = new Date(currentYear, currentMonth + 1, 0);
        
        // 周日到周六的表头
        const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
        weekdays.forEach(day => {
            const dayEl = document.createElement('div');
            dayEl.className = 'calendar-weekday';
            dayEl.textContent = day;
            artCalendar.appendChild(dayEl);
        });
        
        // 填充月份前的空白日期
        for (let i = 0; i < firstDay.getDay(); i++) {
            const emptyDay = document.createElement('div');
            emptyDay.className = 'calendar-day empty';
            artCalendar.appendChild(emptyDay);
        }
        
        // 填充日期
        for (let i = 1; i <= lastDay.getDate(); i++) {
            const dayEl = document.createElement('div');
            dayEl.className = 'calendar-day';
            dayEl.textContent = i;
            
            // 标记当天
            if (i === currentDay) {
                dayEl.classList.add('active');
            }
            
            // 随机添加事件标记（模拟有艺术活动的日期）
            if (Math.random() > 0.7) {
                dayEl.classList.add('has-event');
                dayEl.title = '有艺术活动';
            }
            
            artCalendar.appendChild(dayEl);
        }
    }
});