from flask import Flask, request, jsonify, abort , send_from_directory , session
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity , decode_token , get_jwt
import sqlite3
from flask_cors import CORS ,cross_origin
from datetime import date  , timedelta
from sqlalchemy import Enum
from sqlalchemy.orm import class_mapper , joinedload
from werkzeug.utils import secure_filename
import jwt
from flask_bcrypt import Bcrypt
import datetime
import json
import random
import re


app = Flask(__name__)
api = Api(app)
CORS(app)
app.secret_key = 'secret_secret_key'
# app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///library.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:1234@localhost/library' # change this to your own mysql database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your_secret_key_here'
db = SQLAlchemy(app)
jwt = JWTManager(app)
bcrypt = Bcrypt(app)
invalidated_tokens = set()  # Initialize as a set



def check_if_token_in_blocklist(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return jti in invalidated_tokens

# Define the authentication_successful function here
def authentication_successful(name, password):
    global customer
    customer = Customers.query.filter_by(name=name).first()
    if customer and bcrypt.check_password_hash(customer.password, password):
        return True
    return False


# @app.route('/protected', methods=['GET'])
# def protected_route():
#     # Extract the token
#     token = get_jwt_token()
#     # Check if the token is valid
#     if not is_token_valid(token):
#         return jsonify({'message': 'Token is invalidated'}), 401

# set models 
class Books(db.Model):
    bookID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    author = db.Column(db.Text)
    year_published = db.Column(db.Integer, nullable=False)
    book_type = db.Column(db.Enum('Up to 10 days' , 'Up to 5 days', 'Up to 2 days') )
    PIC_link = db.Column(db.String(500))
    def __init__(self, name, author, year_published, book_type, PIC_link):
        self.name = name
        self.author = author
        self.year_published = year_published
        self.book_type = book_type
        self.PIC_link = PIC_link if PIC_link else 'default.jpg'

    
class Customers(db.Model):
    custID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(255))
    age = db.Column(db.Integer)
    password = db.Column(db.String(500), nullable=False)
    def __init__ (self, name, city, age, password):
        self.name = name
        self.city = city
        self.age = age
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
    
class Loans(db.Model):
    loanID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    custID = db.Column(db.Integer, db.ForeignKey('customers.custID'),nullable=False)
    bookID = db.Column(db.Integer, db.ForeignKey('books.bookID'), nullable=False)
    LoanDate = db.Column(db.Date)
    ReturnDate = db.Column(db.Date)
    def __init__ (self, custID, bookID, LoanDate, ReturnDate):
        self.custID = custID
        self.bookID = bookID
        self.LoanDate = LoanDate
        self.ReturnDate = ReturnDate
        


# set routes
# test route

# @app.route("/")
# def test():
#     return "test is on"


@app.route("/", methods=["GET"])
def home():
    if request.method == "GET":
        path = session.get("http://127.0.0.1:5000/frontend/home.html")
    return send_from_directory(".", path)





# display all books
@app.route("/show_books", methods=['GET'])
@jwt_required()
def show_books():
    current_custID = get_jwt_identity()
    if request.method == 'GET':
        books = Books.query.all()
        book_list = []

        for book in books:
            book_data = {
                'bookID': book.bookID,
                'name': book.name,
                'author': book.author,
                'year_published': book.year_published,
                'book_type': book.book_type,
                'PIC_link': book.PIC_link
            }
            book_list.append(book_data)

        return jsonify({'books': book_list})

# add new book to table books
@app.route('/add_book', methods=['POST'])
@jwt_required()
def add_book():
    if request.method == 'POST':
        data = request.json
        name = data.get('name')
        author = data.get('author')
        year_published = data.get('year_published')
        book_type = data.get('book_type')
        PIC_link = data.get('PIC_link')

    # Validate book_type
        if book_type not in ['Up to 10 days', 'Up to 5 days', 'Up to 2 days']:
            return "Invalid book_type", 400

    # Create a new Books instance
        new_book = Books(name=name, author=author, year_published=int(year_published),book_type=book_type, PIC_link=PIC_link)


    # Add to the session and commit
        try:
            db.session.add(new_book)
            db.session.commit()
            return "Book added successfully", 201
        except Exception as e:
            db.session.rollback()
            return str(e), 500
    
    
    

