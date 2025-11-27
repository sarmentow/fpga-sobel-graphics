import serial
import threading
import time
import os
import glob
from tqdm import tqdm
import img_utils

class SerialTransceiver:
    def __init__(self, port, baud=115200):
        self.ser = serial.Serial(port, baud, timeout=0.1)
        self.running = True
        self.mode = 'interactive'
        
        # RX State
        self.rx_video_active = False
        self.rx_frame_count = 0
        self.img_buffer = bytearray()
        self.img_size = 160 * 120
        
        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()

    def _listen(self):
        while self.running:
            try:
                if self.ser.in_waiting:
                    chunk = self.ser.read(self.ser.in_waiting)
                    
                    if self.mode == 'interactive':
                        try:
                            decoded = chunk.decode('utf-8')
                            print(decoded, end="")
                        except:
                            pass
                            
                    elif self.mode == 'image':
                        # In image mode, we just accumulate data.
                        # The main loop (duplex_workflow) checks the buffer size.
                        self.img_buffer.extend(chunk)
                        
                        # Only auto-save if we are in pure Receiver mode
                        if self.rx_video_active and len(self.img_buffer) >= self.img_size:
                            current_data = bytes(self.img_buffer[:self.img_size])
                            img_utils.save_frame(current_data, self.rx_frame_count)
                            if self.rx_frame_count % 5 == 0:
                                print(".", end="", flush=True)
                            self.rx_frame_count += 1
                            self.img_buffer = self.img_buffer[self.img_size:]

            except Exception as e:
                print(f"Error: {e}")
                break

    def send_raw_byte(self, value):
        self.ser.write(bytes([value]))
        
    def send_raw_byte_array(self, data):
        """Sends a full byte array (frame) at once."""
        self.ser.write(data)

    def send_video_folder(self, folder_path):
        files = sorted(glob.glob(os.path.join(folder_path, "*.*")))
        if not files:
            print("No frames to send.")
            return

        print(f"Preparing to send {len(files)} frames...")
        self.mode = 'sending' 
        
        for f in tqdm(files, unit="frame", desc="Transmitting"):
            try:
                raw_pixels = img_utils.process_image(f)
                self.ser.write(raw_pixels)
                time.sleep(0.2) 
            except Exception as e:
                print(f"Error sending {f}: {e}")

        print("\nTransmission complete.")
        self.mode = 'interactive'

    def close(self):
        self.running = False
        self.thread.join()
        self.ser.close()