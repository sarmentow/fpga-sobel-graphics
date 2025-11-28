import React, { useState, useEffect } from 'react';

function SessionsView({ onOpenPlayback }) {
  const [sessions, setSessions] = useState([]);

  const loadSessions = () => {
    const sessionList = window.api.listSessions();
    const sessionsWithJobs = sessionList.map(name => ({
      name,
      job: window.api.readJob(name) || { status: 'pending', processed_frames: 0, total_frames: 0 },
    }));
    setSessions(sessionsWithJobs);
  };

  useEffect(() => {
    loadSessions();
    const interval = setInterval(loadSessions, 2000);
    return () => clearInterval(interval);
  }, []);

  const formatDate = (sessionName) => {
    try {
      const dateStr = sessionName.replace(/-/g, (m, i) => 
        i < 10 ? '-' : i < 13 ? 'T' : ':'
      ).slice(0, 19);
      const date = new Date(dateStr);
      return isNaN(date.getTime()) ? sessionName : date.toLocaleString('pt-BR');
    } catch {
      return sessionName;
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-medium mb-2">Sessões</h2>
          <p className="text-gray-500 text-sm">Visualize e gerencie as sessões gravadas</p>
        </div>
        <button
          onClick={loadSessions}
          className="text-gray-400 hover:text-accent transition-colors"
        >
          <RefreshIcon />
        </button>
      </div>

      {sessions.length > 0 ? (
        <div className="space-y-3">
          {sessions.map(({ name, job }) => (
            <SessionCard
              key={name}
              name={name}
              job={job}
              displayName={formatDate(name)}
              onClick={() => onOpenPlayback(name)}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-16">
          <p className="text-gray-500">Nenhuma sessão gravada ainda</p>
        </div>
      )}
    </div>
  );
}

function SessionCard({ name, job, displayName, onClick }) {
  const badgeClass = {
    pending: 'badge-pending',
    processing: 'badge-processing',
    done: 'badge-done',
    error: 'badge-error',
  }[job.status] || 'badge-pending';

  const statusText = {
    pending: 'Pendente',
    processing: 'Processando',
    done: 'Concluído',
    error: 'Erro',
  }[job.status] || 'Desconhecido';

  const progress = job.total_frames > 0
    ? Math.round((job.processed_frames / job.total_frames) * 100)
    : 0;

  const showProgress = job.status === 'processing' && job.total_frames > 0;

  return (
    <div className="session-card" onClick={onClick}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium">{displayName}</span>
        <span className={`badge ${badgeClass}`}>{statusText}</span>
      </div>
      {showProgress && (
        <>
          <div className="progress-bar">
            <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {job.processed_frames} / {job.total_frames} quadros ({progress}%)
          </p>
        </>
      )}
    </div>
  );
}

function RefreshIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
      />
    </svg>
  );
}

export default SessionsView;
