from flask import Flask, render_template, request, redirect, session
import sqlite3
import datetime
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "secret123"

# Upload folder create karo agar na ho
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# DATABASE
def init_db():
    conn = sqlite3.connect('school.db')
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_start TEXT,
        session_end TEXT,
        name TEXT,
        surname TEXT,
        place_of_birth TEXT,
        last_school TEXT,
        dob TEXT,
        gender TEXT,
        nationality TEXT,
        religion TEXT,
        address TEXT,
        father TEXT,
        mother TEXT,
        father_cnic TEXT,
        mother_cnic TEXT,
        father_profession TEXT,
        mother_profession TEXT,
        mobile TEXT,
        mother_mobile TEXT,
        admission_date TEXT,
        student_class TEXT,
        gr_number TEXT,
        photo TEXT
    )
    ''')
    conn.commit()
    conn.close()

init_db()

# LOGIN
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'Admin' and password == '135246':
            session['user'] = username
            return redirect('/dashboard')
        else:
            return "Invalid Login"
    return render_template('login.html')

# DASHBOARD
@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        return render_template('dashboard.html')
    return redirect('/login')

# ADMISSION
@app.route('/admission', methods=['GET', 'POST'])
def admission():

    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':

        photo = request.files.get('photo')
        photo_filename = None

        # PHOTO SAVE
        if photo and photo.filename != '':
            filename = secure_filename(photo.filename)

            photo.save(
                os.path.join(app.config['UPLOAD_FOLDER'], filename)
            )

            photo_filename = filename

        data = request.form
        print("CLASS SAVED:", data.get('student_class'))

        conn = sqlite3.connect('school.db')
        c = conn.cursor()

        # CLASS
        student_class = data.get('student_class') or ''

        c.execute(
            "SELECT COUNT(*) FROM students WHERE student_class=?",
            (student_class,)
        )

        result = c.fetchone()
        count = result[0] + 1 if result else 1

        # GR NUMBER
        if student_class == "Nursery":
            class_code = "N"

        elif student_class == "KG":
            class_code = "K"
        else:
            # 8th -> 8, 4th -> 4
            class_code = ''.join(filter(str.isdigit, student_class))
            if not class_code:
                class_code = "X"


        gr_number = f"{class_code}{count:03}{str(datetime.datetime.now().year)[2:]}"

        # DUPLICATE CHECK
        c.execute('''
            SELECT * FROM students
            WHERE name = ?
            AND father = ?
            AND dob = ?
            AND father_cnic = ?
            AND address = ?
        ''', (

            data.get('name'),
            data.get('father'),
            data.get('dob'),
            data.get('father_cnic'),
            data.get('address')

        ))

        existing_student = c.fetchone()

        if existing_student:

            conn.close()

            return '''
            <h2 style="
            color:red;
            text-align:center;
            margin-top:50px;
            font-family:Arial;
            ">
            This student information is already saved in database.
            </h2>
            '''

        # INSERT DATA
        c.execute('''

            INSERT INTO students (

                session_start,
                session_end,

                name,
                surname,

                place_of_birth,
                last_school,

                dob,
                gender,

                nationality,
                religion,

                address,

                father,
                mother,

                father_cnic,
                mother_cnic,

                father_profession,
                mother_profession,

                mobile,
                mother_mobile,

                admission_date,

                student_class,

                gr_number,
                photo

            )

            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )

        ''', (

            data.get('session_start'),
            data.get('session_end'),

            data.get('name'),
            data.get('surname'),

            data.get('place_of_birth'),
            data.get('last_school'),

            data.get('dob'),
            data.get('gender'),

            data.get('nationality'),
            data.get('religion'),

            data.get('address'),

            data.get('father'),
            data.get('mother'),

            data.get('father_cnic'),
            data.get('mother_cnic'),

            data.get('father_profession'),
            data.get('mother_profession'),

            data.get('mobile'),
            data.get('mother_mobile'),

            data.get('admission_date'),

            data.get('student_class'),

            gr_number,
            photo_filename

        ))

        conn.commit()

        student_id = c.lastrowid

        conn.close()

        return redirect(f'/print/{student_id}')

    return render_template('admission.html')



# VIEW ADMISSIONS
@app.route('/view_admissions')
def view_admissions():
    if 'user' not in session:
        return redirect('/login')
    conn = sqlite3.connect('school.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM students ORDER BY id DESC")
    students = c.fetchall()
    conn.close()
    return render_template('view_admissions.html', students=students)

@app.route('/certificate')
def certificate():
    if 'user' not in session:
        return redirect('/login')
    conn = sqlite3.connect('school.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM students ORDER BY name")
    students = c.fetchall()
    conn.close()
    return render_template('certificate_search.html', students=students)

# PRINT PAGE
@app.route('/print/<int:id>')
def print_page(id):
    conn = sqlite3.connect('school.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM students WHERE id=?", (id,))
    student = c.fetchone()
    conn.close()

    if student:
        student = dict(student)
    else:
        student = {}

    return render_template('print.html', s=student)

@app.route('/generate_leaving_certificate/<int:id>', methods=['GET', 'POST'])
def generate_leaving_certificate(id):
    conn = sqlite3.connect('school.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM students WHERE id=?", (id,))
    student = c.fetchone()
    if request.method == 'POST':
        certificate_data = {

            'certificate_no': request.form.get('certificate_no'),

            'last_school': request.form.get('last_school'),

            'progress': request.form.get('progress'),

            'conduct': request.form.get('conduct'),

            'attendance': request.form.get('attendance'),

            'leaving_date': request.form.get('leaving_date'),

            'studied_until': request.form.get('studied_until'),

            'reason': request.form.get('reason'),

            'remarks': request.form.get('remarks'),

            'dob_words': request.form.get('dob_words')

        }

        conn.close()
        return render_template('certificate_form.html', s=student, c=certificate_data)

    conn.close()
    return render_template('certificate_form.html', s=student)

# LOGOUT
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')

# RUN
if __name__ == '__main__':
    app.run(host="0.0.0.0",port=10000)
