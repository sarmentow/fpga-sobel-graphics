from PIL import Image
import os

WIDTH, HEIGHT = 160, 120

def process_image(path):
    """Resizes to 160x120, converts to Grayscale (L), returns raw bytes."""
    with Image.open(path) as img:
        img = img.resize((WIDTH, HEIGHT)).convert('L')
        return img.tobytes()

def save_frame(data, frame_count, folder="rx_frames"):
    """Saves a video frame with a sequence number."""
    if not os.path.exists(folder):
        os.makedirs(folder)
        
    if len(data) != WIDTH * HEIGHT:
        print(f"Error: Data length mismatch.")
        return

    filename = os.path.join(folder, f"frame_{frame_count:04d}.png")
    img = Image.frombytes('L', (WIDTH, HEIGHT), data)
    img.save(filename)
    print(f"Saved {filename}")