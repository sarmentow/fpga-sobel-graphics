#!/usr/bin/env python3
"""
Movement Analyzer Worker
Watches sessions folder, processes videos through Sobel + heatmap pipeline.
Computes movement analytics for repetitive pattern detection.
"""

import os
import sys
import json
import time
import shutil
import glob
import cv2
import numpy as np
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.absolute()
SESSIONS_DIR = SCRIPT_DIR.parent / "sessions"
POLL_INTERVAL = 5

FPGA_WIDTH, FPGA_HEIGHT = 160, 120
SERIAL_PORT = "/dev/ttyUSB1"
BAUD_RATE = 115200
USE_FPGA = False


class JobProcessor:
    def __init__(self):
        self.transceiver = None
    
    def get_video_info(self, video_path):
        """Get video dimensions and FPS. WebM from MediaRecorder often has bad metadata."""
        cap = cv2.VideoCapture(str(video_path))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        reported_fps = cap.get(cv2.CAP_PROP_FPS)
        if reported_fps <= 0 or reported_fps > 120:
            fps = 30.0
        else:
            fps = reported_fps
        
        reported_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if reported_count <= 0:
            frame_count = 0
            while True:
                ret, _ = cap.read()
                if not ret:
                    break
                frame_count += 1
        else:
            frame_count = reported_count
        
        cap.release()
        return width, height, fps, frame_count
    
    def update_job(self, session_path, **updates):
        """Update job.json with new values."""
        job_path = session_path / "job.json"
        
        try:
            with open(job_path, 'r') as f:
                job = json.load(f)
        except:
            job = {}
        
        job.update(updates)
        
        with open(job_path, 'w') as f:
            json.dump(job, f, indent=2)
    
    def compute_periodicity(self, intensity_values, fps):
        """Compute dominant frequency using FFT."""
        if len(intensity_values) < 10:
            return None, None
        
        signal = np.array(intensity_values)
        signal = signal - np.mean(signal)
        
        fft = np.abs(np.fft.rfft(signal))
        freqs = np.fft.rfftfreq(len(signal), 1.0 / fps)
        
        if len(fft) < 2:
            return None, None
        
        fft[0] = 0
        
        peak_idx = np.argmax(fft)
        dominant_freq = freqs[peak_idx]
        
        if dominant_freq > 0:
            return float(dominant_freq), float(fft[peak_idx])
        return None, None
    
    def compute_rhythm_regularity(self, intensity_values, threshold_percentile=75):
        """Compute regularity of movement cycles."""
        if len(intensity_values) < 20:
            return None, 0
        
        signal = np.array(intensity_values)
        threshold = np.percentile(signal, threshold_percentile)
        
        peaks = []
        for i in range(1, len(signal) - 1):
            if signal[i] > threshold and signal[i] > signal[i-1] and signal[i] > signal[i+1]:
                peaks.append(i)
        
        if len(peaks) < 2:
            return None, len(peaks)
        
        intervals = np.diff(peaks)
        if len(intervals) > 0:
            regularity = 1.0 - (np.std(intervals) / np.mean(intervals)) if np.mean(intervals) > 0 else 0
            regularity = max(0, min(1, regularity))
            return float(regularity), len(peaks)
        
        return None, len(peaks)
    
    def compute_hot_zones(self, heatmap, height, width):
        """Analyze which regions have the most movement."""
        third_h = height // 3
        third_w = width // 3
        
        zones = {
            'tl': heatmap[:third_h, :third_w],
            'tc': heatmap[:third_h, third_w:2*third_w],
            'tr': heatmap[:third_h, 2*third_w:],
            'ml': heatmap[third_h:2*third_h, :third_w],
            'mc': heatmap[third_h:2*third_h, third_w:2*third_w],
            'mr': heatmap[third_h:2*third_h, 2*third_w:],
            'bl': heatmap[2*third_h:, :third_w],
            'bc': heatmap[2*third_h:, third_w:2*third_w],
            'br': heatmap[2*third_h:, 2*third_w:]
        }
        
        zone_totals = {name: float(np.sum(zone)) for name, zone in zones.items()}
        total = sum(zone_totals.values())
        
        if total > 0:
            zone_percentages = {name: round((val / total) * 100, 1) for name, val in zone_totals.items()}
        else:
            zone_percentages = {name: 0.0 for name in zones.keys()}
        
        return zone_percentages
    
    def process_session(self, session_path):
        """Process a single session: Sobel filter + movement heatmap + analytics."""
        session_name = session_path.name
        print(f"\n{'='*60}")
        print(f"Processing session: {session_name}")
        print(f"{'='*60}")
        
        original_video = session_path / "original.webm"
        heatmap_video = session_path / "heatmap.webm"
        analytics_file = session_path / "analytics.json"
        
        if not original_video.exists():
            print(f"Error: {original_video} not found")
            self.update_job(session_path, status="error", error="Original video not found")
            return False
        
        width, height, fps, total_frames = self.get_video_info(original_video)
        print(f"Video: {width}x{height} @ {fps:.1f} FPS, {total_frames} frames")
        
        self.update_job(session_path, 
                        status="processing", 
                        total_frames=total_frames, 
                        processed_frames=0)
        
        cap = cv2.VideoCapture(str(original_video))
        
        fourcc = cv2.VideoWriter_fourcc(*'VP80')
        out = cv2.VideoWriter(str(heatmap_video), fourcc, fps, (width, height))
        
        if not out.isOpened():
            print("Error: Could not create output video writer")
            self.update_job(session_path, status="error", error="Failed to create output video")
            cap.release()
            return False
        
        heatmap_accumulator = np.zeros((height, width), dtype=np.float32)
        total_accumulated = np.zeros((height, width), dtype=np.float64)
        previous_sobel = None
        decay_rate = 0.95
        frame_idx = 0
        
        intensity_timeline = []
        zone_timeline = []
        peak_intensity = 0
        peak_frame = 0
        
        sample_interval = max(1, int(fps / 10))
        
        print("Processing frames...")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            sobel = np.sqrt(sobel_x**2 + sobel_y**2)
            sobel = np.uint8(np.clip(sobel, 0, 255))
            
            if previous_sobel is not None:
                delta = cv2.absdiff(sobel, previous_sobel).astype(np.float32)
                heatmap_accumulator = (heatmap_accumulator * decay_rate) + delta
                total_accumulated += delta
            
            previous_sobel = sobel
            
            frame_intensity = float(np.mean(heatmap_accumulator))
            
            if frame_idx % sample_interval == 0:
                intensity_timeline.append({
                    'frame': frame_idx,
                    'time': round(frame_idx / fps, 2),
                    'intensity': round(frame_intensity, 2)
                })
                zone_snapshot = self.compute_hot_zones(heatmap_accumulator, height, width)
                zone_timeline.append({
                    'time': round(frame_idx / fps, 2),
                    'zones': zone_snapshot
                })
            
            if frame_intensity > peak_intensity:
                peak_intensity = frame_intensity
                peak_frame = frame_idx
            
            norm_heatmap = cv2.normalize(heatmap_accumulator, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
            visual_heatmap = cv2.applyColorMap(norm_heatmap, cv2.COLORMAP_INFERNO)
            
            out.write(visual_heatmap)
            
            frame_idx += 1
            
            if frame_idx % 30 == 0:
                self.update_job(session_path, processed_frames=frame_idx)
                progress = (frame_idx / total_frames) * 100 if total_frames > 0 else 0
                print(f"  {frame_idx}/{total_frames} frames ({progress:.1f}%)")
        
        cap.release()
        out.release()
        
        print("Computing analytics...")
        
        intensity_values = [p['intensity'] for p in intensity_timeline]
        
        dominant_freq, freq_strength = self.compute_periodicity(intensity_values, fps / sample_interval)
        rhythm_regularity, cycle_count = self.compute_rhythm_regularity(intensity_values)
        hot_zones = self.compute_hot_zones(total_accumulated, height, width)
        
        avg_intensity = float(np.mean(intensity_values)) if intensity_values else 0
        
        threshold = np.percentile(intensity_values, 75) if intensity_values else 0
        active_area = float(np.mean(total_accumulated > threshold)) * 100 if total_accumulated.size > 0 else 0
        
        analytics = {
            'duration_seconds': round(frame_idx / fps, 2),
            'total_frames': frame_idx,
            'fps': round(fps, 2),
            'resolution': {'width': width, 'height': height},
            'intensity': {
                'average': round(avg_intensity, 2),
                'peak': round(peak_intensity, 2),
                'peak_time': round(peak_frame / fps, 2),
                'peak_frame': peak_frame
            },
            'repetition': {
                'dominant_frequency_hz': round(dominant_freq, 3) if dominant_freq else None,
                'cycles_per_minute': round(dominant_freq * 60, 1) if dominant_freq else None,
                'cycle_count': cycle_count,
                'rhythm_regularity': round(rhythm_regularity, 2) if rhythm_regularity else None
            },
            'hot_zones': hot_zones,
            'active_area_percent': round(active_area, 1),
            'timeline': intensity_timeline,
            'zone_timeline': zone_timeline
        }
        
        with open(analytics_file, 'w') as f:
            json.dump(analytics, f, indent=2)
        
        print(f"Analytics saved to {analytics_file}")
        
        if heatmap_video.exists() and heatmap_video.stat().st_size > 0:
            self.update_job(session_path, 
                            status="done", 
                            processed_frames=frame_idx)
            print(f"Complete! Processed {frame_idx} frames")
            print(f"Output: {heatmap_video}")
            return True
        else:
            self.update_job(session_path, status="error", error="Output video empty")
            return False


def find_pending_jobs(sessions_dir):
    """Find all sessions with pending status."""
    pending = []
    
    if not sessions_dir.exists():
        return pending
    
    for session_path in sessions_dir.iterdir():
        if not session_path.is_dir():
            continue
        
        job_path = session_path / "job.json"
        if not job_path.exists():
            continue
        
        try:
            with open(job_path, 'r') as f:
                job = json.load(f)
            
            if job.get("status") == "pending":
                pending.append(session_path)
        except:
            continue
    
    return pending


def main():
    print("=" * 60)
    print("  Movement Analyzer Worker")
    print("=" * 60)
    print(f"Watching: {SESSIONS_DIR}")
    print(f"Press Ctrl+C to stop")
    print("=" * 60)
    
    processor = JobProcessor()
    
    try:
        while True:
            pending = find_pending_jobs(SESSIONS_DIR)
            
            if pending:
                print(f"\nFound {len(pending)} pending job(s)")
                for session_path in pending:
                    try:
                        processor.process_session(session_path)
                    except Exception as e:
                        print(f"Error processing {session_path.name}: {e}")
                        import traceback
                        traceback.print_exc()
                        processor.update_job(session_path, status="error", error=str(e))
            else:
                print(".", end="", flush=True)
            
            time.sleep(POLL_INTERVAL)
    
    except KeyboardInterrupt:
        print("\n\nWorker stopped.")


if __name__ == "__main__":
    main()
