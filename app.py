from flask import Flask, render_template, request, redirect,session
from passlib.hash import sha256_crypt  # For password hashing
import functions

app = Flask(__name__)
app.config['SECRET_KEY'] = 'zaynabalhaj2004'

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        ssn = request.form['ssn']
        password = request.form['password']

        conn = functions.connect_to_db()

        if not functions.is_student(conn,ssn) and not functions.is_professor(conn,ssn) and not functions.is_librarian(conn,ssn):
            message = "You are not authorized to access the system."
            return render_template('signup.html', message=message)
        
        
        # Hash the password before storing it in the database
        hashed_password = sha256_crypt.hash(password)
        
        # Insert user information into the database
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (ssn, hashed_password))
            conn.commit()
            message = "Signup successful. Please login."
            return render_template('login.html', message=message)
        except Exception as e:
            conn.rollback()
            message = "Error occurred during signup."
            print("Error:", e)
            return render_template('signup.html', message=message)
        finally:
            cursor.close()
            conn.close()
    
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        ssn = request.form['ssn']
        password = request.form['password']
        
        # Check if user exists and password is correct
        conn = functions.connect_to_db()
        cursor = conn.cursor()
        cursor.execute("SELECT username, password FROM users WHERE username = %s", (ssn,))
        user = cursor.fetchone()
        if user and sha256_crypt.verify(password, user[1]):  
            # Store the username (SSN) in session
            session['ssn'] = ssn
            if(functions.is_student(conn, ssn)):
                cursor.execute("SELECT fname, lname FROM students WHERE sid = %s", (ssn,))
                student_data = cursor.fetchone()
                if student_data:
                    fname, lname = student_data
                    name = f"{fname} {lname}"
                return render_template('student.html', name=name)
            elif(functions.is_professor(conn, ssn)):
                cursor.execute("SELECT fname, lname FROM staff_and_prof WHERE pid = %s", (ssn,))
                prof_data = cursor.fetchone()
                if prof_data:
                    fname, lname = prof_data
                    name = f"{fname} {lname}"
                return render_template('professor.html', name=name)
            elif(functions.is_librarian(conn,ssn)):
                session['lid'] = ssn
                return redirect('/librarian')
            else:
                message = "this ssn is not elligible to access."
                return render_template('login.html', message=message)
        else:
            message = "Invalid username or password."
            return render_template('login.html', message=message)
    
    return render_template('login.html')

