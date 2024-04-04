
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image
import tensorflow as tf
from keras.preprocessing import image
import numpy as np

app = Flask(__name__)
app.secret_key = 'Srikanth'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)

MODEL_PATH = r'api/static/models/model.h5'

def load_model_and_predict(image_file, model_path):
    # Load the pre-trained model
    loaded_model = tf.keras.models.load_model(model_path)

    # Load and preprocess an image for classification
    img = Image.open(image_file)
    
    # Convert grayscale image to RGB
    img_rgb = Image.new("RGB", img.size)
    img_rgb.paste(img)
    
    img = img_rgb.resize((150, 150))  # Resize the image to match the model's input shape
    img_array = np.array(img) / 255.0  # Convert image to numpy array and normalize

    # Make predictions
    predictions = loaded_model.predict(np.expand_dims(img_array, axis=0))

    # Determine the class label based on the prediction
    if predictions[0][0] > 0.5:
        return "The Patient has Pneumonia"
    else:
        return "The patient is Normal"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        phone_number = request.form['phone_number']
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return "User already exists!"
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password, phone_number=phone_number)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('signin&up.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            return "Invalid email or password"
    return render_template('signin&up.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST' and 'image' in request.files:
        image_file = request.files['image']
        if image_file.filename != '':
            result = load_model_and_predict(image_file, MODEL_PATH)
            user_id = session.get('user_id')
            if user_id:
                user = User.query.get(user_id)
                return render_template('dashboard.html', user=user, result=result)
            else:
                return redirect(url_for('login'))
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        return render_template('dashboard.html', user=user)
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))
