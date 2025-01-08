import pytest
from flask import Flask, session
from app import app, db
from database import Database

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        with app.app_context():
            db.drop_tables()
            db.create_tables()
        yield client

def test_landing(client):
    response = client.get('/')
    assert response.status_code == 302
    assert response.location == 'http://localhost/login'

def test_login(client):
    response = client.post('/login', data=dict(email='parent@example.com', password='password'))
    assert response.status_code == 200
    assert b'Invalid credentials' in response.data

def test_register_parent(client):
    response = client.post('/register/parent', data=dict(
        name='Parent',
        email='parent@example.com',
        password='password',
        related_email=''
    ))
    assert response.status_code == 200
    assert b'Registration successful! Please login.' in response.data

def test_register_child(client):
    response = client.post('/register/child', data=dict(
        name='Child',
        email='child@example.com',
        password='password',
        related_email='parent@example.com'
    ))
    assert response.status_code == 200
    assert b'Registration successful! Please login.' in response.data

def test_dashboard(client):
    with client.session_transaction() as sess:
        sess['user_email'] = 'parent@example.com'
        sess['user_type'] = 'parent'
    response = client.get('/dashboard')
    assert response.status_code == 200
    assert b'Parent Dashboard' in response.data

def test_game_home(client):
    with client.session_transaction() as sess:
        sess['user_email'] = 'child@example.com'
        sess['user_type'] = 'child'
    response = client.get('/game-home')
    assert response.status_code == 200
    assert b'Game Home' in response.data

def test_logout(client):
    with client.session_transaction() as sess:
        sess['user_email'] = 'parent@example.com'
    response = client.get('/logout')
    assert response.status_code == 302
    assert response.location == 'http://localhost/login'

def test_child_details(client):
    with client.session_transaction() as sess:
        sess['user_email'] = 'parent@example.com'
        sess['user_type'] = 'parent'
    response = client.get('/child/child@example.com')
    assert response.status_code == 200
    assert b'Child Details' in response.data

def test_update_allowance(client):
    with client.session_transaction() as sess:
        sess['user_email'] = 'parent@example.com'
        sess['user_type'] = 'parent'
    response = client.post('/child/child@example.com/update-allowance', data=dict(
        amount='100',
        allowance_day='1',
        start_date='2023-01-01'
    ))
    assert response.status_code == 302
    assert response.location == 'http://localhost/child/child@example.com'

def test_add_earnings(client):
    with client.session_transaction() as sess:
        sess['user_email'] = 'parent@example.com'
        sess['user_type'] = 'parent'
    response = client.post('/child/child@example.com/add-earnings', data=dict(
        amount='50',
        description='Test earnings'
    ))
    assert response.status_code == 302
    assert response.location == 'http://localhost/child/child@example.com'

def test_create_parent():
    db = Database()
    result = db.create_parent('Parent', 'parent@example.com', 'password', '')
    assert result == True

def test_create_child():
    db = Database()
    result = db.create_child('Child', 'child@example.com', 'password', 'parent@example.com')
    assert result == True

def test_verify_parent():
    db = Database()
    db.create_parent('Parent', 'parent@example.com', 'password', '')
    result = db.verify_parent('parent@example.com', 'password')
    assert result is not None

def test_verify_child():
    db = Database()
    db.create_child('Child', 'child@example.com', 'password', 'parent@example.com')
    result = db.verify_child('child@example.com', 'password')
    assert result is not None

def test_get_children_for_parent():
    db = Database()
    db.create_parent('Parent', 'parent@example.com', 'password', '')
    db.create_child('Child', 'child@example.com', 'password', 'parent@example.com')
    result = db.get_children_for_parent('parent@example.com')
    assert len(result) == 1

def test_get_child_details():
    db = Database()
    db.create_child('Child', 'child@example.com', 'password', 'parent@example.com')
    result = db.get_child_details('child@example.com')
    assert result is not None

def test_update_monthly_allowance():
    db = Database()
    db.create_child('Child', 'child@example.com', 'password', 'parent@example.com')
    result = db.update_monthly_allowance('child@example.com', 100, 1, '2023-01-01')
    assert result == True

def test_add_earnings():
    db = Database()
    db.create_child('Child', 'child@example.com', 'password', 'parent@example.com')
    result = db.add_earnings('child@example.com', 50, 'Test earnings')
    assert result == True

def test_get_earnings_history():
    db = Database()
    db.create_child('Child', 'child@example.com', 'password', 'parent@example.com')
    db.add_earnings('child@example.com', 50, 'Test earnings')
    result = db.get_earnings_history('child@example.com')
    assert len(result) == 1
