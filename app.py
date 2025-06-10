import pandas as pd
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash,session
from flask_pymongo import PyMongo
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from dotenv import load_dotenv  # Import load_dotenv
import os

# Load environment variables from .env file

load_dotenv(dotenv_path='config.env')

# Flask App Setup
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")  # Get secret key from .env
app.config["MONGO_URI"] = os.getenv("MONGO_URI") 

mongo = PyMongo(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
csrf = CSRFProtect(app)

# Load dataset
df = pd.read_csv("data/output_cleaned.csv").fillna("")

# User Model for Flask-Login
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data.get('_id'))
        self.username = user_data.get('username')
        self.email = user_data.get('email')
        self.data = user_data
    
    def get_id(self):
        return self.id
    
    @staticmethod
    def is_authenticated():
        return True
    
    @staticmethod
    def is_active():
        return True
    
    @staticmethod
    def is_anonymous():
        return False

@login_manager.user_loader
def load_user(user_id):
    try:
        user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if user_data:
            return User(user_data)
        return None
    except Exception as e:
        print(f"Error loading user: {e}")
        return None

# Add  for create a models.py file
class Build:
    def __init__(self, build_data):
        self.id = str(build_data.get('_id'))
        self.user_id = build_data.get('user_id')
        self.name = build_data.get('name', 'Untitled Build')
        self.budget = build_data.get('budget')
        self.use_case = build_data.get('use_case')
        self.components = build_data.get('components', [])
        self.created_at = build_data.get('created_at')
        self.data = build_data
    
    def get_id(self):
        return self.id
    
    def get_total_price(self):
        """Calculate the total price of all components"""
        total = 0
        for component in self.components:
            price = component.get('price', 0)
            if isinstance(price, str):
                # Remove ₹ and commas if price is a string
                price = float(price.replace('₹', '').replace(',', ''))
            total += price
        return total
    
    @staticmethod
    def from_form_data(user_id, form_data, components):
        """Create a Build object from form data"""
        build_data = {
            'user_id': user_id,
            'name': form_data.get('build_name', 'Untitled Build'),
            'budget': form_data.get('budget'),
            'use_case': form_data.get('use_case'),
            'components': components,
            'created_at': pd.Timestamp.now()
        }
        return Build(build_data)
    
    def to_dict(self):
        """Convert to dictionary for database storage"""
        return {
            'user_id': self.user_id,
            'name': self.name,
            'budget': self.budget,
            'use_case': self.use_case,
            'components': self.components,
            'created_at': self.created_at
        }
    

# Registration Form
class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Register")

# Login Form
class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

# Home Page
@app.route("/")
def home():
    if current_user.is_authenticated:
        return render_template("home.html", user=current_user)
    else:
        return render_template("home.html", user=None)  # Or show guest version


# About Page
@app.route('/about')
def about():
    return render_template('about.html')

# AI Build Page
@app.route('/aibuild')
@login_required
def aibuild():
    return render_template('aibuild.html')

# Component Page
@app.route('/component')
@login_required
def component():
    return render_template('compon.html')

