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
                allowance_day INT DEFAULT 1,  # Day of month for allowance
                allowance_start_date DATE,    # When allowance starts
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
                type VARCHAR(20) NOT NULL,    # 'allowance' or 'extra'
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

    def update_monthly_allowance(self, child_email, new_amount, allowance_day, start_date):
        cursor = self.conn.cursor()
        try:
            # Update allowance settings
            cursor.execute("""
                UPDATE children 
                SET monthly_allowance = %s,
                    allowance_day = %s,
                    allowance_start_date = %s
                WHERE email = %s
            """, (new_amount, allowance_day, start_date, child_email))
            
            # Process past allowances if start date is in the past
            self.process_past_allowances(child_email)
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating allowance: {e}")
            return False

    def process_past_allowances(self, child_email):
        cursor = self.conn.cursor()
        try:
            # Get child's allowance details
            cursor.execute("""
                SELECT monthly_allowance, allowance_day, allowance_start_date, email
                FROM children
                WHERE email = %s
            """, (child_email,))
            
            child = cursor.fetchone()
            if not child or not child[2]:  # If no start date, skip
                return
            
            monthly_allowance, allowance_day, start_date, email = child
            
            # Get the last allowance payment date
            cursor.execute("""
                SELECT MAX(created_at)
                FROM earnings
                WHERE child_email = %s AND type = 'allowance'
            """, (child_email,))
            
            last_payment = cursor.fetchone()[0]
            
            # If no previous payments, use start date
            if not last_payment:
                last_payment = start_date
            
            # Calculate all missing allowance payments
            from datetime import datetime, date
            today = date.today()
            current_date = last_payment
            
            while current_date <= today:
                # If it's past the allowance day in the current month
                if current_date.day >= allowance_day:
                    # Add allowance entry
                    cursor.execute("""
                        INSERT INTO earnings 
                        (child_email, amount, description, type, created_at)
                        VALUES (%s, %s, %s, 'allowance', %s)
                    """, (
                        email,
                        monthly_allowance,
                        f"Monthly Allowance for {current_date.strftime('%B %Y')}",
                        datetime(current_date.year, current_date.month, allowance_day)
                    ))
                    
                    # Update balance
                    cursor.execute("""
                        UPDATE children
                        SET balance = balance + %s
                        WHERE email = %s
                    """, (monthly_allowance, email))
                
                # Move to next month
                if current_date.month == 12:
                    current_date = date(current_date.year + 1, 1, allowance_day)
                else:
                    current_date = date(current_date.year, current_date.month + 1, allowance_day)
            
            self.conn.commit()
        except Exception as e:
            print(f"Error processing past allowances: {e}")
            self.conn.rollback()

    def add_earnings(self, child_email, amount, description):
        cursor = self.conn.cursor()
        try:
            # Add earnings record with type 'extra'
            cursor.execute("""
                INSERT INTO earnings (child_email, amount, description, type, created_at)
                VALUES (%s, %s, %s, 'extra', CURRENT_TIMESTAMP)
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
            SELECT amount, description, type, created_at 
            FROM earnings 
            WHERE child_email = %s 
            ORDER BY created_at DESC
        """, (child_email,))
        return cursor.fetchall() 