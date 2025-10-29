import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';

const PageContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  height: 100vh;
  display: flex;
  flex-direction: column;
`;

const NavBar = styled.nav`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  margin-bottom: 20px;
`;

const AppTitle = styled.h1`
  color: #424242;
  margin: 0;
  font-size: 24px;
`;

const HistoryButton = styled.button`
  background: none;
  border: 1px solid #D7CCC8;
  padding: 8px 16px;
  border-radius: 4px;
  color: #424242;
  cursor: pointer;
  &:hover {
    background: #FFECB3;
  }
`;

const ChatContainer = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

const MessageBubble = styled.div<{ isUser: boolean }>`
  max-width: 70%;
  padding: 12px;
  border-radius: 8px;
  background-color: ${props => props.isUser ? '#FFECB3' : '#FFFFFF'};
  align-self: ${props => props.isUser ? 'flex-end' : 'flex-start'};
  animation: fadeIn 0.2s ease-in-out;

  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
`;

const TemplateBar = styled.div`
  display: flex;
  gap: 1px;
  background-color: #FFECB3;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 10px;

  @media (max-width: 768px) {
    flex-wrap: wrap;
    justify-content: center;
  }
`;

const TemplateButton = styled.button`
  flex: 1;
  padding: 8px;
  border: none;
  background: none;
  color: #424242;
  cursor: pointer;
  transition: all 0.1s ease;
  border-right: 1px dashed #D7CCC8;

  &:last-child {
    border-right: none;
  }

  &:hover {
    background-color: #FFE082;
  }

  &:active {
    transform: scale(0.98);
  }

  @media (max-width: 768px) {
    flex: 0 0 calc(50% - 1px);
    border-right: 1px dashed #D7CCC8;
    border-bottom: 1px dashed #D7CCC8;

    &:nth-child(2n) {
      border-right: none;
    }
  }
`;

const InputContainer = styled.div`
  display: flex;
  gap: 10px;
  padding: 20px 0;
  position: sticky;
  bottom: 0;
  background-color: #FFF8E1;
`;

const Input = styled.input`
  flex: 1;
  padding: 12px;
  border: 1px solid #D7CCC8;
  border-radius: 4px;
  font-size: 16px;
  &:focus {
    outline: none;
    border-color: #FFE082;
  }
`;

const SendButton = styled.button`
  padding: 12px 24px;
  background-color: #FFECB3;
  border: none;
  border-radius: 4px;
  color: #424242;
  cursor: pointer;
  &:hover {
    background-color: #FFE082;
  }
`;

const templates = ['模板一', '模板二', '模板三', '模板四'];

const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<Array<{ text: string; isUser: boolean }>>([]);
  const [inputValue, setInputValue] = useState('');
  const navigate = useNavigate();
  const chatContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = () => {
    if (inputValue.trim()) {
      setMessages([...messages, { text: inputValue, isUser: true }]);
      setInputValue('');
      // Simulate system response
      setTimeout(() => {
        setMessages(prev => [...prev, { text: '收到您的消息了！', isUser: false }]);
      }, 1000);
    }
  };

  const handleTemplateClick = (template: string) => {
    setInputValue(template);
  };

  return (
    <PageContainer>
      <NavBar>
        <AppTitle>对话助手</AppTitle>
        <HistoryButton onClick={() => navigate('/history')}>历史记录</HistoryButton>
      </NavBar>

      <ChatContainer ref={chatContainerRef}>
        {messages.map((message, index) => (
          <MessageBubble key={index} isUser={message.isUser}>
            {message.text}
          </MessageBubble>
        ))}
      </ChatContainer>

      <TemplateBar>
        {templates.map((template, index) => (
          <TemplateButton
            key={index}
            onClick={() => handleTemplateClick(template)}
          >
            {template}
          </TemplateButton>
        ))}
      </TemplateBar>

      <InputContainer>
        <Input
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="输入消息..."
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
        />
        <SendButton onClick={handleSend}>发送</SendButton>
      </InputContainer>
    </PageContainer>
  );
};

export default ChatPage; 