# Get Components (Filtered by Type)
@app.route("/get_components")
@login_required
def get_components():
    try:
        part_type = request.args.get("part", "").lower()
        filtered_data = df[df["part"].str.lower() == part_type].to_dict(orient="records") if part_type else df.to_dict(orient="records")
        return jsonify(filtered_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Build Submission
@app.route('/build', methods=['GET', 'POST'])
@login_required
def build():
    if request.method == 'POST':
        try:
            # Get form data
            build_data = {
                'user_id': current_user.id,
                'components': request.form.getlist('components'),
                'created_at': pd.Timestamp.now(),
                'name': request.form.get('build_name', 'Untitled Build')
            }
            
            # Save to database
            build_id = mongo.db.builds.insert_one(build_data).inserted_id
            
            flash("Build submitted successfully!", "success")
            return redirect(url_for('build'))
        
        except Exception as e:
            flash(f"Error submitting build: {str(e)}", "danger")
            return redirect(url_for('build'))
    
    return render_template('build.html')

# The data from  ai build page is store to database when click on save button
@app.route('/save-build', methods=['POST'])
@login_required
def save_build():
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # Validate required fields
        if not all(key in data for key in ['budget', 'use_case', 'components']):
            return jsonify({
                'success': False,
                'message': 'Missing required fields'
            }), 400
        
        # Create build document
        build_data = {
            'user_id': current_user.id,
            'budget': data.get('budget'),
            'use_case': data.get('use_case'),
            'components': data.get('components', []),
            'created_at': pd.Timestamp.now(),
            'name': data.get('build_name', 'Untitled Build')
        }
        
        # For debugging
        app.logger.info(f"Attempting to save build: {build_data}")
        
        # Save to database
        build_id = mongo.db.builds.insert_one(build_data).inserted_id
        
        return jsonify({
            'success': True,
            'message': 'Build saved successfully',
            'build_id': str(build_id)
        })
    
    except Exception as e:
        app.logger.error(f"Error saving build: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
    
 #User Profile
@app.route('/profile')
@login_required
def profile():
    # Get user's builds
    builds_data = list(mongo.db.builds.find({'user_id': current_user.id}))
    user_builds = [Build(build_data) for build_data in builds_data]
    
    return render_template('profile.html', user=current_user, builds=user_builds)


# Add this route for deleting builds (if not already present)
@app.route('/delete-build/<build_id>', methods=['DELETE'])
@login_required
def delete_build(build_id):
    try:
        # Verify the build belongs to the current user
        result = mongo.db.builds.delete_one({
            '_id': ObjectId(build_id),
            'user_id': current_user.id
        })
        
        if result.deleted_count == 1:
            return jsonify({
                'success': True,
                'message': 'Build deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Build not found or not authorized'
            }), 404
            
    except Exception as e:
        app.logger.error(f"Error deleting build: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# for display the saved builds
@app.route('/buildp')
@login_required
def buildp():
    # Get user's builds and convert to Build objects
    builds_data = list(mongo.db.builds.find({'user_id': current_user.id}))
    builds = [Build(build_data) for build_data in builds_data]
    
    return render_template('build.html', builds=builds)

# Login Route
@app.route("/login", methods=["GET", "POST"])
def login():
    # Redirect if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    # Clear any existing flash messages on GET request
    if request.method == 'GET':
        session.pop('_flashes', None)
        
    form = LoginForm()
    if form.validate_on_submit():
        # Find user by username
        user_data = mongo.db.users.find_one({"username": form.username.data})
        
        # Verify password
        if user_data and check_password_hash(user_data["password"], form.password.data):
            user = User(user_data)
            login_user(user)
            
            # Get next page or default to home
            next_page = request.args.get('next')
            flash("Login successful!", "success")
            return redirect(next_page or url_for("home"))
        
        flash("Invalid username or password.", "danger")
    
    return render_template("login.html", form=form)

# Register Route (sign up)
@app.route("/register", methods=["GET", "POST"])
def register():
    # Redirect if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if email or username already exists
        if mongo.db.users.find_one({"email": form.email.data}):
            flash("Email already exists.", "danger")
            return redirect(url_for("register"))
            
        if mongo.db.users.find_one({"username": form.username.data}):
            flash("Username already exists.", "danger")
            return redirect(url_for("register"))
        
        # Create new user
        hashed_password = generate_password_hash(form.password.data)
        new_user = {
            "username": form.username.data,
            "email": form.email.data,
            "password": hashed_password,
            "created_at": pd.Timestamp.now()
        }
        
        # Insert into database
        user_id = mongo.db.users.insert_one(new_user).inserted_id
        new_user['_id'] = user_id
        
        # Log in the new user
        login_user(User(new_user))
        
        flash("Registration successful! You're now logged in.", "success")
        return redirect(url_for("home"))
        
    return render_template("signup.html", form=form)

# Logout Route
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))  # Redirect to homepage

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# Run App
if __name__ == "__main__":
    app.run(debug=True)