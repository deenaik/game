import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = 'your-very-secure-secret-key-here'
    DB_HOST = 'svc-3482219c-a389-4079-b18b-d50662524e8a-shared-dml.aws-virginia-6.svc.singlestore.com'
    DB_PORT = '3333'
    DB_USER = 'game'
    DB_PASSWORD = 'password'
    DB_NAME = 'db_deepak_34363'
