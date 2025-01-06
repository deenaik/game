import singlestoredb as db
from config import Config
import bcrypt

class Database:
    def __init__(self):
        self.conn = None
        self.connect()

    def init_db(self):
        """Initialize database tables if they don't exist"""
        self.create_tables()

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
        
        # Create parents table with a single composite primary key
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parents (
                id INT AUTO_INCREMENT,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                child_email VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id, email)
            )
        """)
        
        # Create children table with a single composite primary key
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS children (
                id INT AUTO_INCREMENT,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                parent_email VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id, email)
            )
        """)
        
        # Create reference indexes (without IF NOT EXISTS)
        try:
            cursor.execute("""
                CREATE REFERENCE INDEX parent_email_idx ON parents (email)
            """)
        except Exception as e:
            print(f"Index parent_email_idx might already exist: {e}")
        
        try:
            cursor.execute("""
                CREATE REFERENCE INDEX child_email_idx ON children (email)
            """)
        except Exception as e:
            print(f"Index child_email_idx might already exist: {e}")
        
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