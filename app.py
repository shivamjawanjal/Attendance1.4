from flask import Flask, render_template, request, redirect, url_for, send_file, session
from config import get_database
import pandas as pd
import time
import os

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key')  # Use environment variable for secret key

# Connect to MongoDB
db = get_database()
collection = db['user']
attend_collection = db['attendance']
users_collection = db['login']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = users_collection.find_one({'username': username, 'password': password})

        if user:
            session['username'] = username  # Store user info in session
            return render_template('studentlogin.html')
        else:
            return render_template('index.html', alertMsg='User does not exist or incorrect password')

    return render_template('index.html')

@app.route('/adminlogin', methods=['GET', 'POST'])
def adminlogin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == 'GPJadmin' and password == 'Kalesir@9022': 
            session['admin'] = True
            return render_template('Admin.html')
        else:
            return render_template('index.html', alertMsg='User does not exist or incorrect password')

    return render_template('Adminlogin.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('admin'):
        return redirect(url_for('adminlogin'))
    return render_template('Adminlogin.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return render_template('Adminlogin.html')

@app.route('/createuser', methods=['POST'])
def create_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if users_collection.find_one({'username': username}):
            return render_template('create.html', alertMsg='User already exists')
        else:
            users_collection.insert_one({'username': username, 'password': password})
            return render_template('index.html')

    return redirect(url_for('student_login'))

@app.route('/create', methods=['POST', 'GET'])
def create():
    return render_template('create.html')

data={}
@app.route('/share', methods=['POST'])
def share():
    if request.method == 'POST':
        className = request.form.get('className')
        date = request.form.get('date')
        code = request.form.get('code')
        data['className'] = className
        data['date'] = date
        data['code'] = code
        data['timestamp'] = time.time()

        # Debug: Print the values being set in session
        print(f"Shared data - className: {className}, date: {date}, code: {code}")

        if className and date and code:
            return render_template('Admin.html', date=date, code=code )
        else:
            return render_template('Admin.html', alertMsg="Missing data for fields. Please check your input.")
        
    return render_template('Admin.html', alertMsg="Can't share attendance")

@app.route('/add_order', methods=['POST'])
def add_order():
    collection.insert_one({
        'className': request.form.get('className'),
        'date': request.form.get('newDate'),
        'subject': request.form.get('subject'),
        'code': request.form.get('code')
    })
    return render_template('Admin.html')

@app.route('/delete_order', methods=['POST'])
def delete_order():
    className = request.form.get('className')
    date = request.form.get('date')
    subject = request.form.get('subject')

    if className and date and subject:
        collection.delete_one({'className': className, 'date': date, 'subject': subject})
    return redirect(request.referrer or url_for('index'))

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if not session.get('admin'):
        return redirect(url_for('adminlogin'))
    return render_template('Admin.html')

@app.route('/Aboute', methods=['GET'])
def Aboute():
    return render_template('Aboute.html')

@app.route('/co-3k', methods=['GET'])
def co3k():
    className = 'CO-3K'
    data = list(collection.find({"className": className}))
    return render_template('co-3k.html', data=data, className=className)

@app.route('/co-4k', methods=['GET'])
def co4k():
    className = 'CO-4K'
    data = list(collection.find({"className": className}))
    return render_template('co-4k.html', data=data, className=className)

@app.route('/co-5i', methods=['GET'])
def co5i():
    className = 'CO-5I'
    data = list(collection.find({"className": className}))
    return render_template('co-5i.html', data=data, className=className)

@app.route('/co-6i', methods=['GET'])
def co6i():
    className = 'CO-6I'
    data = list(collection.find({"className": className}))
    return render_template('co-6i.html', data=data, className=className)

@app.route('/student', methods=['GET', 'POST'])
def student_index():
    if request.method == 'POST':
        classn = request.form.get('className')
        data = {'className': classn}
        return render_template('index.html', data=data)
    return render_template('index.html', data={})

@app.route('/add_student_data', methods=['POST'])
def add_student_data():
    OTP = request.form.get('otp')

    if 'timestamp' in data:
        elapsed_time = time.time() - data['timestamp']

        if elapsed_time < 60:  # Data is valid within 1 minute
            code = data['code']
            
            if OTP == code :
                return render_template('addtosheet.html')
            else:
                data.clear()
                return render_template('index.html', alertMsg="The given Code is incorrect")
                
        return render_template('index.html', alertMsg="Shared data has expired. Please share again.")

    return render_template('index.html', alertMsg="No shared data available. Please share first.")


@app.route('/download_file', methods=['POST'])
def download_file():
    className = request.form.get('className')
    date = request.form.get('date')

    query = {}
    if className:
        query['className'] = className
    if date:
        query['date'] = date

    data = list(attend_collection.find(query))
    df = pd.DataFrame(data)

    if '_id' in df.columns:
        df = df.drop(columns=['_id'])

    excel_path = f"{className}_{date}.xlsx"
    df.to_excel(excel_path, index=False)

    response = send_file(excel_path, as_attachment=True)
    return response
