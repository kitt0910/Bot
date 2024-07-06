import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'super-secret'
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    CORS_ORIGINS = ['http://localhost:3000']