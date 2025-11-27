import argparse
import time
import os
import sys
import serial.tools.list_ports
from transceiver import SerialTransceiver
import video_utils
import img_utils
from tqdm import tqdm

# --- Configuration ---
TEMP_VIDEO = "temp_capture.avi"
TX_FRAMES_DIR = "tx_frames_cache"
RX_FRAMES_DIR = "rx_frames"
FINAL_VIDEO = "processed_video.mp4"
# ---------------------

def list_ports():
    ports = serial.tools.list_ports.comports()
    return [p.device for p in ports]

def sender_workflow(trx):
    """Only sends data. Used if you have two distinct computers/FPGAs."""
    video_path = video_utils.capture_from_webcam(TEMP_VIDEO)
    video_utils.video_to_frames(video_path, TX_FRAMES_DIR, skip_frames=1)
    input("Press Enter to start transmission...")
    trx.send_video_folder(TX_FRAMES_DIR)

def receiver_workflow(trx):
    """Only receives data. Used if you have two distinct computers/FPGAs."""
    print(f"--- Receiver Mode ---")
    if not os.path.exists(RX_FRAMES_DIR):
        os.makedirs(RX_FRAMES_DIR)

    trx.rx_frame_count = 0
    trx.rx_video_active = True
    trx.mode = 'image'

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping reception...")
        trx.rx_video_active = False
        trx.mode = 'interactive'
        video_utils.frames_to_video(RX_FRAMES_DIR, FINAL_VIDEO, fps=6)

def duplex_workflow(trx):
    """
    SINGLE DEVICE MODE (PC -> FPGA -> PC).
    Captures video, sends one frame, waits for response, saves it, repeats.
    """
    # 1. Capture
    video_path = video_utils.capture_from_webcam(TEMP_VIDEO)
    
    # 2. Process to frames
    print("Processing frames...")
    # Skip frames to reduce total transmission time
    video_utils.video_to_frames(video_path, TX_FRAMES_DIR, skip_frames=5)
    
    # 3. Prepare RX folder
    if not os.path.exists(RX_FRAMES_DIR):
        os.makedirs(RX_FRAMES_DIR)
        
    files = sorted(os.listdir(TX_FRAMES_DIR))
    tx_files = [os.path.join(TX_FRAMES_DIR, f) for f in files if f.endswith('.png')]
    
    print(f"--- Starting Duplex Transmission ({len(tx_files)} frames) ---")
    print("Pattern: Send Frame -> Wait for FPGA Reply -> Save -> Next Frame")
    
    trx.mode = 'image' # Ensure we capture incoming bytes to buffer
    
    for i, file_path in enumerate(tqdm(tx_files, unit="frame")):
        # A. Send Frame
        raw_pixels = img_utils.process_image(file_path)
        trx.send_raw_byte_array(raw_pixels)
        
        # B. Wait for Response (Timeout after 5 seconds)
        start_wait = time.time()
        while len(trx.img_buffer) < trx.img_size:
            time.sleep(0.01)
            if time.time() - start_wait > 5.0:
                print(f"\n[Timeout] FPGA did not return frame {i} in time.")
                break
        
        # C. Save Received Frame
        if len(trx.img_buffer) >= trx.img_size:
            # Extract exactly one frame worth of data
            frame_data = bytes(trx.img_buffer[:trx.img_size])
            img_utils.save_frame(frame_data, i, RX_FRAMES_DIR)
            
            # Remove that data from buffer
            trx.img_buffer = trx.img_buffer[trx.img_size:]
        else:
            # If we timed out, we still need to clear buffer or skip
            print("Skipping save for this frame.")
            trx.img_buffer = bytearray()

    # 4. Stitch Video
    print("\nTransmission complete. Stitching video...")
    video_utils.frames_to_video(RX_FRAMES_DIR, FINAL_VIDEO, fps=6)
    print(f"Done! Output saved to: {FINAL_VIDEO}")

def main():
    parser = argparse.ArgumentParser(description="Serial Video Transceiver")
    parser.add_argument("--port", help="Serial port")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--role", choices=['sender', 'receiver', 'duplex'], required=True, 
                        help="'duplex' is for single-PC (Loopback/FPGA) testing.")

    args = parser.parse_args()
    
    port = args.port
    if not port:
        avail = list_ports()
        if not avail:
            print("No ports found.")
            return
        port = avail[0]

    print(f"Opening {port}...")
    try:
        trx = SerialTransceiver(port, args.baud)
    except Exception as e:
        print(f"\n[Error] Could not open serial port {port}.")
        print("Hint: Only ONE program can use the port at a time.")
        return

    try:
        if args.role == 'duplex':
            duplex_workflow(trx)
            
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        trx.close()

if __name__ == "__main__":
    main()