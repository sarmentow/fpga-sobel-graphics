import React, { useRef, useState, useEffect } from 'react';

function RecordView({ onComplete }) {
  const videoRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  
  const [isRecording, setIsRecording] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [cameraReady, setCameraReady] = useState(false);
  const [error, setError] = useState(null);
  const [stream, setStream] = useState(null);

  useEffect(() => {
    async function initCamera() {
      try {
        const mediaStream = await navigator.mediaDevices.getUserMedia({
          video: { width: 1280, height: 720 },
          audio: true,
        });
        
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
        }
        setStream(mediaStream);
        setCameraReady(true);
      } catch (err) {
        console.error('Camera access failed:', err);
        setError('Camera access denied');
      }
    }
    
    initCamera();
    
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  useEffect(() => {
    let interval;
    if (isRecording) {
      interval = setInterval(() => {
        setElapsedTime(t => t + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isRecording]);

  const startRecording = () => {
    if (!stream) return;
    
    chunksRef.current = [];
    
    const mediaRecorder = new MediaRecorder(stream, {
      mimeType: 'video/webm;codecs=vp9',
    });
    
    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        chunksRef.current.push(e.data);
      }
    };
    
    mediaRecorder.onstop = saveRecording;
    
    mediaRecorderRef.current = mediaRecorder;
    mediaRecorder.start(1000);
    
    setIsRecording(true);
    setElapsedTime(0);
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
  };

  const saveRecording = async () => {
    const blob = new Blob(chunksRef.current, { type: 'video/webm' });
    const arrayBuffer = await blob.arrayBuffer();
    const videoData = new Uint8Array(arrayBuffer);
    
    const now = new Date();
    const sessionName = now.toISOString().replace(/[:.]/g, '-').slice(0, 19);
    
    try {
      window.api.createSession(sessionName, videoData, null);
      onComplete();
    } catch (err) {
      console.error('Failed to save recording:', err);
      setError('Failed to save recording: ' + err.message);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
    const secs = (seconds % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h2 className="text-xl font-medium mb-2">Record Session</h2>
        <p className="text-gray-500 text-sm">Capture video for movement analysis</p>
      </div>

      <div className="relative bg-surface-800 rounded-lg overflow-hidden aspect-video mb-6 border border-surface-600">
        <video
          ref={videoRef}
          autoPlay
          muted
          playsInline
          className="w-full h-full object-cover"
        />
        
        {!cameraReady && (
          <div className="absolute inset-0 flex items-center justify-center">
            <p className={error ? 'text-red-400' : 'text-gray-500'}>
              {error || 'Camera initializing...'}
            </p>
          </div>
        )}

        {isRecording && (
          <div className="absolute top-4 left-4">
            <span className="flex items-center gap-2 bg-red-600 px-3 py-1 rounded-full text-sm">
              <span className="w-2 h-2 bg-white rounded-full animate-pulse" />
              REC
            </span>
          </div>
        )}

        {isRecording && (
          <div className="absolute top-4 right-4">
            <span className="bg-surface-900/80 px-3 py-1 rounded text-sm font-medium">
              {formatTime(elapsedTime)}
            </span>
          </div>
        )}
      </div>

      <div className="flex justify-center gap-4">
        {!isRecording ? (
          <button
            className="btn-primary"
            onClick={startRecording}
            disabled={!cameraReady}
          >
            Start Recording
          </button>
        ) : (
          <button className="btn-secondary" onClick={stopRecording}>
            Stop Recording
          </button>
        )}
      </div>
    </div>
  );
}

export default RecordView;

