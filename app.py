import os
import numpy as np
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.utils import secure_filename
from PIL import Image
import base64
import io
import tensorflow as tf
from tensorflow import keras
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from functools import wraps

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
if not app.secret_key:
    print("Warning: SECRET_KEY not set in environment variables. This is insecure for production.")
    app.secret_key = "some_secret_key"  # Fallback for development

# Configure Database
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'faces.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Set upload folder
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load trained model
try:
    model = keras.models.load_model('face_recognition_model.h5')
    print("DEBUG: Face recognition model loaded successfully.")
    
    if len(model.input_shape) == 4:
        dummy_input = np.zeros((1, model.input_shape[1], model.input_shape[2], model.input_shape[3]), dtype=np.float32)
    elif len(model.input_shape) == 3:
        dummy_input = np.zeros((1, model.input_shape[1], model.input_shape[2]), dtype=np.float32)
    else:
        raise ValueError("Unexpected input shape for the model")
    model(dummy_input)
    print("DEBUG: Face recognition model built successfully.")
except Exception as e:
    model = None
    print(f"DEBUG: Error loading or building face recognition model: {e}")

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    enrollment_number = db.Column(db.String(20), nullable=False, unique=True)  
    features = db.Column(db.LargeBinary, nullable=False)  
    image_path = db.Column(db.String(200))
    photo_id_path = db.Column(db.String(200)) 

    def __repr__(self):
        return f'<User {self.name} ({self.enrollment_number})>'

def preprocess_image(image_path):
    try:
        img = Image.open(image_path).convert("L")
        img = img.resize((64, 64))
        img = np.array(img).reshape(1, 64, 64, 1)
        img = img / 255.0
        return img
    except Exception as e:
        print(f"Error preprocessing image: {e}")
        return None

def extract_features(model, preprocessed_image):
    if model is not None and preprocessed_image is not None:
        try:
            layer_name = model.layers[-2].name
            feature_extractor = keras.Model(inputs=model.inputs, outputs=[model.get_layer(layer_name).output])
            features = feature_extractor(preprocessed_image)
            print(f"Extracted feature shape: {features.shape}")
            return features.numpy().flatten().tobytes()  # Store as bytes in DB
        except Exception as e:
            print(f"DEBUG: Error in extract_features: {e}")
            return None
    return None

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html", filename=None, predicted_class=None)

@app.route('/register', methods=['GET', 'POST'])
def register():
    message = None
    if request.method == 'POST':
        if 'image' not in request.files and 'photo_id' not in request.files: # Corrected condition
            message = 'No image or photo ID part in the request'
        elif 'image' not in request.files:
            message = 'No image part in the request'
        elif 'photo_id' not in request.files:
            message = 'No photo ID part in the request'
        else:
            file = request.files['image']
            photo_id_file = request.files['photo_id'] #photo id file
            name = request.form.get('name')
            enrollment_number = request.form.get('enrollment_number') #added enrollment number

            if file.filename == '' or photo_id_file.filename == '' or not name or not enrollment_number: #added photo_id_file and enrollment_number
                message = 'Please select both an image and a photo ID, and provide your name and enrollment number.'
            elif file and photo_id_file and name and enrollment_number: #added photo_id_file and enrollment_number
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)

                photo_id_filename = secure_filename(photo_id_file.filename) #photo id
                photo_id_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_id_filename) #photo id
                photo_id_file.save(photo_id_path) #photo id

                if model:
                    img = preprocess_image(filepath)
                    if img is not None:
                        features_bytes = extract_features(model, img)
                        if features_bytes:
                            new_user = User(name=name, enrollment_number=enrollment_number, features=features_bytes, image_path=filepath, photo_id_path=photo_id_path) 
                            db.session.add(new_user)
                            try:
                                db.session.commit()
                                message = f'Face registered for {name} with ID {new_user.id} and Enrollment Number {enrollment_number}' 
                                print(f"Registered features for {name} (ID: {new_user.id}):")
                                features = np.frombuffer(features_bytes, dtype=np.float32)
                                print(f"  Shape: {features.shape}")
                                print(f"  First 10 values: {features[:10]}")
                            except Exception as e:
                                db.session.rollback()
                                message = f'Error registering user: {e}'
                        else:
                            message = 'Could not extract features from the image.'
                    else:
                        message = 'Error preprocessing the image for registration.'
                else:
                    message = 'Face recognition model not loaded.'
            else:
                message = 'Please provide an image, a photo ID, your name, and enrollment number.' # Corrected message
    return render_template('register.html', message=message)

