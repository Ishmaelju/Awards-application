from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(80), unique=True, nullable=False)
  password = db.Column(db.String(120), nullable=False)

  awarded_stickers = db.relationship('StudentSticker', backref='user', lazy=True)
 
  def __init__(self, username, password):
    self.username = username
    self.set_password(password)

  def set_password(self, password):
    self.password = generate_password_hash(password)

  def check_password(self, password):
    return check_password_hash(self.password, password)

class Student(db.Model):
  id = db.Column(db.String(9), primary_key=True)
  first_name = db.Column(db.String(100), nullable=False)
  last_name = db.Column(db.String(100), nullable=False)
  programme = db.Column(db.String(100), nullable=False)
  start_date = db.Column(db.String(10), nullable=False)
  profile_pic = db.Column(db.String(255), nullable=False)

  stickers = db.relationship('StudentSticker', backref='student', lazy=True)

class Sticker(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), nullable=False)
  image = db.Column(db.String(255), nullable=False)

  awards = db.relationship('StudentSticker', backref='sticker', lazy=True)

class StudentSticker(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  student_id = db.Column(db.String(9), db.ForeignKey('student.id'), nullable=False)
  sticker_id = db.Column(db.Integer, db.ForeignKey('sticker.id'), nullable=False)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  date_awarded = db.Column(db.DateTime, default=datetime.utcnow)
