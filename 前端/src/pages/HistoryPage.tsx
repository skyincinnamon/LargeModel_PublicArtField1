import React from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';

const PageContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
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

const BackButton = styled.button`
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

const HistoryList = styled.div`
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
`;

const HistoryCard = styled.div`
  background: #FFFFFF;
  border: 1px solid #D7CCC8;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  }
`;

const DateText = styled.div`
  color: #424242;
  font-size: 14px;
  margin-bottom: 8px;
`;

const PreviewText = styled.div`
  color: #424242;
  font-size: 16px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

// Mock data for demonstration
const mockHistory = [
  { id: 1, date: '5月13日', preview: '这是一个示例对话内容，展示了历史记录的功能...' },
  { id: 2, date: '5月12日', preview: '另一个示例对话，用于展示历史记录列表...' },
  { id: 3, date: '5月11日', preview: '这是更早的对话记录，同样展示在历史列表中...' },
];

const HistoryPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <PageContainer>
      <NavBar>
        <AppTitle>对话助手</AppTitle>
        <BackButton onClick={() => navigate('/')}>返回对话</BackButton>
      </NavBar>

      <HistoryList>
        {mockHistory.map((item) => (
          <HistoryCard key={item.id} onClick={() => navigate('/')}>
            <DateText>{item.date}</DateText>
            <PreviewText>{item.preview}</PreviewText>
          </HistoryCard>
        ))}
      </HistoryList>
    </PageContainer>
  );
};

export default HistoryPage; 