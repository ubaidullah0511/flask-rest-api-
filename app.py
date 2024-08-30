from flask import Flask, render_template, request, redirect, session , jsonify
from flask_mysqldb import MySQL
from config import Config  

app = Flask(__name__)

app.config.from_object(Config)

mysql = MySQL(app)

def get_valid_string(str):
    while True:
        if any(char.isdigit() for char in str):
            return False
        elif not all(char.isalpha() or char.isspace() for char in str):
            return False
        else:
            return str.lstrip(" ").rstrip(" ")

userid = 0
bookid = 0

def generate_userid():
    global userid  
    userid += 1
    return userid

def generate_bookid():
    global bookid
    bookid += 1
    return bookid

@app.route('/')
def hello():
    return 'Welcome to Library Management System'

@app.route('/showusersform')
def showusersform():
    return render_template("viewusers.html")

@app.route('/showusers')
def showusers():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()

    userlist = []
    for user in users:
        user_dict = {
            "id": user[0],
            "name": user[1]
        }
        userlist.append(user_dict)

    cursor.close()
    return jsonify(userlist)

@app.route("/showbooks")
def showbooks():
    return render_template("viewbooks.html")

@app.route('/showbooksincatalogue', methods=["GET"])
def showbooksincatalogue():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM books')
    books = cursor.fetchall()

    booklist = []
    for book in books:
        book_id = book[0]  
        book_name = book[1]
        author_name = book[2]
        user_id = book[3]

        user = None
        if user_id is not None:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()

        book_dict = {
            "id": book_id,
            "bookname": book_name,
            "authorname": author_name,
            "user": user[1] if user else None
        }
        booklist.append(book_dict)

    cursor.close()
    return jsonify(booklist)

@app.route('/deletebook/<int:book_id>', methods=['DELETE'])
def delbook(book_id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
    
    if cursor.rowcount == 0:
        return jsonify({"message": "book not found"}), 404
    
    mysql.connection.commit()
    cursor.close()
    return jsonify({"message": "book deleted successfully"})

@app.route('/addusers', methods=['POST', 'GET'])
def addusers():
    if request.method == 'POST':
        username = get_valid_string(request.form["name"])
        if not username:
            return jsonify({"message": "Invalid Username"})
        
        cursor = mysql.connection.cursor()
        cursor.execute(f"INSERT INTO users (id, name) VALUES (%s,%s)", (generate_userid(), username))
        mysql.connection.commit()
        cursor.close()
        return jsonify({"message": "Users added successfully!", "users": username}), 201
    return render_template('adduser.html')

@app.route("/deleteall", methods=["DELETE"])
def delall():
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM users")
    if cursor.rowcount == 0:
        return jsonify({"message": "nothing to Delete"}), 404
    
    mysql.connection.commit()
    cursor.close()
    return jsonify({"message": "deleted successfully"})

@app.route('/deleteuser/<int:user_id>', methods=['DELETE'])
def deluser(user_id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    
    if cursor.rowcount == 0:
        return jsonify({"message": "User not found"}), 404
    
    mysql.connection.commit()
    cursor.close()
    return jsonify({"message": "user deleted successfully"})

@app.route('/user/<int:user_id>', methods=['GET'])
def getoneuser(user_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    return jsonify(user)

@app.route('/edituser/<int:user_id>', methods=['PUT', 'GET'])
def edituser(user_id):
    if request.method == 'GET':
        return render_template("edituser.html")
    else:
        cursor = mysql.connection.cursor()
        user = request.get_json()
        user_data = get_valid_string(user.get('name'))
        if not user_data:
            return jsonify({"message": "Invalid Input"})
        cursor.execute("UPDATE users SET name = %s WHERE id = %s", (user_data, user_id))
        if cursor.rowcount == 0:
            return jsonify({"message": "User not found"}), 404
        mysql.connection.commit()
        cursor.close()
        return jsonify({"message": user_data})

@app.route('/addbookincatalogue', methods=['POST', 'GET'])
def addbookincatalogue():
    if request.method == 'POST':
        bookname = request.form["name"]
        authorname = get_valid_string(request.form["author"])
        if not authorname:
            return jsonify({"message": "Invalid authorname"})

        cursor = mysql.connection.cursor()
        cursor.execute(f"INSERT INTO books (id, name, author) VALUES (%s,%s,%s)", (generate_bookid(), bookname, authorname))
        mysql.connection.commit()
        cursor.close()
        return jsonify({"message": "books added successfully!", "users": bookname}), 201
    
    return render_template("addbook.html")

@app.route('/showbooksfromusers/<int:user_id>')
def showbooksfromusers(user_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = %s", user_id)
    users = cursor.fetchall()

    cursor.execute("SELECT * FROM books WHERE user_id = %s", (user_id))
    books = cursor.fetchall()
    booklist = []
    for book in books:
        book_dict = {
            "id": book[0],
            "name": book[1],
            "author": book[2],
        }
        booklist.append(book_dict)

    user_dictionary = {
        "id": user_id,
        "name": users[1],
        "books": booklist
    }
    return jsonify(user_dictionary)

@app.route('/issuebooktouser/<int:user_id>/<int:book_id>', methods=['PUT'])
def addbook(user_id, book_id):
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE books SET user_id = %s WHERE id = %s", (user_id, book_id))
    
    if cursor.rowcount == 0:
        cursor.close()
        return jsonify({"message": "Book not found or already issued to a user"}), 404

    mysql.connection.commit()
    cursor.close()
    return jsonify({"message": f"Book successfully issued to user id: {user_id}"}), 200

@app.route('/returnbookfromuser/<int:book_id>', methods=['PUT'])
def removebook(book_id):
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE books SET user_id = %s WHERE id = %s", (0, book_id))
    if cursor.rowcount == 0:
        cursor.close()
        return jsonify({"message": "Book not found or already issued to a user"}), 404
    
    mysql.connection.commit()
    cursor.close()
    return jsonify({"message": f"Book deleted successfully"})

@app.route('/handle_post', methods=['POST'])
def handle_post():
    if request.method == 'POST':
        a = request.get_json()
        return a

if __name__ == "__main__":
    app.run(debug=True)
