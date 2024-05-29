import psycopg2
from apscheduler.schedulers.blocking import BlockingScheduler
import bcrypt
from passlib.hash import sha256_crypt  # For password hashing
import random
import string
from datetime import date,datetime,timedelta


def generate_random_id():
   return ''.join(random.choices(string.digits, k=9))


def connect_to_db():
    return psycopg2.connect(
        database="trial433",
        user='postgres',
        password='zaynab742004',
        host='127.0.0.1',
        port=5432
    )

def is_student(connection, ssn):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM STUDENTS WHERE SID = %s", (ssn,))
    if cursor.fetchall():
        return True
    return False

def is_librarian(connection,ssn):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Librarian  WHERE LID = %s", (ssn,))
    if cursor.fetchall():
        return True
    return False


def is_professor(connection,ssn):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM STAFF_AND_PROF WHERE PID = %s", (ssn,))
    if cursor.fetchall():
        return True
    return False


def get_books_by_title(connection, title):
    cursor = connection.cursor()
    message = []
    books = []
    try:
        # ILIKE for case-insensitive, if entered in lower case same as upper case
        cursor.execute("SELECT ISBN, TITLE, FNAME, LNAME FROM BOOK JOIN AUTHOR ON AID = BID WHERE TITLE ILIKE %s", ('%' + title + '%',))
        books = cursor.fetchall()

        if not books:
            message.append(f"Book with title '{title}' not found.")
        
    except Exception as e:
        print("Error:", e)
    cursor.close()
    
    return books

# def get_books_by_genre(connection, genre_list):
#     cursor = connection.cursor()
#     message = []
#     books = []
#     print(genre_list)
#     try:
#         cursor.execute("SELECT B.ISBN, B.TITLE, A.FNAME, A.LNAME FROM BOOK B JOIN AUTHOR A ON B.BID = A.AID JOIN BOOK_GENRE BG ON B.ISBN = BG.IISBN WHERE BG.GENRE IN %s", (tuple(genre_list),))
#         books = cursor.fetchall()
#         if not books:
#             message.append( f"no_booksgen")
#     except Exception as e:
#         print("Error:", e)
#         books = []
#     cursor.close()
#     return books

def get_books_by_genre(connection, genre_list):
    cursor = connection.cursor()
    message = []
    books = []
    try:
        if not genre_list:
            message.append("No genres provided")
            return books 
        placeholders = ', '.join(['%s'] * len(genre_list))
        query = f"SELECT B.ISBN, B.TITLE, A.FNAME, A.LNAME FROM BOOK B JOIN AUTHOR A ON B.BID = A.AID JOIN BOOK_GENRE BG ON B.ISBN = BG.IISBN WHERE BG.GENRE IN ({placeholders})"
        
        cursor.execute(query, tuple(genre_list))
        books = cursor.fetchall()
        if not books:
            message.append("No books found for the provided genres")
    except Exception as e:
        print("Error:", e)
        books = []
    cursor.close()
    return books



def get_books_by_author(connection, fname, lname):
    cursor = connection.cursor()
    message = []
    books = []
    try:
        cursor.execute("SELECT ISBN, TITLE, FNAME, LNAME FROM BOOK JOIN AUTHOR ON AID = BID WHERE FNAME ILIKE %s AND LNAME ILIKE %s ", ('%' + fname + '%', '%' + lname + '%')) 
        books = cursor.fetchall()
        if not books:
            message.append( f"no_books")
        
    except Exception as e:
        print("Error:", e)
        books = []
    cursor.close()
    return books


def get_history(connection, ssn):
    cursor = connection.cursor()
    
    data = []
    try: 
        if(is_student(connection, ssn)):
            cursor.execute("SELECT isbn,deadline_date,lid FROM BORROW_STUDENTS WHERE SID = %s ORDER BY DEADLINE_DATE", (ssn,))
            data = cursor.fetchall()
        else:
            cursor.execute("SELECT isbn,deadline_date,lid FROM Borrow_Staff  WHERE PID = %s ORDER BY DEADLINE_DATE", (ssn,))
            data = cursor.fetchall()
        
    except Exception as e:
        print("Error:", e)
        data = None
        
    finally:
        cursor.close()
    
    return data


def get_holds(connection, ssn):
    cursor = connection.cursor()
    holds = []
   
    try:
        cursor.execute("SELECT B.TITLE, H.ISBN, H.Deadline_Date FROM Holds H JOIN BOOK B ON H.ISBN = B.ISBN WHERE H.SID = %s", (ssn,))
        holds = cursor.fetchall()
              
    except Exception as e:
        print("Error executing query:", e)
        
    finally:
        cursor.close()
          
    return holds
    
