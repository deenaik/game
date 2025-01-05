from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for sessions and flash messages

# Temporary user storage (replace with database in production)
users = {
    'parents': {},
    'children': {}
}

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
        
        if email in users['parents'] and users['parents'][email]['password'] == password:
            session['user_email'] = email
            session['user_type'] = 'parent'
            return redirect(url_for('dashboard'))
        elif email in users['children'] and users['children'][email]['password'] == password:
            session['user_email'] = email
            session['user_type'] = 'child'
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
        
        if user_type == 'parent':
            users['parents'][email] = {
                'name': name,
                'password': password,
                'child_email': related_email
            }
        else:
            users['children'][email] = {
                'name': name,
                'password': password,
                'parent_email': related_email
            }
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
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