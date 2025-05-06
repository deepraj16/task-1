import os
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import base64

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://book_4saj_user:SIQZ2sIESiuwlcJN68frvpXgeuDw3MGW@dpg-cso932hu0jms7394f68g-a.oregon-postgres.render.com/book_4saj")
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://book_4saj_user:SIQZ2sIESiuwlcJN68frvpXgeuDw3MGW@dpg-cso932hu0jms7394f68g-a.oregon-postgres.render.com/book_4saj?sslmode=require"

# Add SSL requirements for PostgreSQL connection
if DATABASE_URL.startswith('postgresql'):
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    # Add SSL mode to handle connection issues
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "connect_args": {
            "sslmode": "require",
            "application_name": "flask_image_app",
            # Increasing timeout values can help with unstable connections
            "connect_timeout": 30
        },
        # Configure pool settings for better reliability
        "pool_pre_ping": True,
        "pool_recycle": 300,  # Recycle connections every 5 minutes
        "pool_timeout": 30,
        "max_overflow": 15
    }
else:
    # Fallback to SQLite for local development if PostgreSQL fails
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///images.db"
    print("Warning: Using SQLite as fallback database")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Upload configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize database
db = SQLAlchemy(app)

# Define Image model
class Image(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    data = db.Column(db.LargeBinary, nullable=False)  # Store image data directly in DB

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app.route('/')
def index():
    """Display all images"""
    images = Image.query.order_by(Image.created_at.desc()).all()
    return render_template('index.html', images=images)

@app.route('/upload', methods=['GET', 'POST'])
def upload_image():
    """Upload a new image"""
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        
        # If user does not select file, browser submits an empty file
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            title = request.form.get('title', '')
            description = request.form.get('description', '')
            
            # Read file data
            file_data = file.read()
            
            # Create new image entry
            new_image = Image(
                filename=filename,
                title=title,
                description=description,
                data=file_data,
                mimetype=file.content_type
            )
            
            db.session.add(new_image)
            db.session.commit()
            
            flash('Image successfully uploaded')
            return redirect(url_for('index'))
    
    return render_template('upload.html')

@app.route('/images/<image_id>')
def view_image(image_id):
    """View a single image"""
    image = Image.query.get_or_404(image_id)
    # Convert binary data to base64 for displaying in HTML
    image_data = base64.b64encode(image.data).decode('utf-8')
    return render_template('view.html', image=image, image_data=image_data)

@app.route('/images/<image_id>/edit', methods=['GET', 'POST'])
def edit_image(image_id):
    """Edit image details"""
    image = Image.query.get_or_404(image_id)
    
    if request.method == 'POST':
        image.title = request.form.get('title', '')
        image.description = request.form.get('description', '')
        
        # Check if a new file was uploaded
        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                image.filename = filename
                image.data = file.read()
                image.mimetype = file.content_type
        
        db.session.commit()
        flash('Image updated successfully')
        return redirect(url_for('view_image', image_id=image.id))
    
    image_data = base64.b64encode(image.data).decode('utf-8')
    return render_template('edit.html', image=image, image_data=image_data)

@app.route('/images/<image_id>/delete', methods=['POST'])
def delete_image(image_id):
    """Delete an image"""
    image = Image.query.get_or_404(image_id)
    db.session.delete(image)
    db.session.commit()
    flash('Image deleted successfully')
    return redirect(url_for('index'))

@app.route('/images/<image_id>/raw')
def get_raw_image(image_id):
    """Return the raw image data"""
    image = Image.query.get_or_404(image_id)
    return image.data, 200, {'Content-Type': image.mimetype}

# API routes for CRUD operations
@app.route('/api/images', methods=['GET'])
def api_get_images():
    """Get all images (metadata only)"""
    images = Image.query.order_by(Image.created_at.desc()).all()
    result = []
    for image in images:
        result.append({
            'id': image.id,
            'filename': image.filename,
            'title': image.title,
            'description': image.description,
            'mimetype': image.mimetype,
            'created_at': image.created_at,
            'updated_at': image.updated_at
        })
    return jsonify(result)

@app.route('/api/images/<image_id>', methods=['GET'])
def api_get_image(image_id):
    """Get a single image's metadata"""
    image = Image.query.get_or_404(image_id)
    image_data = base64.b64encode(image.data).decode('utf-8')
    return jsonify({
        'id': image.id,
        'filename': image.filename,
        'title': image.title,
        'description': image.description,
        'mimetype': image.mimetype,
        'data': f"data:{image.mimetype};base64,{image_data}",
        'created_at': image.created_at,
        'updated_at': image.updated_at
    })

@app.route('/api/images', methods=['POST'])
def api_create_image():
    """Create a new image via API"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        title = request.form.get('title', '')
        description = request.form.get('description', '')
        
        file_data = file.read()
        
        new_image = Image(
            filename=filename,
            title=title,
            description=description,
            data=file_data,
            mimetype=file.content_type
        )
        
        db.session.add(new_image)
        db.session.commit()
        
        return jsonify({
            'id': new_image.id,
            'message': 'Image uploaded successfully'
        }), 201
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/api/images/<image_id>', methods=['PUT', 'PATCH'])
def api_update_image(image_id):
    """Update an image via API"""
    image = Image.query.get_or_404(image_id)
    
    if 'title' in request.form:
        image.title = request.form.get('title')
    
    if 'description' in request.form:
        image.description = request.form.get('description')
    
    if 'file' in request.files and request.files['file'].filename != '':
        file = request.files['file']
        
        if allowed_file(file.filename):
            filename = secure_filename(file.filename)
            image.filename = filename
            image.data = file.read()
            image.mimetype = file.content_type
        else:
            return jsonify({'error': 'File type not allowed'}), 400
    
    db.session.commit()
    return jsonify({'message': 'Image updated successfully'})

@app.route('/api/images/<image_id>', methods=['DELETE'])
def api_delete_image(image_id):
    """Delete an image via API"""
    image = Image.query.get_or_404(image_id)
    db.session.delete(image)
    db.session.commit()
    return jsonify({'message': 'Image deleted successfully'})

# Create database tables if they don't exist
def initialize_database():
    """Initialize database with error handling"""
    try:
        with app.app_context():
            db.create_all()
            print("Database tables created successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
        print("\nTrying to connect to fallback SQLite database...")
        # Switch to SQLite as fallback
        app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///images.db"
        try:
            with app.app_context():
                db.create_all()
                print("Fallback database initialized successfully")
        except Exception as e2:
            print(f"Error initializing fallback database: {e2}")
            raise

# Initialize database
initialize_database()

if __name__ == '__main__':
    app.run(debug=True)