@app.route('/verify_capture', methods=['POST'])
def verify_capture():
    print("DEBUG: Entering verify_capture function")
    try:
        data = request.get_json()
        image_data = data['image']

        image_data_part = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data_part)
        image = Image.open(io.BytesIO(image_bytes)).convert("L")
        frame = np.array(image)
        frame_resized = Image.fromarray(frame).resize((64, 64))
        img = np.array(frame_resized).reshape(1, 64, 64, 1)
        img = img / 255.0
        print(f"DEBUG: Output of preprocess_image (verification): {type(img)}, shape: {getattr(img, 'shape', None)}")
        if model:
            print("DEBUG: Model is loaded.")
            query_features_bytes = extract_features(model, img)
            print(f"DEBUG: Output of extract_features (verification bytes): {type(query_features_bytes)}, length: {len(query_features_bytes) if query_features_bytes else None}")
            if query_features_bytes:
                query_features_np = np.frombuffer(query_features_bytes, dtype=np.float32).flatten()
                min_distance = float('inf')
                matched_user = None

                # Query all users for verification without enrollment number
                users = User.query.all()

                if not users:
                    return jsonify({'message': 'No users registered in the database.'})

                closest_match = None
                min_distance = float('inf')
                recognition_threshold = 50

                for user in users:
                    registered_features_np = np.frombuffer(user.features, dtype=np.float32).flatten()
                    distance = np.linalg.norm(registered_features_np - query_features_np)
                    print(f"Distance to {user.name} (ID: {user.id}, Enrollment: {user.enrollment_number}): {distance}")
                    if distance < min_distance:
                        min_distance = distance
                        closest_match = user

                print(f"Minimum Distance: {min_distance}")
                print(f"Recognition Threshold: {recognition_threshold}")

                if closest_match and min_distance < recognition_threshold:
                    return jsonify({'message': f'Face verified. Matched with {closest_match.name} (Enrollment: {closest_match.enrollment_number}).'})
                else:
                    print("DEBUG: Face not recognized logic reached")
                    return jsonify({'message': 'Face not recognized.'})
            else:
                print("DEBUG: Could not extract features during verification")
                return jsonify({'message': 'Could not extract features from the uploaded image for verification.'})
        else:
            print("DEBUG: Model is NOT loaded.")
            return jsonify({'message': 'Model not loaded.'})
    except Exception as e:
        print(f"DEBUG: Outer exception during verification: {e}")
        return jsonify({'error': str(e)})

@app.route('/verify_user', methods=['GET', 'POST'])
def verify_user():
    message = None
    show_auth_button = False
    if request.method == 'POST':
        name = request.form.get('name')
        enrollment_number = request.form.get('enrollment_number')
        user = User.query.filter_by(name=name, enrollment_number=enrollment_number).first()
        if user:
            session['verification_enrollment_number'] = enrollment_number 
            message = f'User {name} with Enrollment Number {enrollment_number} verified. Proceed to authentication.'
            show_auth_button = True
        else:
            message = 'Invalid Name or Enrollment Number.'
    return render_template('verify_user.html', message=message, show_auth_button=show_auth_button)

@app.route('/verify', methods=['GET'])
def verify():
    enrollment_number = session.get('verification_enrollment_number')
    if enrollment_number:
        return render_template('verify.html')
    else:
        return redirect(url_for('verify_user')) 

@app.route('/vote')
def vote():
    return render_template('voting.html')

@app.route('/cast_vote', methods=['POST'])
def cast_vote():
    selected_candidate = request.form.get('candidate')
    # Here you would implement the logic to record the vote
    print(f"Vote cast for: {selected_candidate}")
    return render_template('vote_cast_success.html', candidate=selected_candidate) #fixed variable

@app.route('/vote_cast_success')
def vote_cast_success():
    candidate = request.args.get('candidate', 'unknown')
    return render_template('vote_cast_success.html', candidate=candidate)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/FAQ')
def faq():
    return render_template('FAQ.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
