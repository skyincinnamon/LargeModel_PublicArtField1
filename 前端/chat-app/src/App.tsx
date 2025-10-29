import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import styled from 'styled-components';
import ChatPage from './pages/ChatPage';
import HistoryPage from './pages/HistoryPage';

const AppContainer = styled.div`
  min-height: 100vh;
  background-color: #FFF8E1;
`;

function App() {
  return (
    <Router>
      <AppContainer>
        <Routes>
          <Route path="/" element={<ChatPage />} />
          <Route path="/history" element={<HistoryPage />} />
        </Routes>
      </AppContainer>
    </Router>
  );
}

export default App;
