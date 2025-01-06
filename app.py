from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from database import Database
from config import Config

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

# Initialize database only once when the application starts
db = Database()
db.init_db()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def landing():
    if 'user_email' in session:
        if session.get('user_type') == 'parent':
            return redirect(url_for('dashboard'))
        return redirect(url_for('game_home'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Try parent login
        parent = db.verify_parent(email, password)
        if parent:
            session['user_email'] = email
            session['user_type'] = 'parent'
            session['user_name'] = parent['name']
            return redirect(url_for('dashboard'))
        
        # Try child login
        child = db.verify_child(email, password)
        if child:
            session['user_email'] = email
            session['user_type'] = 'child'
            session['user_name'] = child['name']
            return redirect(url_for('game_home'))
        
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/register/<user_type>', methods=['GET', 'POST'])
def register(user_type):
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        related_email = request.form['related_email']
        
        success = False
        if user_type == 'parent':
            success = db.create_parent(name, email, password, related_email)
        else:
            success = db.create_child(name, email, password, related_email)
        
        if success:
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        else:
            flash('Registration failed. Please try again.')
    
    return render_template('register.html', user_type=user_type)

@app.route('/dashboard')
@login_required
def dashboard():
    if session.get('user_type') != 'parent':
        return redirect(url_for('game_home'))
    return render_template('dashboard.html')

@app.route('/game-home')
@login_required
def game_home():
    if session.get('user_type') != 'child':
        return redirect(url_for('dashboard'))
    return render_template('game_home.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True) 