# show all customers 
@app.route("/show_customers", methods=['GET'])
@jwt_required()
def show_customers():
    current_custID = get_jwt_identity()
    if request.method == 'GET':
        customers = Customers.query.all()
        customer_list = []
        for customer in customers:
            customer_data = {
                'name': customer.name,
                'city': customer.city,
                'age': customer.age
            }
            customer_list.append(customer_data)

        return jsonify({'customers': customer_list})

# add new customer to table customers
# @app.route("/add_customer", methods=['POST'])
# @jwt_required()
# def add_customer():
#     if request.method == 'POST':
#         data = request.get_json()
#         new_customer = Customers(
#             custID = data['custID'],
#             name=data['name'],
#             city=data['city'],
#             age=data['age'],
#             password=data['password']
#         )
#         db.session.add(new_customer)
#         db.session.commit()
#         return jsonify({'message': 'Customer added successfully'})
 
# show all loans
@app.route("/show_loans", methods=["GET"])
@jwt_required()
def show_loans():
    current_custID = get_jwt_identity()
    if request.method == "GET":
        loans = Loans.query.all()
        loan_list = []
        for loan in loans:
            customer = Customers.query.filter_by(custID=loan.custID).first()
            book = Books.query.filter_by(bookID=loan.bookID).first()

            loan_data = {
                "id": loan.loanID,
                "customer_name": customer.name,
                "book_name": book.name,
                "LoanDate": loan.LoanDate,
                "ReturnDate": loan.ReturnDate,
            }
            loan_list.append(loan_data)

        return jsonify({"loans": loan_list})



def fetch_customer_book_list():
    result = db.session.query(Customers.name, Books.name)\
                    .join(Loans, Customers.custID == Loans.custID)\
                    .join(Books, Loans.bookID == Books.bookID)\
                    .all()
    return result

# add new loan to table loans
@app.route("/loan_book", methods=["POST"])
@jwt_required()
def loan_book():
    current_custID = get_jwt_identity()
    if request.method == "POST":
        data = request.get_json()
        book_name = data.get("name")
        customer_name = data.get("customer_name")

        loanDate_str = data.get("LoanDate", str(date.today()))
        year, month, day = map(int, loanDate_str.split('-'))
        loanDate = date(year, month, day)

        if not book_name or not customer_name:
            return jsonify({"message": "Invalid request. Please provide required fields."}), 400

        book = Books.query.filter_by(name=book_name).first()
        customer = Customers.query.filter_by(name=customer_name).first()

        if not book or not customer:
            return jsonify({"message": "Book or customer not found."}), 404
        
        loan_duration = re.findall(r'\d+', book.book_type)
        if loan_duration:
            days_to_add = int(loan_duration[0])
        else:
            return jsonify({'message': 'Invalid book type.'}), 400


        
        return_date = loanDate + timedelta(days=days_to_add)
        
        new_loan = Loans(
            custID=customer.custID,
            bookID=book.bookID,
            LoanDate=loanDate,
            ReturnDate=return_date,
        )
        db.session.add(new_loan)
        db.session.commit()
        return jsonify({"message": "Book loaned successfully"})




# return book and delete loan from db 
@app.route("/return_book", methods=['POST'])
@jwt_required()
def return_book():
    current_custID = get_jwt_identity()
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name').join()
        customer_name = data.get('customer_name').join()
        
        if not book_name or not customer_name:
            return jsonify({'message': 'Invalid request. Please provide both name and customer_name in the request.'}), 400
        book = Books.query.filter_by(name=name).fetch_customer_book_list()
        customer = Customers.query.filter_by(name=customer_name).fetch_customer_book_list()

        if not book or not customer:
            return jsonify({'message': 'Book or customer not found.'}), 404

        loan = Loans.query.filter_by(bookID=book.bookID, custID=customer.custID).first()

        if not loan:
            return jsonify({'message': 'Loan not found.'}), 404

        return_date = data.get('ReturnDate')

        if return_date:
            loan.ReturnDate = return_date
            db.session.commit()
            
            db.session.delete(loan)
            db.session.commit()

            return jsonify({'message': 'Book returned successfully and loan deleted.'})
        else:
            return jsonify({'message': 'Invalid request. Please provide ReturnDate in the request.'}), 400

