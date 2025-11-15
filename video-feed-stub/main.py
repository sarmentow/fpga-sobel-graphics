import cv2
import numpy as np
import pyfakewebcam
import sys
import time

WIDTH, HEIGHT = 640, 480
FPS = 30

def generate_synthetic_sobel_frame(frame_count):    
    """
    Generates a single frame of a moving shape, then applies a Sobel filter.
    This simulates the output of your FPGA.
    """
    
    canvas = np.zeros((HEIGHT, WIDTH), dtype=np.uint8)
    t = frame_count * (1.0 / FPS)
    x = int(WIDTH / 2 + (WIDTH / 3) * np.sin(t * 1.2))
    y = int(HEIGHT / 2 + (HEIGHT / 3) * np.cos(t * 0.7))
    
    cv2.circle(canvas, (x, y), 50, (255, 255, 255), -1)

    sobel_x = cv2.Sobel(canvas, cv2.CV_8U, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(canvas, cv2.CV_8U, 0, 1, ksize=3)
    
    sobel_frame = cv2.addWeighted(sobel_x, 0.5, sobel_y, 0.5, 0)
    
    return sobel_frame

def main():
    if len(sys.argv) < 2:
        print(f"Usage: python3 {sys.argv[0]} /dev/videoX")
        print("Please provide the path to the v4l2loopback device.")
        sys.exit(1)

    device_path = sys.argv[1]

    try:
        fake_cam = pyfakewebcam.FakeWebcam(device_path, WIDTH, HEIGHT)
    except Exception as e:
        print(f"Error: Could not initialize fake webcam at {device_path}.")
        print(f"Did you run 'sudo modprobe v4l2loopback'?")
        print(f"Error details: {e}")
        sys.exit(1)

    print(f"Broadcasting to {device_path} at {FPS} FPS...")
    print("Press Ctrl+C to stop.")

    frame_count = 0
    try:
        while True:
            sobel_frame = generate_synthetic_sobel_frame(frame_count)

            sobel_rgb = cv2.cvtColor(sobel_frame, cv2.COLOR_GRAY2RGB)

            fake_cam.schedule_frame(sobel_rgb)

            time.sleep(1.0 / FPS)
            frame_count += 1

    except KeyboardInterrupt:
        print("\nStopping broadcast.")
    finally:
        pass

if __name__ == "__main__":
    main()