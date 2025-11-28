import React, { useRef, useState, useEffect } from 'react';

function PlaybackView({ sessionName, onBack }) {
  const originalRef = useRef(null);
  const heatmapRef = useRef(null);
  
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [hasHeatmap, setHasHeatmap] = useState(false);
  const [analytics, setAnalytics] = useState(null);

  useEffect(() => {
    if (!sessionName) return;

    const originalPath = window.api.getSessionFile(sessionName, 'original.webm');
    const heatmapPath = window.api.getSessionFile(sessionName, 'heatmap.webm');

    if (originalRef.current) {
      originalRef.current.src = `file://${originalPath}`;
    }

    const heatmapExists = window.api.fileExists(heatmapPath);
    setHasHeatmap(heatmapExists);

    const analyticsData = window.api.readAnalytics(sessionName);
    setAnalytics(analyticsData);
  }, [sessionName]);

  useEffect(() => {
    if (!sessionName || !hasHeatmap) return;

    const heatmapPath = window.api.getSessionFile(sessionName, 'heatmap.webm');
    
    if (heatmapRef.current) {
      heatmapRef.current.src = `file://${heatmapPath}`;
    }
  }, [sessionName, hasHeatmap]);

  const togglePlayPause = () => {
    if (!originalRef.current) return;

    if (originalRef.current.paused) {
      originalRef.current.play();
      if (heatmapRef.current && hasHeatmap) {
        heatmapRef.current.play();
      }
      setIsPlaying(true);
    } else {
      originalRef.current.pause();
      if (heatmapRef.current) {
        heatmapRef.current.pause();
      }
      setIsPlaying(false);
    }
  };

  const handleTimeUpdate = () => {
    if (!originalRef.current) return;
    setCurrentTime(originalRef.current.currentTime);
    
    if (heatmapRef.current && hasHeatmap) {
      if (Math.abs(originalRef.current.currentTime - heatmapRef.current.currentTime) > 0.1) {
        heatmapRef.current.currentTime = originalRef.current.currentTime;
      }
    }
  };

  const handleLoadedMetadata = () => {
    if (originalRef.current) {
      const dur = originalRef.current.duration;
      if (isFinite(dur) && dur > 0) {
        setDuration(dur);
      }
    }
  };

  const handleDurationChange = () => {
    if (originalRef.current) {
      const dur = originalRef.current.duration;
      if (isFinite(dur) && dur > 0) {
        setDuration(dur);
      }
    }
  };

  const handleSeek = (e) => {
    const time = (e.target.value / 100) * effectiveDuration;
    if (originalRef.current) {
      originalRef.current.currentTime = time;
    }
    if (heatmapRef.current && hasHeatmap) {
      heatmapRef.current.currentTime = time;
    }
  };

  const handleEnded = () => {
    setIsPlaying(false);
  };

  const formatTime = (seconds) => {
    if (!isFinite(seconds) || isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  };

  const effectiveDuration = duration > 0 ? duration : (analytics?.duration_seconds || 0);

  const formatDate = (name) => {
    if (!name) return '';
    try {
      const dateStr = name.replace(/-/g, (m, i) => 
        i < 10 ? '-' : i < 13 ? 'T' : ':'
      ).slice(0, 19);
      const date = new Date(dateStr);
      return isNaN(date.getTime()) ? name : date.toLocaleString();
    } catch {
      return name;
    }
  };

  const progress = effectiveDuration > 0 ? (currentTime / effectiveDuration) * 100 : 0;

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-6 flex items-center gap-4">
        <button
          onClick={onBack}
          className="text-gray-400 hover:text-accent transition-colors"
        >
          <BackIcon />
        </button>
        <div>
          <h2 className="text-xl font-medium">{formatDate(sessionName)}</h2>
          <p className="text-gray-500 text-sm">
            {hasHeatmap ? 'Side-by-side comparison' : 'Heatmap processing not complete'}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-surface-800 rounded-lg overflow-hidden border border-surface-600">
          <div className="px-4 py-2 bg-surface-700 border-b border-surface-600">
            <span className="text-sm text-gray-400">Original</span>
          </div>
          <video
            ref={originalRef}
            className="w-full aspect-video bg-black"
            onTimeUpdate={handleTimeUpdate}
            onLoadedMetadata={handleLoadedMetadata}
            onDurationChange={handleDurationChange}
            onEnded={handleEnded}
          />
        </div>

        <div className="bg-surface-800 rounded-lg overflow-hidden border border-surface-600">
          <div className="px-4 py-2 bg-surface-700 border-b border-surface-600">
            <span className="text-sm text-gray-400">Movement Heatmap</span>
          </div>
          {hasHeatmap ? (
            <video
              ref={heatmapRef}
              className="w-full aspect-video bg-black"
            />
          ) : (
            <div className="w-full aspect-video bg-black flex items-center justify-center">
              <p className="text-gray-500 text-sm">Processing not complete</p>
            </div>
          )}
        </div>
      </div>

      <div className="bg-surface-800 rounded-lg p-4 border border-surface-600 mb-6">
        <div className="flex items-center gap-4">
          <button
            onClick={togglePlayPause}
            className="text-accent hover:text-accent-dim transition-colors"
          >
            {isPlaying ? <PauseIcon /> : <PlayIcon />}
          </button>

          <div className="flex-1">
            <input
              type="range"
              min="0"
              max="100"
              value={progress}
              onChange={handleSeek}
              className="w-full"
            />
          </div>

          <span className="text-sm text-gray-400 font-medium min-w-[80px] text-right">
            {formatTime(currentTime)} / {formatTime(effectiveDuration)}
          </span>
        </div>
      </div>

      {analytics && <AnalyticsPanel analytics={analytics} currentTime={currentTime} />}
    </div>
  );
}

