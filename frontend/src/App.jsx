import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import NavBar from './components/NavBar';
import HomePage from './pages/HomePage';
import ResearchPage from './pages/ResearchPage';
import HistoryPage from './pages/HistoryPage';
import UploadPage from './pages/UploadPage';
import SettingsPage from './pages/SettingsPage';

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <div className="min-h-screen bg-app text-primary-color transition-colors duration-300">
          <NavBar />
          <Routes>
            <Route path="/"         element={<HomePage />} />
            <Route path="/research" element={<ResearchPage />} />
            <Route path="/history"  element={<HistoryPage />} />
            <Route path="/upload"   element={<UploadPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*"         element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </BrowserRouter>
    </ThemeProvider>
  );
}
