import json, sqlite3, click, functools, os, hashlib,time, random, sys, hashlib
from flask import Flask, current_app, g, session, redirect, render_template, url_for, request




### DATABASE FUNCTIONS ###

def connect_db():
    return sqlite3.connect(app.database)

def init_db():
    """Initializes the database with our great SQL schema"""
    conn = connect_db()
    db = conn.cursor()
    db.executescript("""

DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS notes;

CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assocUser INTEGER NOT NULL,
    dateWritten DATETIME NOT NULL,
    note TEXT NOT NULL,
    publicID INTEGER NOT NULL
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL
);

INSERT INTO users VALUES(null,"viggo", "1931701645");
INSERT INTO notes VALUES(null,2,"2022-11-09 13:40:00","ssh stud@secu14.itu.dk",1234567890);

""")



### APPLICATION SETUP ###
app = Flask(__name__)
app.database = "db.sqlite3"
app.secret_key = os.urandom(32)

### ADMINISTRATOR'S PANEL ###
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

@app.route("/")
def index():
    if not session.get('logged_in'):
        return render_template('index.html')
    else:
        return redirect(url_for('notes'))


@app.route("/notes/", methods=('GET', 'POST'))
def notes():
    importerror=""
    #Posting a new note:
    if request.method == 'POST':
        if request.form['submit_button'] == 'add note':
            note = request.form['noteinput']
            db = connect_db()
            c = db.cursor()
            statement = """INSERT INTO notes(id,assocUser,dateWritten,note,publicID) VALUES(null,%s,'%s','%s',%s);""" %(session['userid'],time.strftime('%Y-%m-%d %H:%M:%S'),note,random.randrange(1000000000, 9999999999))
            print(statement)
            c.execute(statement)
            db.commit()
            db.close()
        elif request.form['submit_button'] == 'import note':
            noteid = request.form['noteid']
            db = connect_db()
            c = db.cursor()
            statement = """SELECT * from NOTES where publicID = %s""" %noteid
            c.execute(statement)
            result = c.fetchall()
            if(len(result)>0):
                row = result[0]
                statement = """INSERT INTO notes(id,assocUser,dateWritten,note,publicID) VALUES(null,%s,'%s','%s',%s);""" %(session['userid'],row[2],row[3],row[4])
                c.execute(statement)
            else:
                importerror="No such note with that ID!"
            db.commit()
            db.close()
    
    db = connect_db()
    c = db.cursor()
    statement = "SELECT * FROM notes WHERE assocUser = %s;" %session['userid']
    print(statement)
    c.execute(statement)
    notes = c.fetchall()
    print(notes)
    
    return render_template('notes.html',notes=notes,importerror=importerror)

def myHash(text:str):
  hash=0
  for ch in text:
    hash = ( hash*281  ^ ord(ch)*997) & 0xFFFFFFFF
  return hash

def sanitize(text:str):
    sanitary = False
    sanitary = not text.__contains__("'")
    sanitary = not text.__contains__(" ")
    sanitary = not text.__contains__("-")
    return sanitary


@app.route("/login/", methods=('GET', 'POST'))
def login():
    error = ""
    if request.method == 'POST':
        username = request.form['username']
        password = str(myHash(request.form['password']))
        db = connect_db()
        c = db.cursor()
        statement = "SELECT * FROM users WHERE username = '%s' AND password = '%s';" %(username, password)
        c.execute(statement)
        result = c.fetchall()

        if len(result) > 0 and sanitize(username) and sanitize(password):            
            session.clear()
            session['logged_in'] = True
            session['userid'] = result[0][0]
            session['username']=result[0][1]
            return redirect(url_for('index'))
        else:
            error = "Wrong username or password, or invalid input!"
    return render_template('login.html',error=error)


@app.route("/register/", methods=('GET', 'POST'))
def register():
    errored = False
    usererror = ""
    passworderror = ""
    if request.method == 'POST':
        username = request.form['username']
        password = str(myHash(request.form['password']))
        db = connect_db()
        c = db.cursor()
        pass_statement = """SELECT * FROM users WHERE password = '%s';""" %password
        user_statement = """SELECT * FROM users WHERE username = '%s';""" %username
        c.execute(pass_statement)
        if(len(c.fetchall())>0):
            errored = True
            passworderror = "That password is already in use by someone else!"

        c.execute(user_statement)
        if(len(c.fetchall())>0):
            errored = True
            usererror = "That username is already in use by someone else!"
        
        errored = not sanitize(username)
        errored = not sanitize(password)

        if errored:
            usererror = "Invalid username or password! Please only use letters or numbers."

        if(not errored):
            statement = """INSERT INTO users(id,username,password) VALUES(null,'%s','%s');""" %(username,password)
            print(statement)
            c.execute(statement)
            db.commit()
            db.close()
            return f"""<html>
                        <head>
                            <meta http-equiv="refresh" content="2;url=/" />
                        </head>
                        <body>
                            <h1>SUCCESS!!! Redirecting in 2 seconds...</h1>
                        </body>
                        </html>
                        """
        
        db.commit()
        db.close()
    return render_template('register.html',usererror=usererror,passworderror=passworderror)


@app.route("/logout/")
@login_required
def logout():
    """Logout: clears the session"""
    session.clear()
    return redirect(url_for('index'))

if __name__ == "__main__":
    #create database if it doesn't exist yet
    if not os.path.exists(app.database):
        init_db()
    runport = 5000
    if(len(sys.argv)==2):
        runport = sys.argv[1]
    try:
        app.run(host='0.0.0.0', port=runport) # runs on machine ip address to make it visible on netowrk
    except:
        print("Something went wrong. the usage of the server is either")
        print("'python3 app.py' (to start on port 5000)")
        print("or")
        print("'sudo python3 app.py 80' (to run on any other port)")