function AnalyticsPanel({ analytics, currentTime }) {
  const { intensity, repetition, hot_zones, timeline, zone_timeline, duration_seconds } = analytics;

  const currentZones = React.useMemo(() => {
    if (!zone_timeline || zone_timeline.length === 0) return hot_zones;
    
    let closest = zone_timeline[0];
    for (const entry of zone_timeline) {
      if (entry.time <= currentTime) {
        closest = entry;
      } else {
        break;
      }
    }
    return closest?.zones || hot_zones;
  }, [zone_timeline, currentTime, hot_zones]);

  return (
    <div className="bg-surface-800 rounded-lg border border-surface-600 p-6">
      <h3 className="text-lg font-medium mb-4 text-accent">Movement Analytics</h3>
      
      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatCard label="Duration" value={formatDuration(duration_seconds)} />
        <StatCard label="Avg Intensity" value={intensity?.average?.toFixed(1) || '—'} />
        <StatCard 
          label="Peak Intensity" 
          value={intensity?.peak?.toFixed(1) || '—'} 
          subtext={intensity?.peak_time ? `@ ${formatDuration(intensity.peak_time)}` : null}
        />
        <StatCard 
          label="Cycles Detected" 
          value={repetition?.cycle_count || 0}
          subtext={repetition?.cycles_per_minute ? `${repetition.cycles_per_minute}/min` : null}
        />
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2">
          <h4 className="text-sm text-gray-400 mb-2">Intensity Timeline</h4>
          <IntensityGraph timeline={timeline} currentTime={currentTime} duration={duration_seconds} />
        </div>
        
        <div>
          <h4 className="text-sm text-gray-400 mb-2">Hot Zones (Live)</h4>
          <HotZonesGrid zones={currentZones} />
          
          {repetition && (
            <div className="mt-4">
              <h4 className="text-sm text-gray-400 mb-2">Repetition Analysis</h4>
              <div className="space-y-2">
                {repetition.dominant_frequency_hz && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Frequency</span>
                    <span>{repetition.dominant_frequency_hz.toFixed(2)} Hz</span>
                  </div>
                )}
                {repetition.rhythm_regularity !== null && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Regularity</span>
                    <RegularityBadge value={repetition.rhythm_regularity} />
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, subtext }) {
  return (
    <div className="bg-surface-700 rounded-lg p-3">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className="text-xl font-medium">{value}</div>
      {subtext && <div className="text-xs text-gray-500 mt-1">{subtext}</div>}
    </div>
  );
}

function IntensityGraph({ timeline, currentTime, duration }) {
  if (!timeline || timeline.length === 0) {
    return <div className="h-32 bg-surface-700 rounded flex items-center justify-center text-gray-500 text-sm">No data</div>;
  }

  const maxIntensity = Math.max(...timeline.map(p => p.intensity), 1);
  const width = 100;
  const height = 32;
  
  const points = timeline.map((point, i) => {
    const x = (point.time / duration) * width;
    const y = height - (point.intensity / maxIntensity) * height;
    return `${x},${y}`;
  }).join(' ');

  const currentX = (currentTime / duration) * 100;

  return (
    <div className="h-32 bg-surface-700 rounded p-2 relative">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full" preserveAspectRatio="none">
        <defs>
          <linearGradient id="intensityGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#00ff9f" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#00ff9f" stopOpacity="0.1" />
          </linearGradient>
        </defs>
        <polygon
          points={`0,${height} ${points} ${width},${height}`}
          fill="url(#intensityGradient)"
        />
        <polyline
          points={points}
          fill="none"
          stroke="#00ff9f"
          strokeWidth="0.5"
        />
      </svg>
      <div 
        className="absolute top-0 bottom-0 w-px bg-white/50"
        style={{ left: `${currentX}%` }}
      />
      <div className="absolute bottom-1 left-2 text-xs text-gray-500">0:00</div>
      <div className="absolute bottom-1 right-2 text-xs text-gray-500">{formatDuration(duration)}</div>
    </div>
  );
}

function HotZonesGrid({ zones }) {
  if (!zones) return null;

  const zoneOrder = ['tl', 'tc', 'tr', 'ml', 'mc', 'mr', 'bl', 'bc', 'br'];
  const maxZone = Math.max(...Object.values(zones), 1);

  return (
    <div className="grid grid-cols-3 gap-1">
      {zoneOrder.map(zone => {
        const value = zones[zone] || 0;
        const intensity = value / maxZone;
        const bgOpacity = 0.1 + (intensity * 0.8);
        
        return (
          <div
            key={zone}
            className="aspect-square rounded flex items-center justify-center text-xs transition-all duration-150"
            style={{ 
              backgroundColor: `rgba(0, 255, 159, ${bgOpacity})`,
              color: intensity > 0.5 ? '#0a0a0b' : '#9ca3af'
            }}
          >
            {value > 0 ? `${Math.round(value)}%` : ''}
          </div>
        );
      })}
    </div>
  );
}

function RegularityBadge({ value }) {
  if (value === null || value === undefined) return <span className="text-gray-500">—</span>;
  
  let label, colorClass;
  if (value >= 0.7) {
    label = 'High';
    colorClass = 'bg-green-500/20 text-green-400';
  } else if (value >= 0.4) {
    label = 'Medium';
    colorClass = 'bg-yellow-500/20 text-yellow-400';
  } else {
    label = 'Low';
    colorClass = 'bg-red-500/20 text-red-400';
  }

  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${colorClass}`}>
      {label} ({(value * 100).toFixed(0)}%)
    </span>
  );
}

function formatDuration(seconds) {
  if (!seconds && seconds !== 0) return '—';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60).toString().padStart(2, '0');
  return `${mins}:${secs}`;
}

function BackIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M10 19l-7-7m0 0l7-7m-7 7h18"
      />
    </svg>
  );
}

function PlayIcon() {
  return (
    <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
      <path d="M8 5v14l11-7z" />
    </svg>
  );
}

function PauseIcon() {
  return (
    <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
      <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
    </svg>
  );
}

export default PlaybackView;
