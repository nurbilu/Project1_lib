from flask import Flask, request, jsonify, abort 
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity , decode_token
import sqlite3
from flask_cors import CORS , cross_origin
from datetime import date 
from sqlalchemy.orm import class_mapper
from werkzeug.utils import secure_filename
import jwt
from flask_bcrypt import Bcrypt
import datetime



app = Flask(__name__)
app.secret_key = 'secret_secret_key'
api = Api(app)
# app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///library.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:1234@localhost/library' # change this to your own mysql database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your_secret_key_here'
db = SQLAlchemy(app)
jwt = JWTManager(app)
bcrypt = Bcrypt(app)
CORS(app )




# Define the authentication_successful function here
def authentication_successful(name, password):
    global customer
    customer = Customers.query.filter_by(name=name).first()
    if customer and bcrypt.check_password_hash(customer.password, password):
        return True
    return False

# set models 
class Books(db.Model):
    bookID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    author = db.Column(db.Text)
    year_published = db.Column(db.Integer, nullable=False)
    Type = db.Column(db.String(10))
    def __init__ (self, name, author, year_published, Type):
        self.name = name
        self.author = author
        self.year_published = year_published
        self.Type = Type
    
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
@app.route("/")
def test():
    return "test is on"

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
                'Type': book.Type
            }
            book_list.append(book_data)

        return jsonify({'books': book_list})

# add new book to table books
@app.route("/add_book", methods=['POST'])
@jwt_required()
def add_book():
    current_custID = get_jwt_identity()
    if request.method == 'POST':
        try:
            data = request.get_json()

            new_book = Books(
                name=data['name'],
                author=data['author'],
                year_published=data['year_published'],
                Type=data['Type']
            )

            db.session.add(new_book)
            db.session.commit()

            return jsonify({'message': 'Book added successfully'}), 200
        except Exception as e:
            print(f"Error adding book: {str(e)}")
            return jsonify({'message': 'Internal Server Error'}), 500
    
    
    

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
@app.route("/show_loans", methods=['GET'])
@jwt_required()
def show_loans():
    current_custID = get_jwt_identity()
    if request.method == 'GET':
        loans = Loans.query.all()
        loan_list = []
        for loan in loans:
            loan_data = {
                'id': loan.loanID,
                'custID': loan.custID,
                'bookID': loan.bookID,
                'LoanDate': loan.LoanDate,
                'ReturnDate': loan.ReturnDate
            }
            loan_list.append(loan_data)
        return jsonify({'loans': loan_list})

# add new loan to table loans
@app.route("/loan_book", methods=['POST'])
@jwt_required()
def loan_book():
    current_custID = get_jwt_identity()
    if request.method == 'POST':
        data = request.get_json()
        book_name = data.get('book_name')
        custID = data.get('custID')
        loanDate = data.get('LoanDate')
        returnDate = data.get('ReturnDate')

        if not book_name or not custID or not loanDate or not returnDate:
            return jsonify({'message': 'Invalid request. Please provide book_name, custID, LoanDate, and ReturnDate in the request.'}), 400

        book = Books.query.filter_by(name=book_name).first()
        customer = Customers.query.filter_by(custID=custID).first()

        if not book or not customer:
            return jsonify({'message': 'Book or customer not found.'}), 404

        new_loan = Loans(
            custID=custID,
            bookID=book.bookID,
            LoanDate=loanDate,
            ReturnDate=returnDate
        )
        db.session.add(new_loan)
        db.session.commit()

        return jsonify({'message': 'Book loaned successfully'})

# return book and delete loan from db 
@app.route("/return_book", methods=['POST'])
@jwt_required()
def return_book():
    current_custID = get_jwt_identity()
    if request.method == 'POST':
        data = request.get_json()
        book_name = data.get('book_name')
        customer_name = data.get('customer_name')
        
        if not book_name or not customer_name:
            return jsonify({'message': 'Invalid request. Please provide both book_name and customer_name in the request.'}), 400
        book = Books.query.filter_by(name=book_name).first()
        customer = Customers.query.filter_by(name=customer_name).first()

        if not book or not customer:
            return jsonify({'message': 'Book or customer not found.'}), 404

        loan = Loans.query.filter_by(bookID=book.bookID, custID=customer.custID).first()

        if not loan:
            return jsonify({'message': 'Loan not found.'}), 404

        return_date = date.today()

        if return_date:
            loan.ReturnDate = return_date
            db.session.commit()
            
            db.session.delete(loan)
            db.session.commit()

            return jsonify({'message': 'Book returned successfully and loan deleted.'})
        else:
            return jsonify({'message': 'Invalid request. Please provide ReturnDate in the request.'}), 400

# search book by name
@app.route("/search_book/", methods=['POST'])
@jwt_required()
def search_book():
    current_custID = get_jwt_identity()
    if request.method == 'POST':
        data = request.get_json()
        book = Books.query.filter_by(name=data['name']).first()
        if book:
            book_data = {
                'bookID': book.bookID,
                'name': book.name,
                'author': book.author,
                'year_published': book.year_published,
                'Type': book.Type
            }
            return jsonify({'book': book_data})
        else:
            return jsonify({'message': 'Book not found'})

# search customer by name 
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

# unit test - create a test book
@app.route("/book_test", methods=['POST'])
@jwt_required()
def book_test():
    current_custID = get_jwt_identity()
    if request.method == 'POST':
        books_data = [
            {"name": "1984", "author": "George Orwell", "year_published": 1949, "Type": "2 days"},
            {"name": "To Kill a Mockingbird", "author": "Harper Lee", "year_published": 1960, "Type": "5 days"},
            {"name": "The Great Gatsby", "author": "F. Scott Fitzgerald", "year_published": 1925, "Type": "10 days"}
        ]

        for book_data in books_data:
            book = Books(
                name=book_data['name'],
                author=book_data['author'],
                year_published=book_data['year_published'],
                Type=book_data['Type']
            )
            db.session.add(book)

        db.session.commit()

        return jsonify({'message': 'Books added successfully'})


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
        test_loan_data = {"book_name": "Test Book","custID": 1,"LoanDate": "2022-01-13", "ReturnDate": "2022-01-15"}
        book = Books.query.filter_by(name=test_loan_data['book_name']).first()

        if not book:
            return jsonify({'message': 'Book not found.'}), 404

        test_loan = Loans(
            custID=test_loan_data['custID'],
            bookID=book.bookID,
            LoanDate=test_loan_data['LoanDate'],
            ReturnDate=test_loan_data['ReturnDate']
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
@app.route("/logout", methods=['POST'])
def logout():
    if request.method == 'POST':
        # Extract the token from the Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(" ")[1]
        else:
            return jsonify({'message': 'Bearer token not provided'}), 401

        # Decode and validate the token
        try:
            payload = decode_token(token)
            name = payload.get('name')
        except Exception as e:
            return jsonify({'message': 'Invalid token. Error: ' + str(e)}), 401

        customer = Customers.query.filter_by(name=name).first()
        if customer:
            invalidate_token(token)  # Invalidate the token
            return jsonify({'message': 'Logout successful'})
        else:
            return jsonify({'message': 'Invalid user'}), 401



# gereate a token for the costumer as user fo library 
def generate_token(custID):
    expiration_time = datetime.timedelta(minutes=20)
    token = create_access_token(identity=custID, expires_delta=expiration_time)
    return token

# entry point of the app 
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create the database tables before running the app
    CORS(app)
    app.run(debug=True, port=5000)
