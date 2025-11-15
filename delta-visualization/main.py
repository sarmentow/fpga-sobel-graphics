import cv2
import numpy as np
import sys

def main():
    if len(sys.argv) < 2:
        print(f"Usage: python3 {sys.argv[0]} <device_index>")
        print("Please provide the video device index (e.g., '2').")
        sys.exit(1)

    try:
        device_index = int(sys.argv[1])
    except ValueError:
        print(f"Error: Device index must be a number. You gave '{sys.argv[1]}'")
        sys.exit(1)

    cap = cv2.VideoCapture(device_index)

    if not cap.isOpened():
        print(f"Error: Could not open video device at index {device_index}.")
        sys.exit(1)

    print(f"Successfully connected to device {device_index}.")
    print("Press 'q' to quit.")

    sobel_previous = None
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    heatmap_accumulator = np.zeros((height, width), dtype=np.float32)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to grab frame.")
            break
        
        sobel_current = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        if sobel_previous is not None:
            delta = cv2.absdiff(sobel_current, sobel_previous)
            decay_rate = 0.95  # Pixels cool off by 5% per frame
            heatmap_accumulator = (heatmap_accumulator * decay_rate) + delta.astype(np.float32)
        
        sobel_previous = sobel_current
        norm_heatmap = cv2.normalize(heatmap_accumulator, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
        visual_heatmap = cv2.applyColorMap(norm_heatmap, cv2.COLORMAP_INFERNO)
        sobel_current_rgb = cv2.cvtColor(sobel_current, cv2.COLOR_GRAY2BGR)        
        combined_display = np.hstack([sobel_current_rgb, visual_heatmap])

        cv2.imshow("Left: Raw Sobel Feed | Right: Generated Heatmap", combined_display)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Consumer stopped.")

if __name__ == "__main__":
    main()