# search book by name
#error: NameError: name 'name' is not defined #
@app.route("/search_book/", methods=['POST'])
@jwt_required()
def search_book():
    current_custID = get_jwt_identity()
    if request.method == 'POST':
        data = request.get_json()
        book_name = data.get('name')
        if not book_name:
            return jsonify({'message': 'Book name is required'}), 400

        book = Books.query.filter_by(name=book_name).first()
        if book:
            book_data = {
                'bookID': book.bookID,
                'book_name': book.name,
                'author': book.author,
                'year_published': book.year_published,
                'PIC_link': book.PIC_link
            }
            return jsonify({'book': book_data})
        else:
            return jsonify({'message': 'Book not found'})

        


# search customer by name 
# make search user as a friend requests
@app.route("/search_customer/", methods=['POST'])
@jwt_required()
def search_customer():
    current_custID = get_jwt_identity()
    if request.method == 'POST':
        data = request.get_json()
        customer = Customers.query.filter_by(name=data['name']).first()
        if customer:
            customer_data = {
                'id': customer.custID,
                'name': customer.name,
                'city': customer.city,
                'age': customer.age,
                # 'password': <PASSWORD>
            }
            return jsonify({'customer': customer_data})
        else:
            return jsonify({'message': 'Customer not found'})

    
# display late loans
@app.route("/display_late_loans", methods=['GET'])
@jwt_required()
def display_late_loans():
    current_custID = get_jwt_identity()
    today = date.today()
    late_loans = Loans.query.filter(Loans.ReturnDate < today).all()
    late_loan_list = []

    for loan in late_loans:
        late_loan_data = {
            'id': loan.loanID,
            'custID': loan.custID,
            'bookID': loan.bookID,
            'LoanDate': loan.LoanDate,
            'ReturnDate': loan.ReturnDate
        }
        late_loan_list.append(late_loan_data)

    return jsonify({'late_loans': late_loan_list})

# unit test - create a test books - make 3 random books and add them to the db 1st

@app.route("/book_test", methods=["POST"])
@jwt_required()
def book_test():
    current_custID = get_jwt_identity()  
    if request.method == "POST":
        books_to_add = [
            {
                "name": "Don Quixote",
                "author": "Miguel de Cervantes",
                "year_published": 1605, 
                "book_type": "Up to 10 days",
                "PIC_link": "https://example.com/donquixote.jpg",
            },
            {
                "name": "One Hundred Years of Solitude",
                "author": "Gabriel García Márquez",
                "year_published": 1967,
                "book_type": "Up to 5 days",
                "PIC_link": "https://example.com/solitude.jpg",
            },
            {
                "name": "The Little Prince",
                "author": "Antoine de Saint-Exupéry",
                "year_published": 1943,
                "book_type": "Up to 10 days",
                "PIC_link": "https://example.com/thelittleprince.jpg",
            },
            {
                "name": "The Diary of Anne Frank",
                "author": "Anne Frank",
                "year_published": 1947,
                "book_type": "Up to 10 days",
                "PIC_link": "https://example.com/annefrank.jpg",
            },
            {
                "name": "The Adventures of Huckleberry Finn",
                "author": "Mark Twain",
                "year_published": 1884,
                "book_type": "Up to 5 days",
                "PIC_link": "https://example.com/huckleberryfinn.jpg",
            },
        ]

        for book_data in books_to_add:
            book = Books(
                name=book_data["name"],
                author=book_data["author"],
                year_published=book_data["year_published"],
                book_type=book_data["book_type"],
                PIC_link=book_data["PIC_link"],
            )
            db.session.add(book)

        db.session.commit()
        return jsonify({"message": "Books added successfully"})

    return jsonify({"msg": "Invalid request method"}), 405

# unit test - create a test books - make 3 random books and add them to the db 2nd

# fake = Faker()

# @app.route("/book_test", methods=["POST"])
# @jwt_required()
# def book_test():
#     current_custID = get_jwt_identity()

#     if request.method == "POST":
#         books_to_add = []
        
#         for _ in range(3):  # Generate 3 random books
#             book_data = {
#                 "name": fake.catch_phrase(),  # Random book name
#                 "author": fake.name(),  # Random author name
#                 "year_published": random.randint(1800, 2021),  # Random publication year
#                 "book_type": random.choice(["Up to 10 days", "Up to 5 days", "Up to 2 days"]),  # Random book type
#                 "PIC_link": fake.image_url()  # Random image URL
#             }
#             books_to_add.append(book_data)

