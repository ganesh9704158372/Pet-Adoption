from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo
from bson import ObjectId
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/pet'  # Update this to your MongoDB URI
app.config['UPLOAD_FOLDER'] = 'static/uploads'
mongo = PyMongo(app)

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class RegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

@app.route('/')
def frontpage():
    return render_template('frontpage.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)  # Remove the method='sha256'
        user = mongo.db.users.find_one({'email': form.email.data})
        if user:
            flash('User already exists!', 'error')
            return redirect(url_for('register'))
        mongo.db.users.insert_one({
            'name': form.name.data,
            'email': form.email.data,
            'password': hashed_password
        })
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = mongo.db.users.find_one({'email': form.email.data})
        if user and check_password_hash(user['password'], form.password.data):
            session['user_id'] = str(user['_id'])
            return redirect(url_for('home'))
        flash('Invalid email or password!', 'error')
    return render_template('login.html', form=form)

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    return render_template('home.html', user=user)

@app.route('/forgot')
def forgot():
    return render_template('forgot.html')


@app.route('/categories')
def categories():
    return render_template('categories.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/service')
def service():
    return render_template('service.html')

@app.route('/adoptform')
def adoptform():
    return render_template('adoptform.html')


@app.route('/addpet', methods=['GET', 'POST'])
def addpet():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        email = request.form['email']
        contact = request.form['contact']
        type_ = request.form['type']

        if 'img' in request.files:
            img = request.files['img']
            if img.filename != '':
                filename = secure_filename(img.filename)
                img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_url = url_for('static', filename='uploads/' + filename)
            else:
                image_url = None
        else:
            image_url = None

        mongo.db.pets.insert_one({
            'name': name,
            'age': age,
            'email': email,
            'contact': contact,
            'type': type_,
            'image': image_url
        })
        flash('Pet added successfully!', 'success')
        return redirect(url_for('view_pets'))
    return render_template('addpet.html')

@app.route('/view_pets')
def view_pets():
    pets = mongo.db.pets.find()
    return render_template('view_pets.html', pets=pets)

@app.route('/edit_pet/<pet_id>', methods=['GET', 'POST'])
def edit_pet(pet_id):
    pet = mongo.db.pets.find_one({'_id': ObjectId(pet_id)})
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        email = request.form['email']
        contact = request.form['contact']
        type_ = request.form['type']

        if 'img' in request.files:
            img = request.files['img']
            if img.filename != '':
                filename = secure_filename(img.filename)
                img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_url = url_for('static', filename='uploads/' + filename)
            else:
                image_url = pet['image']
        else:
            image_url = pet['image']

        mongo.db.pets.update_one({'_id': ObjectId(pet_id)}, {
            '$set': {
                'name': name,
                'age': age,
                'email': email,
                'contact': contact,
                'type': type_,
                'image': image_url
            }
        })
        flash('Pet updated successfully!', 'success')
        return redirect(url_for('view_pets'))
    return render_template('edit_pet.html', pet=pet)

@app.route('/delete_pet/<pet_id>')
def delete_pet(pet_id):
    mongo.db.pets.delete_one({'_id': ObjectId(pet_id)})
    flash('Pet deleted successfully!', 'success')
    return redirect(url_for('view_pets'))

if __name__ == "__main__":
    app.run(debug=True)