@app.route('/',methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/logout')
def logout():
    session.pop('ssn', None)
    return redirect('/login')  

#this route as if it is student route bs t8yro btshelo
@app.route('/dashboard')
def homepage():
    return render_template('dashboard.html') 

#the following two routes are still not used
# i added them in the login fxn when the user is student he will be directed to this route
# the html files still doesnt exist akid asln bs tsht8lo 3lyhun ha t8yro ktir n hal eshya

@app.route('/student',methods=['GET', 'POST'])
def student():
    conn = functions.connect_to_db()
    functions.update_hold(conn)
    return render_template("student.html")


@app.route('/professor',methods=['GET', 'POST'])
def professor():
    conn = functions.connect_to_db()
    functions.extend_deadline_professors(conn)
    return render_template("professor_homepage.html")

@app.route('/librarian',methods=['GET', 'POST'])
def librarian():
    return render_template("librarian.html")

@app.route('/history')
def history():
    conn = functions.connect_to_db()
    ssn = session['ssn'] 
    history = functions.get_history(conn, ssn)
    #NOTE: when u add l html files lal students wel proff , uncomment w add l html files l bdkn hene
    
    #if (functions.is_student(conn, ssn)):
    #    return render_template("student.html", history = history)
    #else:
    #    return render_template("professor.html", history = history)
    return render_template("search_results.html", history=history)

@app.route('/search_by_title',methods = ['POST'])
def search_by_title():
    conn = functions.connect_to_db()
    title = request.form['title']
    books = functions.get_books_by_title(conn,title)
    return render_template("search_results.html", books = books) 
    
@app.route('/search_by_genre',methods = ['POST'])   
def search_by_genre(): 
    conn = functions.connect_to_db()
    genre_list = request.form.getlist('genre') 
    books = functions.get_books_by_genre(conn, genre_list)
    if not books:
        books = 'no_booksgen'
    return render_template("search_results.html", books = books) 
    
@app.route('/search_by_author',methods = ['POST'])
def search_by_author():
    conn = functions.connect_to_db()
    fname = request.form['fname']
    lname = request.form['lname']
    books = functions.get_books_by_author(conn,fname,lname)
    if not books:
        books = 'no_books'
    return render_template("search_results.html", books = books)
    
@app.route('/display_holds')
def display_holds():
    conn = functions.connect_to_db()
    ssn = session['ssn']
    holds = functions.get_holds(conn,ssn)
    return render_template("search_results.html", holds = holds) 

@app.route('/display_holds_librarian',methods=['GET','POST'])
def display_holds_librarian():
    conn = functions.connect_to_db()
    ssn = request.form.get('sid')  # Safely get 'sid'
    
    holds = functions.get_holds(conn,ssn)
    
    if not holds:
        holds = 'No holds'
    return render_template("search_st_results.html", holds = holds)


@app.route('/history_librarian',methods=['GET','POST'])
def history_librarian():
    conn = functions.connect_to_db()
    ssn =  request.form.get('sid')
    print(ssn)
    history = functions.get_history(conn, ssn)

    if not history:
        history == 'No history log for this student'
    return render_template("search_st_results.html", history=history)


@app.route('/borrow_student', methods=['POST'])
def borrow_student():
    if 'lid' in session:
        lid = session['lid']  
    else:
        return 'You are not logged in', 403

    conn = functions.connect_to_db()
    try:
        sid = request.form['student_id']
        isbn = request.form['isbn']
        deadline = request.form['deadline']

        cursor = conn.cursor()
        if(functions.is_student(conn, sid)):
            sql = "INSERT INTO borrow_students (sid, isbn, deadline_date, lid) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (sid, isbn, deadline, lid))
            conn.commit()
        else:
            return 'Student Id not found. Please try again.'
        return 'Book borrowed successfully'
    except Exception as e:
        conn.rollback()
        return f'Error borrowing book: {str(e)}'
    finally:
        conn.close()

@app.route('/borrow_staff',methods = ['POST'])
def borrow_staff():
    if 'lid' in session:
        lid = session['lid'].strip()  
    else:
        return 'You are not logged in', 403

    conn = functions.connect_to_db()
    try:
        pid = request.form['staff_id'].strip()
        isbn = request.form['isbn'].strip()
        deadline = request.form['deadline']

        if(functions.is_professor(conn, pid)):
            cursor = conn.cursor()
            sql = "INSERT INTO borrow_staff (pid, isbn, deadline_date, lid) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (pid, isbn, deadline, lid))
            conn.commit()
        return 'Book borrowed successfully'
    except Exception as e:
        conn.rollback()
        return f'Error borrowing book: {str(e)}'
    finally:
        conn.close()


@app.route('/request_book',methods = ['GET','POST'])
def request_book():
    if request.method  == 'POST':
        conn = functions.connect_to_db()
        isbn =  request.form.get('isbn')
        print(isbn)
        title = request.form['title']
        print(title)
        bid = request.form['bid']
        print(bid)
        message = functions.request_book_library(conn,isbn,title,bid)
        
        return render_template("search_st_results.html", message_1 = message)
    
'''
@app.route('/search_student',methods=['GET', 'POST'])
def search_student():
    conn = functions.connect_to_db()
    sid = request.form['sid']
    print(request.form)

    name,info,message = functions.searching_student_by_librarian(conn,sid)
    return render_template("search_student.html", name=name ,info=info ,message4 = message)
'''

@app.route('/search_student', methods=['GET', 'POST'])
def search_student():
    if request.method == 'POST':
        conn = functions.connect_to_db()
        sid = request.form.get('sid')  # Safely get 'sid'
        
        if sid:  # Check if 'sid' is not None
            name, info = functions.searching_student_by_librarian(conn, sid)
            return render_template("search_st_results.html", name=name, info=info)
        else:
            message = "No Student ID provided"
            return render_template("search_st_results.html", message=message)
    else:
        # If it's a GET request, just render the form without data
        return render_template("search_st_results.html")



if __name__ == '__main__':
    app.run(debug=True)
 
     