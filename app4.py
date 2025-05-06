from flask import Flask, Response, render_template_string
import psycopg2

app = Flask(__name__)

# Database config
DB_CONFIG = {
    "host": "dpg-d0apcb15pdvs73c0u030-a.oregon-postgres.render.com",
    "port": 5432,
    "database": "image_store_8qam",
    "user": "image_store_8qam_user",
    "password": "pVZT7u3IdvZMjeEHmZeIhuLmk4QiFrHN"
}

# HTML template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Latest Webcam Image</title></head>
<body>
    <h1>Latest Captured Image</h1>
    {% if image_available %}
        <img src="{{ url_for('image') }}" alt="Webcam Image" style="max-width: 100%;">
    {% else %}
        <p>No image found in the database.</p>
    {% endif %}
</body>
</html>
'''

@app.route("/")
def index():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM webcam_images ORDER BY created_at DESC LIMIT 1")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template_string(HTML_TEMPLATE, image_available=bool(result))

@app.route("/image")
def image():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT image FROM webcam_images ORDER BY created_at DESC LIMIT 1")
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result and result[0]:
        return Response(result[0], mimetype='image/jpeg')
    else:
        return "No image found", 404

if __name__ == "__main__":
    app.run(debug=True)
