import time
import os
from datetime import datetime
from picamera import PiCamera

# Directory to save photos
save_dir = "/home/pi/photos"

# Create directory if it doesn't exist
os.makedirs(save_dir, exist_ok=True)

# Initialize camera
camera = PiCamera()
camera.resolution = (1024, 768)

# Optional warm-up
camera.start_preview()
time.sleep(2)
camera.stop_preview()

print("Photo capture script started. Taking a photo every 15 minutes.")

try:
    while True:
        # Timestamp for filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join(save_dir, f"photo_{timestamp}.jpg")
        
        # Capture photo
        camera.capture(filename)
        print(f"Captured: {filename}")
        
        # Wait 15 minutes
        time.sleep(900)

except KeyboardInterrupt:
    print("Photo capture stopped.")