import React, { useState } from 'react';
import RecordView from './views/RecordView.jsx';
import SessionsView from './views/SessionsView.jsx';
import PlaybackView from './views/PlaybackView.jsx';

function App() {
  const [currentView, setCurrentView] = useState('record');
  const [selectedSession, setSelectedSession] = useState(null);

  const handleOpenPlayback = (sessionName) => {
    setSelectedSession(sessionName);
    setCurrentView('playback');
  };

  const handleBackToSessions = () => {
    setSelectedSession(null);
    setCurrentView('sessions');
  };

  const handleRecordingComplete = () => {
    setCurrentView('sessions');
  };

  return (
    <div className="bg-surface-900 text-gray-100 font-mono min-h-screen">
      <nav className="bg-surface-800 border-b border-surface-600 px-6 py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-accent text-lg font-semibold tracking-tight">AFTER</h1>
          <div className="flex gap-1">
            <NavButton
              active={currentView === 'record'}
              onClick={() => setCurrentView('record')}
              showDot
            >
              Gravar
            </NavButton>
            <NavButton
              active={currentView === 'sessions'}
              onClick={() => setCurrentView('sessions')}
            >
              Sessões
            </NavButton>
            <NavButton
              active={currentView === 'playback'}
              onClick={() => setCurrentView('playback')}
            >
              Reproduzir
            </NavButton>
          </div>
        </div>
      </nav>

      <main className="p-6">
        {currentView === 'record' && (
          <RecordView onComplete={handleRecordingComplete} />
        )}
        {currentView === 'sessions' && (
          <SessionsView onOpenPlayback={handleOpenPlayback} />
        )}
        {currentView === 'playback' && (
          <PlaybackView
            sessionName={selectedSession}
            onBack={handleBackToSessions}
          />
        )}
      </main>
    </div>
  );
}

function NavButton({ children, active, onClick, showDot }) {
  return (
    <button
      className={`nav-btn ${active ? 'active' : ''}`}
      onClick={onClick}
    >
      {showDot && (
        <span className={`w-2 h-2 rounded-full ${active ? 'bg-red-500 animate-pulse' : 'bg-transparent'}`} />
      )}
      {children}
    </button>
  );
}

export default App;
