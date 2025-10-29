# 对话助手

一个基于 React + TypeScript 的现代化对话应用。

## 功能特点

- 响应式设计，支持桌面端和移动端
- 淡黄色主题界面
- 模板快速输入
- 历史记录查看
- 优雅的动画效果

## 技术栈

- React 18
- TypeScript
- Styled Components
- React Router
- Vite

## 开发环境要求

- Node.js 16+
- npm 7+

## 安装和运行

1. 安装依赖：
```bash
npm install
```

2. 启动开发服务器：
```bash
npm run dev
```

3. 构建生产版本：
```bash
npm run build
```

## 项目结构

```
src/
  ├── pages/          # 页面组件
  │   ├── ChatPage.tsx    # 主对话页面
  │   └── HistoryPage.tsx # 历史记录页面
  ├── App.tsx         # 应用主组件
  └── main.tsx        # 应用入口
```

## 使用说明

1. 在输入框输入消息或点击模板按钮快速输入
2. 点击发送按钮或按回车键发送消息
3. 点击右上角"历史记录"查看历史对话
4. 在历史记录页面点击卡片可返回对话页面 