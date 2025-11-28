const { contextBridge } = require('electron');
const fs = require('fs');
const path = require('path');

const sessionsDir = path.join(__dirname, 'sessions');

if (!fs.existsSync(sessionsDir)) {
  fs.mkdirSync(sessionsDir, { recursive: true });
}

contextBridge.exposeInMainWorld('api', {
  getSessionsPath: () => sessionsDir,

  listSessions: () => {
    try {
      const entries = fs.readdirSync(sessionsDir, { withFileTypes: true });
      return entries
        .filter(e => e.isDirectory())
        .map(e => e.name)
        .sort()
        .reverse();
    } catch (err) {
      console.error('Failed to list sessions:', err);
      return [];
    }
  },

  readJob: (sessionName) => {
    try {
      const jobPath = path.join(sessionsDir, sessionName, 'job.json');
      if (!fs.existsSync(jobPath)) return null;
      const data = fs.readFileSync(jobPath, 'utf-8');
      return JSON.parse(data);
    } catch (err) {
      console.error('Failed to read job:', err);
      return null;
    }
  },

  createSession: (sessionName, videoData, audioData) => {
    const sessionPath = path.join(sessionsDir, sessionName);
    fs.mkdirSync(sessionPath, { recursive: true });

    fs.writeFileSync(path.join(sessionPath, 'original.webm'), Buffer.from(videoData));

    if (audioData) {
      fs.writeFileSync(path.join(sessionPath, 'audio.webm'), Buffer.from(audioData));
    }

    const job = {
      status: 'pending',
      total_frames: 0,
      processed_frames: 0,
      created_at: new Date().toISOString()
    };
    fs.writeFileSync(path.join(sessionPath, 'job.json'), JSON.stringify(job, null, 2));

    return sessionPath;
  },

  getSessionFile: (sessionName, filename) => {
    return path.join(sessionsDir, sessionName, filename);
  },

  fileExists: (filePath) => {
    return fs.existsSync(filePath);
  },

  readAnalytics: (sessionName) => {
    try {
      const analyticsPath = path.join(sessionsDir, sessionName, 'analytics.json');
      if (!fs.existsSync(analyticsPath)) return null;
      const data = fs.readFileSync(analyticsPath, 'utf-8');
      return JSON.parse(data);
    } catch (err) {
      console.error('Failed to read analytics:', err);
      return null;
    }
  }
});

