#!/usr/bin/env python3
"""
Movement Analyzer Worker
Watches sessions folder, processes videos through FPGA Sobel + heatmap pipeline.
Computes movement analytics for repetitive pattern detection.
"""

import os
import sys
import json
import time
import serial
import serial.tools.list_ports
import threading
import cv2
import numpy as np
from pathlib import Path
from PIL import Image

SCRIPT_DIR = Path(__file__).parent.absolute()
SESSIONS_DIR = SCRIPT_DIR.parent / "sessions"
POLL_INTERVAL = 5

FPGA_WIDTH, FPGA_HEIGHT = 160, 120
BAUD_RATE = 115200
FPGA_TIMEOUT = 5.0


def discover_serial_port():
    """Auto-discover available serial port for FPGA."""
    ports = serial.tools.list_ports.comports()
    if not ports:
        return None
    for port in ports:
        if 'USB' in port.device or 'ttyUSB' in port.device or 'ttyACM' in port.device:
            return port.device
    return ports[0].device


class FPGATransceiver:
    """Handles serial communication with the FPGA for Sobel filtering."""
    
    def __init__(self, port, baud=115200):
        self.ser = serial.Serial(port, baud, timeout=0.1)
        self.running = True
        self.img_buffer = bytearray()
        self.img_size = FPGA_WIDTH * FPGA_HEIGHT
        self.lock = threading.Lock()
        
        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()

    def _listen(self):
        while self.running:
            try:
                if self.ser.in_waiting:
                    chunk = self.ser.read(self.ser.in_waiting)
                    with self.lock:
                        self.img_buffer.extend(chunk)
            except Exception as e:
                print(f"Serial error: {e}")
                break
            time.sleep(0.001)

    def send_frame(self, frame_bytes):
        """Send a frame to the FPGA."""
        self.ser.write(frame_bytes)

    def receive_frame(self, timeout=FPGA_TIMEOUT):
        """Wait for a complete frame from the FPGA. Returns bytes or None on timeout."""
        start = time.time()
        while time.time() - start < timeout:
            with self.lock:
                if len(self.img_buffer) >= self.img_size:
                    frame_data = bytes(self.img_buffer[:self.img_size])
                    self.img_buffer = self.img_buffer[self.img_size:]
                    return frame_data
            time.sleep(0.01)
        return None

    def clear_buffer(self):
        """Clear any pending data in the buffer."""
        with self.lock:
            self.img_buffer = bytearray()

    def close(self):
        self.running = False
        self.thread.join(timeout=1.0)
        self.ser.close()


class JobProcessor:
    def __init__(self):
        self.fpga = None
        self.serial_port = None
    
    def connect_fpga(self):
        """Connect to the FPGA. Raises exception on failure."""
        if self.fpga is not None:
            return
        
        self.serial_port = discover_serial_port()
        if not self.serial_port:
            raise RuntimeError("No serial ports found. Is the FPGA connected?")
        
        print(f"Connecting to FPGA on {self.serial_port}...")
        self.fpga = FPGATransceiver(self.serial_port, BAUD_RATE)
        self.fpga.clear_buffer()
        print("FPGA connected.")

    def disconnect_fpga(self):
        """Disconnect from the FPGA."""
        if self.fpga:
            self.fpga.close()
            self.fpga = None
    
    def frame_to_fpga_format(self, frame):
        """Convert BGR frame to 160x120 grayscale bytes for FPGA."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (FPGA_WIDTH, FPGA_HEIGHT))
        return resized.tobytes()
    
    def fpga_response_to_frame(self, data, target_width, target_height):
        """Convert FPGA response bytes to a frame at target resolution."""
        small_frame = np.frombuffer(data, dtype=np.uint8).reshape((FPGA_HEIGHT, FPGA_WIDTH))
        if target_width != FPGA_WIDTH or target_height != FPGA_HEIGHT:
            return cv2.resize(small_frame, (target_width, target_height), interpolation=cv2.INTER_LINEAR)
        return small_frame

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
        """Process a single session: FPGA Sobel filter + movement heatmap + analytics."""
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
        
        try:
            self.connect_fpga()
        except Exception as e:
            error_msg = f"FPGA connection failed: {e}"
            print(f"Error: {error_msg}")
            self.update_job(session_path, status="error", error=error_msg)
            return False
        
        width, height, fps, total_frames = self.get_video_info(original_video)
        print(f"Video: {width}x{height} @ {fps:.1f} FPS, {total_frames} frames")
        print(f"FPGA processing at {FPGA_WIDTH}x{FPGA_HEIGHT}, upscaling back to {width}x{height}")
        
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
        
        print("Processing frames via FPGA...")
        self.fpga.clear_buffer()
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            fpga_input = self.frame_to_fpga_format(frame)
            self.fpga.send_frame(fpga_input)
            
            fpga_response = self.fpga.receive_frame(timeout=FPGA_TIMEOUT)
            
            if fpga_response is None:
                error_msg = f"FPGA timeout at frame {frame_idx}"
                print(f"\nError: {error_msg}")
                self.update_job(session_path, status="error", error=error_msg)
                cap.release()
                out.release()
                if heatmap_video.exists():
                    heatmap_video.unlink()
                return False
            
            sobel = self.fpga_response_to_frame(fpga_response, width, height)
            
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
            
            if frame_idx % 10 == 0:
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
            'fpga_resolution': {'width': FPGA_WIDTH, 'height': FPGA_HEIGHT},
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
    print("  Movement Analyzer Worker (FPGA)")
    print("=" * 60)
    print(f"Watching: {SESSIONS_DIR}")
    
    available_ports = [p.device for p in serial.tools.list_ports.comports()]
    if available_ports:
        print(f"Available ports: {', '.join(available_ports)}")
    else:
        print("Warning: No serial ports detected")
    
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
    finally:
        processor.disconnect_fpga()


if __name__ == "__main__":
    main()
