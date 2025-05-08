import cv2
import psycopg2
import time

def capture_image():
    cam = cv2.VideoCapture(0)
    ret, frame = cam.read()
    cam.release()

    if not ret:
        raise Exception("Failed to capture image")

    # Encode image as JPEG
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

    # Create table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS webcam_images (
            id SERIAL PRIMARY KEY,
            image BYTEA,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Insert the image
    cursor.execute("INSERT INTO webcam_images (image) VALUES (%s)", (psycopg2.Binary(image_bytes),))
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    try:
        print("Starting image capture every 30 seconds... (Press Ctrl+C to stop)")
        while True:
            img_data = capture_image()
            store_image_in_db(img_data)
            print("Image captured and stored at", time.strftime("%Y-%m-%d %H:%M:%S"))
            time.sleep(30)
    except KeyboardInterrupt:
        print("Stopped by user.")
    except Exception as e:
        print("Error:", e)
