import cv2
import os
import shutil
import glob
from PIL import Image

def capture_from_webcam(output_path="temp_recording.avi", width=640, height=480):
    """
    Opens a window showing the webcam feed. Records to file until 'q' is pressed.
    """
    cap = cv2.VideoCapture(0)
    
    # Define codec and create VideoWriter object
    # MJPG is usually safe for .avi on most systems without extra codecs
    fourcc = cv2.VideoWriter_fourcc(*'MJPG') 
    out = cv2.VideoWriter(output_path, fourcc, 20.0, (width, height))

    print(f"--- Recording to {output_path} ---")
    print("Press 'q' to stop recording.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break
        
        # Resize frame for the window/file if necessary (optional)
        frame = cv2.resize(frame, (width, height))

        # Write the frame
        out.write(frame)

        # Show the frame
        cv2.imshow('Recording - Press q to stop', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print("Recording saved.")
    return output_path

def video_to_frames(video_path, output_folder, target_size=(160, 120), skip_frames=5):
    """
    Reads video, resizes, converts to grayscale, and saves frames.
    skip_frames: Save only every Nth frame to reduce transmission time.
    """
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)
    os.makedirs(output_folder)

    cap = cv2.VideoCapture(video_path)
    count = 0
    saved_count = 0
    
    print("Processing video for transmission...")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Resize
        frame = cv2.resize(frame, target_size)
        # Convert to Grayscale
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Save using PIL logic (so it matches your existing img_utils)
        # Or just save using cv2
        filename = os.path.join(output_folder, f"frame_{saved_count:04d}.png")
        cv2.imwrite(filename, frame)
        saved_count += 1
            

    cap.release()
    print(f"Extracted {saved_count} frames to {output_folder}")
    return saved_count

def frames_to_video(input_folder, output_path, fps=30):
    """
    Stitches a sequence of images back into a video file.
    """
    images = sorted(glob.glob(os.path.join(input_folder, "*.png")))
    
    if not images:
        print("No images found to stitch.")
        return

    # Read first image to get dimensions
    frame = cv2.imread(images[0])
    height, width, layers = frame.shape

    fourcc = cv2.VideoWriter_fourcc(*'mp4v') # or 'XVID'
    video = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    print(f"Stitching {len(images)} frames into {output_path}...")
    
    for image in images:
        video.write(cv2.imread(image))

    cv2.destroyAllWindows()
    video.release()
    print("Video reconstruction complete.")