import os, csv
from flask import Flask, redirect, render_template, request, flash, url_for
from sqlalchemy.exc import OperationalError, IntegrityError
from App.models import db, User, Student, Sticker, StudentSticker
from datetime import timedelta

from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt_identity,
    jwt_required,
    current_user,
    set_access_cookies,
    unset_jwt_cookies,
)


def create_app():
  app = Flask(__name__, static_url_path='/static')
  app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
  app.config['TEMPLATES_AUTO_RELOAD'] = True
  app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'data.db')
  app.config['DEBUG'] = True
  app.config['SECRET_KEY'] = 'MySecretKey'
  app.config['PREFERRED_URL_SCHEME'] = 'https'
  app.config['JWT_ACCESS_COOKIE_NAME'] = 'access_token'
  app.config['JWT_REFRESH_COOKIE_NAME'] = 'refresh_token'
  app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
  app.config["JWT_COOKIE_SECURE"] = True
  app.config["JWT_SECRET_KEY"] = "super-secret"
  app.config["JWT_COOKIE_CSRF_PROTECT"] = False
  app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

  app.app_context().push()
  return app


app = create_app()
db.init_app(app)
jwt = JWTManager(app)


@jwt.user_identity_loader
def user_identity_lookup(user):
  return user 


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
  return User.query.get(int(jwt_data["sub"]))


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
  flash("Your session has expired. Please log in again.")
  return redirect(url_for('login'))


def parse_students():
  with open('students.csv', mode='r', encoding='utf-8') as file:
    csv_reader = csv.DictReader(file)
    for row in csv_reader:
      student = Student(
        id=row['ID'],
        first_name=row['FirstName'],
        last_name=row['LastName'],
        programme=row['Programme'],
        start_date=row['YearStarted'],
        profile_pic=row['Picture']
      )
      db.session.add(student)
    db.session.commit()

def create_users():
  users = [
    User(username="rob", password="robpass"),
    User(username="bob", password="bobpass"),
    User(username="sally", password="sallypass"),
    User(username="pam", password="pampass"),
    User(username="chris", password="chrispass")
  ]
  db.session.add_all(users)
  db.session.commit()

def create_stickers():
  stickers = [
    ("Awesome", "awesome.png"),
    ("Cool", "cool.png"),
    ("Bravo", "bravo.png"),
    ("Excellent", "excellent.png"),
    ("Good Job", "good_job.png"),
    ("Thumbs Up", "thumbs_up.png"),
    ("Well Done", "well_done.png"),
    ("Wonderful", "wonderful.png")
  ]
  for name, filename in stickers:
    db.session.add(Sticker(name=name, image=f"/static/stickers/{filename}"))
  db.session.commit()

def initialize_db():
  db.drop_all()
  db.create_all()
  create_users()
  parse_students()
  create_stickers()
  print('Database initialized')


@app.route('/')
def login():
  return render_template('login.html')


@app.route('/login', methods=['POST'])
def login_action():
  username = request.form.get('username')
  password = request.form.get('password')
  user = User.query.filter_by(username=username).first()
  if user and user.check_password(password):
    response = redirect(url_for('home'))
    access_token = create_access_token(identity=str(user.id))  
    set_access_cookies(response, access_token)
    return response
  else:
    flash('Invalid username or password')
    return redirect(url_for('login'))


@app.route('/app')
@app.route('/app/<id>')
@jwt_required()
def home(id=None):
  students = Student.query.all()
  selected_student = Student.query.get(id) if id else None
  stickers = Sticker.query.all()
  awarded = []
  if selected_student:
    awarded = StudentSticker.query.filter_by(student_id=selected_student.id).all()
  return render_template(
    'index.html',
    selected_student=selected_student,
    students=students,
    stickers=stickers,
    awarded=awarded,
    user=current_user
  )


@app.route('/award', methods=['POST'])
@jwt_required()
def award_sticker():
  student_id = request.form.get('student_id')
  sticker_id = request.form.get('sticker_id')
  existing = StudentSticker.query.filter_by(
    student_id=student_id,
    sticker_id=sticker_id
  ).first()
  if existing:
    flash("This student already has that sticker.")
  else:
    award = StudentSticker(
      student_id=student_id,
      sticker_id=sticker_id,
      user_id=current_user.id
    )
    db.session.add(award)
    db.session.commit()
    flash("Sticker awarded!")
  return redirect(url_for('home', id=student_id))


@app.route('/delete/<int:sticker_id>/<student_id>')
@jwt_required()
def delete_sticker(sticker_id, student_id):
  record = StudentSticker.query.filter_by(
    sticker_id=sticker_id,
    student_id=student_id,
    user_id=current_user.id
  ).first()
  if record:
    db.session.delete(record)
    db.session.commit()
    flash("Sticker removed.")
  else:
    flash("You cannot delete this sticker.")
  return redirect(url_for('home', id=student_id))


@app.route('/logout')
def logout():
  response = redirect(url_for('login'))
  unset_jwt_cookies(response)
  flash('logged out')
  return response


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080, debug=True) 