#         for book_data in books_to_add:
#             book = Books(
#                 name=book_data["name"],
#                 author=book_data["author"],
#                 year_published=book_data["year_published"],
#                 book_type=book_data["book_type"],
#                 PIC_link=book_data["PIC_link"],
#             )
#             db.session.add(book)

#         db.session.commit()
#         return jsonify({"message": "Books added successfully"})

#     return jsonify({"msg": "Invalid request method"}), 405


# unit test - create a test customer
@app.route("/customer_test", methods=['POST'])
@jwt_required()
def customer_test():
    current_custID = get_jwt_identity()
    if request.method == 'POST':
        test_customer_data = {"name": "roei","city": "Tel Aviv","age": 20, "password": "111111111"}
        test_customer = Customers(
            name=test_customer_data['name'],
            city=test_customer_data['city'],
            age=test_customer_data['age'],
            password=test_customer_data['password']
        )   
        db.session.add(test_customer)
        db.session.commit()
        return jsonify({'message': 'Test customer added successfully'})


# unit test - create a test loan 
@app.route("/loan_test", methods=['POST'])
@jwt_required()
def loan_test():
    current_custID = get_jwt_identity()
    if request.method == 'POST':
        test_loan_data = {"name": "The First Book", "custID": 1, "LoanDate": date.today()} 
        book = Books.query.filter_by(name=test_loan_data['name']).first()

        if not book:
            return jsonify({'message': 'Book not found.'}), 404

        loan_duration = re.findall(r'\d+', book.book_type)
        if loan_duration:
            days_to_add = int(loan_duration[0])
        else:
            return jsonify({'message': 'Invalid book type.'}), 400

        return_date = test_loan_data['LoanDate'] + timedelta(days=days_to_add)

        test_loan = Loans(
            custID=test_loan_data['custID'],
            bookID=book.bookID,
            LoanDate=test_loan_data['LoanDate'],
            ReturnDate=return_date
        )
        db.session.add(test_loan)
        db.session.commit()
        return jsonify({'message': 'Test loan added successfully'})
    


# create a costumer a user     
@app.route("/register", methods=['POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name')
        city = data.get('city')
        age = data.get('age')
        password = data.get('password')

        if not name or not city or not age or not password:
            return jsonify({'message': 'Invalid request. Please provide name, city, age, and password in the request.'}), 400

        existing_user = Customers.query.filter_by(name=name).first()
        if existing_user:
            return jsonify({'message': 'User already exists. Please choose a different username.'}), 409

        new_customer = Customers(name=name, city=city, age=age, password=password)
        db.session.add(new_customer)
        db.session.commit()

        return jsonify({'message': 'Customer registered successfully'})

# login costumer 
# if user didnt login -  can not access other routes/pages rather than register 
@app.route("/login", methods=['POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name')
        password = data.get('password')

        if authentication_successful(name, password):
            custName = customer.query.filter_by(name=name).first().custID
            token = generate_token(custName)
            return jsonify({'token': token})

        if custName and bcrypt.check_password_hash(custName.password, password):
            access_token = generate_token(identity=name)
            return jsonify({'message': 'Login successful', 'access_token': access_token})
        else:
            return jsonify({'message': 'Invalid username or password'}), 401



# logout costumer
# fix logout so it blocks connction to the other endpoints 
@app.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    # Extract the token's identifier (jti)
    jti = get_jwt()["jti"]
    
    try:
        # Add the token identifier to the invalidated tokens list
        invalidated_tokens.add(jti)
        session.clear()  # Clear the session
        return jsonify({"message": "Logout successful"}), 200
    except Exception as e:  # Catch any unexpected errors
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500


@app.route('/customer_book_list', methods=['GET'])
def get_customer_book_list():
    result = db.session.query(Customers.name, Books.name)\
                    .join(Loans, Customers.custID == Loans.custID)\
                    .join(Books, Loans.bookID == Books.bookID)\
                    .all()

    # Format the result as desired, e.g., return a JSON response
    return jsonify([{"customer": customer_name, "book": name} for customer_name, book_name in result])


# gereate a token for the costumer as user fo library 
def generate_token(custID):
    expiration_time = datetime.timedelta(minutes=20)
    token = create_access_token(identity=custID, expires_delta=expiration_time)
    return token

# entry point of the app 
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create the database tables before running the app
    app.run(debug=True, port=5000)
