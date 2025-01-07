import singlestoredb as db
from config import Config
import bcrypt

class Database:
    def __init__(self):
        self.conn = None
        self.connect()
        self.drop_tables()
        self.create_tables()

    def drop_tables(self):
        """Drop existing tables to recreate with new schema"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("DROP TABLE IF EXISTS earnings")  # Drop earnings first due to potential foreign key
            cursor.execute("DROP TABLE IF EXISTS children")
            cursor.execute("DROP TABLE IF EXISTS parents")
            self.conn.commit()
        except Exception as e:
            print(f"Error dropping tables: {e}")

    def connect(self):
        try:
            self.conn = db.connect(
                host=Config.DB_HOST,
                port=int(Config.DB_PORT),
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME
            )
        except Exception as e:
            print(f"Database connection error: {e}")
            raise

    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Create parents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parents (
                id INT AUTO_INCREMENT,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                child_email VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id, email),
                INDEX parent_email_idx (email)
            )
        """)
        
        # Create children table with financial fields
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS children (
                id INT AUTO_INCREMENT,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                parent_email VARCHAR(100),
                monthly_allowance DECIMAL(10,2) DEFAULT 0.00,
                balance DECIMAL(10,2) DEFAULT 0.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id, email),
                INDEX child_email_idx (email)
            )
        """)
        
        # Create earnings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS earnings (
                id INT AUTO_INCREMENT,
                child_email VARCHAR(100) NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id)
            )
        """)
        
        self.conn.commit()

    def create_parent(self, name, email, password, child_email):
        cursor = self.conn.cursor()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        try:
            # First check if email already exists
            cursor.execute("SELECT id FROM parents WHERE email = %s", (email,))
            if cursor.fetchone():
                print("Email already exists")
                return False
            
            cursor.execute("""
                INSERT INTO parents (name, email, password_hash, child_email)
                VALUES (%s, %s, %s, %s)
            """, (name, email, password_hash, child_email))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error creating parent: {e}")
            return False

    def create_child(self, name, email, password, parent_email):
        cursor = self.conn.cursor()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        try:
            # First check if email already exists
            cursor.execute("SELECT id FROM children WHERE email = %s", (email,))
            if cursor.fetchone():
                print("Email already exists")
                return False
            
            cursor.execute("""
                INSERT INTO children (name, email, password_hash, parent_email)
                VALUES (%s, %s, %s, %s)
            """, (name, email, password_hash, parent_email))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error creating child: {e}")
            return False

    def verify_parent(self, email, password):
        cursor = self.conn.cursor()
        cursor.execute("SELECT password_hash, name FROM parents WHERE email = %s", (email,))
        result = cursor.fetchone()
        
        if result and bcrypt.checkpw(password.encode('utf-8'), result[0].encode('utf-8')):
            return {'name': result[1]}
        return None

    def verify_child(self, email, password):
        cursor = self.conn.cursor()
        cursor.execute("SELECT password_hash, name FROM children WHERE email = %s", (email,))
        result = cursor.fetchone()
        
        if result and bcrypt.checkpw(password.encode('utf-8'), result[0].encode('utf-8')):
            return {'name': result[1]}
        return None

    def close(self):
        if self.conn:
            self.conn.close()

    def get_children_for_parent(self, parent_email):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name, email 
            FROM children 
            WHERE parent_email = %s
        """, (parent_email,))
        return cursor.fetchall() 

    def get_child_details(self, child_email):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name, email, monthly_allowance, balance 
            FROM children 
            WHERE email = %s
        """, (child_email,))
        return cursor.fetchone()

    def update_monthly_allowance(self, child_email, new_amount):
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                UPDATE children 
                SET monthly_allowance = %s 
                WHERE email = %s
            """, (new_amount, child_email))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating allowance: {e}")
            return False

    def add_earnings(self, child_email, amount, description):
        cursor = self.conn.cursor()
        try:
            # Add earnings record
            cursor.execute("""
                INSERT INTO earnings (child_email, amount, description, created_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            """, (child_email, amount, description))
            
            # Update child's balance
            cursor.execute("""
                UPDATE children 
                SET balance = balance + %s 
                WHERE email = %s
            """, (amount, child_email))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error adding earnings: {e}")
            return False

    def get_earnings_history(self, child_email):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT amount, description, created_at 
            FROM earnings 
            WHERE child_email = %s 
            ORDER BY created_at DESC
        """, (child_email,))
        return cursor.fetchall() 