def update_hold(connection):
    cursor = connection.cursor()
    try:
        current_date = datetime.now().date()
        cursor.execute("SELECT sid, isbn, deadline_date FROM borrow_students WHERE deadline_date < %s ", (current_date,))
        overdue_borrowings = cursor.fetchall()
        
        for borrowing in overdue_borrowings:
            sid = borrowing['sid']
            isbn = borrowing['isbn']
            deadline = borrowing['deadline_date']
            cursor.execute("INSERT INTO hold (sid, isbn, deadline_date) VALUES (%s, %s, %s)", (sid, isbn, deadline))
        
        connection.commit()
    except Exception as e:
        print("Error:", e)
        connection.rollback()
    finally:
        cursor.close()
        
def extend_deadline_professors(conn):
    cursor = conn.cursor()
    try:
        current_date = datetime.now().date()
        new_deadline = current_date + timedelta(days=7)
        cursor.execute("UPDATE Borrow_Staff SET Deadline_Date = %s WHERE Deadline_Date <= %s",
                       (new_deadline, current_date))
        conn.commit()
        print("Deadline extended successfully.")

    except Exception as e:
        print("Error:", e)
        conn.rollback()

    finally:
        cursor.close()
        


def fill_student_data(connection,lid,ssn,deadline,isbn):
    try:
        
        cur = connection.cursor()

        # Check if the book exists and is available
        cur.execute("SELECT Quantity FROM Book WHERE ISBN = %s", (isbn,))
        quantity = cur.fetchone()

        if quantity and quantity[0] > 0:
            # Convert deadline date string to a date object
            deadline_date = date.fromisoformat(deadline)

            # Insert data into Borrow_Students table
            cur.execute("INSERT INTO Borrow_Students (SID, ISBN, Deadline_Date, LID) VALUES (%s, %s, %s, %s)",
                        (ssn, isbn, deadline_date, lid))

            # Decrement quantity in Book table by 1
            cur.execute("UPDATE Book SET Quantity = Quantity - 1 WHERE ISBN = %s", (isbn,))
            connection.commit()
            message = "Done :)"
            
        elif not quantity:
            message = "This book doesn't exist"
        else:
            message = "Quantity for the book is currently out of stock."
    except Exception as e:
        print("Error:", e)
        
    return message


def fill_staff_data(connection,lid,ssn,deadline,isbn):
    try:
        message = None
        cur = connection.cursor()

        # Check if the book exists and is available
        cur.execute("SELECT Quantity FROM Book WHERE ISBN = %s", (isbn,))
        quantity = cur.fetchone()

        if quantity and quantity[0] > 0:
            # Convert deadline date string to a date object
            deadline_date = date.fromisoformat(deadline)

            # Insert data into Borrow_Students table
            cur.execute("INSERT INTO Borrow_Staff (PID, ISBN, Deadline_Date, LID) VALUES (%s, %s, %s, %s)",
                        (ssn, isbn, deadline_date, lid))

            # Decrement quantity in Book table by 1
            cur.execute("UPDATE Book SET Quantity = Quantity - 1 WHERE ISBN = %s", (isbn,))
            connection.commit()
            message = "Done :)"
            
        elif not quantity:
            message = "This book doesn't exist"
        else:
            message = "Quantity for the book is currently out of stock."
    except Exception as e:
        print("Error:", e)
        
    return message

def request_book_library(conn,isbn,title,bid):
    cur = conn.cursor()
    message = None
    try:
        request_id = generate_random_id()
        # Generate a random request status (accepted or rejected)
        request_status = random.choice(["accepted", "rejected"])
    
        # Insert data into External_library_source table
        cur.execute("INSERT INTO External_library_source (ID, Requested_ISBN, Request_status) VALUES (%s, %s, %s)",
                    (request_id, isbn, request_status))
    
        if request_status == "accepted":
            # Insert data into Book table if request is accepted
            cur.execute("INSERT INTO BOOK (ISBN, TITLE, QUANTITY, BID) VALUES (%s, %s, %s, %s)",
                        (isbn, title, 1, bid))
            print("OK")
            message = "The request for the book is accepted."
        else:
            message = "The request for the book is rejected."
            print(message)
            
        conn.commit()
    except Exception as e:
        print("Error:", e)
    return message


def searching_student_by_librarian(conn,sid):
    try:
        message = ""
        cur = conn.cursor()
        # Retrieve student information
        cur.execute("SELECT Fname, Lname FROM Students WHERE SID = %s", (sid,))
        student_info = cur.fetchone()

        if student_info:
            student_name = " ".join(student_info)

            # Retrieve borrowed books information for the student
            cur.execute("SELECT b.TITLE, bs.Deadline_Date FROM Borrow_Students bs JOIN BOOK b ON bs.ISBN = b.ISBN WHERE SID = %s ORDER BY bs.Deadline_Date ASC", (sid,))
            books_info = cur.fetchall()

        else:
            message = "Student not found"

    except Exception as e:
        print("Error:", e)
        
    return student_name,books_info