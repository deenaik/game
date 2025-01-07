from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from database import Database
from config import Config

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

# Initialize database only once when the application starts
db = Database()

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
    
    children = db.get_children_for_parent(session['user_email'])
    return render_template('dashboard.html', children=children)

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

@app.route('/child/<child_email>')
@login_required
def child_details(child_email):
    if session.get('user_type') != 'parent':
        return redirect(url_for('game_home'))
    
    child = db.get_child_details(child_email)
    earnings_history = db.get_earnings_history(child_email)
    
    if not child:
        flash('Child not found')
        return redirect(url_for('dashboard'))
    
    return render_template('child_details.html', child=child, earnings=earnings_history)

@app.route('/child/<child_email>/update-allowance', methods=['POST'])
@login_required
def update_allowance(child_email):
    if session.get('user_type') != 'parent':
        return redirect(url_for('game_home'))
    
    amount = request.form.get('amount')
    allowance_day = request.form.get('allowance_day')
    start_date = request.form.get('start_date')
    
    if db.update_monthly_allowance(child_email, amount, allowance_day, start_date):
        flash('Monthly allowance updated successfully')
    else:
        flash('Failed to update monthly allowance')
    
    return redirect(url_for('child_details', child_email=child_email))

@app.route('/child/<child_email>/add-earnings', methods=['POST'])
@login_required
def add_earnings(child_email):
    if session.get('user_type') != 'parent':
        return redirect(url_for('game_home'))
    
    amount = request.form.get('amount')
    description = request.form.get('description')
    
    if db.add_earnings(child_email, amount, description):
        flash('Earnings added successfully')
    else:
        flash('Failed to add earnings')
    
    return redirect(url_for('child_details', child_email=child_email))

if __name__ == '__main__':
    app.run(debug=True) 