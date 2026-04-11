import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Header from './components/layout/Header';
import Footer from './components/layout/Footer';
import TrendDashboard from './pages/TrendDashboard';
import ComparePage from './pages/ComparePage';
import GraphExplorer from './pages/GraphExplorer';
import ChatbotPage from './pages/ChatbotPage';
import './styles/global.css';

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Header />
        <main className="page-content">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<TrendDashboard />} />
            <Route path="/compare" element={<ComparePage />} />
            <Route path="/graph" element={<GraphExplorer />} />
            <Route path="/chat" element={<ChatbotPage />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </BrowserRouter>
  );
}
