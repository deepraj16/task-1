from flask import Flask, Response, render_template_string, request, redirect, url_for, flash
import psycopg2
import psycopg2.extras
import base64
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for flash messages

# Database config
DB_CONFIG = {
    "host": "dpg-d0apcb15pdvs73c0u030-a.oregon-postgres.render.com",
    "port": 5432,
    "database": "image_store_8qam",
    "user": "image_store_8qam_user",
    "password": "pVZT7u3IdvZMjeEHmZeIhuLmk4QiFrHN"
}

# HTML template with CRUD functionality
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Webcam Image Manager</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { display: flex; justify-content: space-between; align-items: center; }
        .images-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; margin-top: 20px; }
        .image-card { border: 1px solid #ddd; border-radius: 4px; overflow: hidden; }
        .image-card img { width: 100%; height: 250px; object-fit: cover; }
        .image-info { padding: 10px; }
        .image-actions { display: flex; gap: 10px; padding: 10px; }
        .btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; text-align: center; }
        .btn-primary { background-color: #007bff; color: white; }
        .btn-danger { background-color: #dc3545; color: white; }
        .btn-warning { background-color: #ffc107; color: black; }
        .btn-view { background-color: #17a2b8; color: white; }
        .flash-messages { padding: 10px; margin-bottom: 20px; }
        .flash-message { padding: 10px; margin-bottom: 10px; border-radius: 4px; }
        .flash-success { background-color: #d4edda; color: #155724; }
        .flash-error { background-color: #f8d7da; color: #721c24; }
        .modal { display: none; position: fixed; z-index: 1; left: 0; top: 0; width: 100%; height: 100%; overflow: auto; background-color: rgba(0,0,0,0.4); }
        .modal-content { background-color: #fefefe; margin: 10% auto; padding: 20px; border: 1px solid #888; width: 50%; max-width: 500px; }
        .close { color: #aaa; float: right; font-size: 28px; font-weight: bold; cursor: pointer; }
        .close:hover { color: black; }
        .form-group { margin-bottom: 15px; }
        .form-control { width: 100%; padding: 8px; box-sizing: border-box; }
        .form-label { display: block; margin-bottom: 5px; }
        .image-view { max-width: 100%; max-height: 80vh; margin: 0 auto; display: block; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Webcam Image Manager</h1>
            <button class="btn btn-primary" onclick="showUploadModal()">Upload New Image</button>
        </div>

        <!-- Flash Messages -->
        {% if get_flashed_messages() %}
        <div class="flash-messages">
            {% for category, message in get_flashed_messages(with_categories=true) %}
                <div class="flash-message flash-{{ category }}">{{ message }}</div>
            {% endfor %}
        </div>
        {% endif %}

        <!-- Images Grid -->
        <div class="images-grid">
            {% for image in images %}
            <div class="image-card">
                <img src="{{ url_for('get_image', image_id=image.id) }}" alt="Image {{ image.id }}">
                <div class="image-info">
                    <p><strong>ID:</strong> {{ image.id }}</p>
                    <p><strong>Created:</strong> {{ image.created_at.strftime('%Y-%m-%d %H:%M:%S') }}</p>
                    {% if image.description %}
                    <p><strong>Description:</strong> {{ image.description }}</p>
                    {% endif %}
                </div>
                <div class="image-actions">
                    <a href="{{ url_for('view_image', image_id=image.id) }}" class="btn btn-view">View</a>
                    <a href="{{ url_for('edit_image', image_id=image.id) }}" class="btn btn-warning">Edit</a>
                    <a href="{{ url_for('delete_image', image_id=image.id) }}" class="btn btn-danger" onclick="return confirm('Are you sure you want to delete this image?');">Delete</a>
                </div>
            </div>
            {% else %}
            <p>No images found in the database.</p>
            {% endfor %}
        </div>
    </div>

    <!-- Upload Modal -->
    <div id="uploadModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeUploadModal()">&times;</span>
            <h2>Upload New Image</h2>
            <form action="{{ url_for('upload_image') }}" method="POST" enctype="multipart/form-data">
                <div class="form-group">
                    <label class="form-label" for="image">Select Image:</label>
                    <input type="file" class="form-control" id="image" name="image" accept="image/*" required>
                </div>
                <div class="form-group">
                    <label class="form-label" for="description">Description (optional):</label>
                    <textarea class="form-control" id="description" name="description" rows="3"></textarea>
                </div>
                <button type="submit" class="btn btn-primary">Upload</button>
            </form>
        </div>
    </div>

    <script>
        // Modal functions
        function showUploadModal() {
            document.getElementById('uploadModal').style.display = 'block';
        }
        
        function closeUploadModal() {
            document.getElementById('uploadModal').style.display = 'none';
        }
        
        // Close modal when clicking outside of it
        window.onclick = function(event) {
            const modal = document.getElementById('uploadModal');
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        }
    </script>
</body>
</html>
'''

# Single image view template
IMAGE_VIEW_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>View Image</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { display: flex; justify-content: space-between; align-items: center; }
        .btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; }
        .btn-primary { background-color: #007bff; color: white; }
        .image-container { margin-top: 20px; text-align: center; }
        .image-view { max-width: 100%; max-height: 80vh; }
        .image-info { margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>View Image</h1>
            <a href="{{ url_for('index') }}" class="btn btn-primary">Back to Gallery</a>
        </div>

        <div class="image-container">
            <img src="{{ url_for('get_image', image_id=image.id) }}" alt="Image {{ image.id }}" class="image-view">
        </div>

        <div class="image-info">
            <p><strong>ID:</strong> {{ image.id }}</p>
            <p><strong>Created:</strong> {{ image.created_at.strftime('%Y-%m-%d %H:%M:%S') }}</p>
            {% if image.description %}
            <p><strong>Description:</strong> {{ image.description }}</p>
            {% endif %}
        </div>
    </div>
</body>
</html>
'''

# Edit image template
EDIT_IMAGE_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Edit Image</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .header { display: flex; justify-content: space-between; align-items: center; }
        .btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; text-align: center; }
        .btn-primary { background-color: #007bff; color: white; }
        .btn-secondary { background-color: #6c757d; color: white; }
        .form-group { margin-bottom: 15px; }
        .form-control { width: 100%; padding: 8px; box-sizing: border-box; }
        .form-label { display: block; margin-bottom: 5px; }
        .image-preview { max-width: 100%; max-height: 300px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Edit Image</h1>
            <a href="{{ url_for('index') }}" class="btn btn-secondary">Cancel</a>
        </div>

        <img src="{{ url_for('get_image', image_id=image.id) }}" alt="Image {{ image.id }}" class="image-preview">

        <form action="{{ url_for('update_image', image_id=image.id) }}" method="POST" enctype="multipart/form-data">
            <div class="form-group">
                <label class="form-label" for="description">Description:</label>
                <textarea class="form-control" id="description" name="description" rows="3">{{ image.description or '' }}</textarea>
            </div>
            <div class="form-group">
                <label class="form-label" for="new_image">Replace Image (optional):</label>
                <input type="file" class="form-control" id="new_image" name="new_image" accept="image/*">
            </div>
            <button type="submit" class="btn btn-primary">Save Changes</button>
        </form>
    </div>
</body>
</html>
'''

def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    return conn

# Make sure the table has all required fields
def ensure_table_schema():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if description column exists, if not add it
    cursor.execute("""
    SELECT column_name FROM information_schema.columns 
    WHERE table_name='webcam_images' AND column_name='description'
    """)
    if not cursor.fetchone():
        cursor.execute("ALTER TABLE webcam_images ADD COLUMN description TEXT")
    
    cursor.close()
    conn.close()

@app.route("/")
def index():
    ensure_table_schema()
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT id, created_at, description FROM webcam_images ORDER BY created_at DESC")
    images = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template_string(HTML_TEMPLATE, images=images)

@app.route("/image/<int:image_id>")
def get_image(image_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT image FROM webcam_images WHERE id = %s", (image_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if result and result[0]:
        return Response(result[0], mimetype='image/jpeg')
    else:
        return "Image not found", 404

@app.route("/view/<int:image_id>")
def view_image(image_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT id, created_at, description FROM webcam_images WHERE id = %s", (image_id,))
    image = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if image:
        return render_template_string(IMAGE_VIEW_TEMPLATE, image=image)
    else:
        flash("Image not found", "error")
        return redirect(url_for('index'))

@app.route("/edit/<int:image_id>")
def edit_image(image_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT id, created_at, description FROM webcam_images WHERE id = %s", (image_id,))
    image = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if image:
        return render_template_string(EDIT_IMAGE_TEMPLATE, image=image)
    else:
        flash("Image not found", "error")
        return redirect(url_for('index'))

@app.route("/update/<int:image_id>", methods=['POST'])
def update_image(image_id):
    description = request.form.get('description', '')
    new_image = request.files.get('new_image')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if new_image and new_image.filename:
        # Update both image and description
        image_data = new_image.read()
        cursor.execute(
            "UPDATE webcam_images SET image = %s, description = %s WHERE id = %s",
            (image_data, description, image_id)
        )
    else:
        # Update only description
        cursor.execute(
            "UPDATE webcam_images SET description = %s WHERE id = %s",
            (description, image_id)
        )
    
    cursor.close()
    conn.close()
    
    flash("Image updated successfully", "success")
    return redirect(url_for('index'))

@app.route("/delete/<int:image_id>")
def delete_image(image_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM webcam_images WHERE id = %s", (image_id,))
    cursor.close()
    conn.close()
    
    flash("Image deleted successfully", "success")
    return redirect(url_for('index'))

@app.route("/upload", methods=['POST'])
def upload_image():
    image_file = request.files.get('image')
    description = request.form.get('description', '')
    
    if not image_file:
        flash("No image uploaded", "error")
        return redirect(url_for('index'))
    
    image_data = image_file.read()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO webcam_images (image, description, created_at) VALUES (%s, %s, %s)",
        (image_data, description, datetime.now())
    )
    cursor.close()
    conn.close()
    
    flash("Image uploaded successfully", "success")
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)