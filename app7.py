from picamera2 import Picamera2
import cv2
import time
import psycopg2
import numpy as np

def capture_image():
    picam2 = Picamera2()

    # Configure camera for still image capture
    config = picam2.create_still_configuration()
    picam2.configure(config)
    picam2.start()

    # Wait for camera to warm up and capture
    time.sleep(2)  # Warm-up delay

    # Capture as RGB image
    frame = picam2.capture_array()
    picam2.close()

    if frame is None or frame.size == 0:
        raise Exception("Failed to capture image")

    # Encode to JPEG
    ret, buffer = cv2.imencode('.jpg', frame)
    if not ret:
        raise Exception("Failed to encode image")

    return buffer.tobytes()


def store_image_in_db(image_bytes):
    conn = psycopg2.connect(
        host="dpg-d0apcb15pdvs73c0u030-a.oregon-postgres.render.com",
        port=5432,
        database="image_store_8qam",
        user="image_store_8qam_user",
        password="pVZT7u3IdvZMjeEHmZeIhuLmk4QiFrHN"
    )
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS webcam_images (
            id SERIAL PRIMARY KEY,
            image BYTEA,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute("INSERT INTO webcam_images (image) VALUES (%s)", (psycopg2.Binary(image_bytes),))
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    try:
        print("Starting image capture every 30 seconds... (Press Ctrl+C to stop)")
        while True:
            try:
                img_data = capture_image()
                store_image_in_db(img_data)
                print("Image captured and stored at", time.strftime("%Y-%m-%d %H:%M:%S"))
            except Exception as cam_err:
                print("Camera error:", cam_err)

            time.sleep(30)

    except KeyboardInterrupt:
        print("Stopped by user.")
    except Exception as e:
        print("Unexpected error:", e)

