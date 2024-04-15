from flask import Flask, request, jsonify, abort , send_from_directory , session
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity , decode_token , get_jwt
import sqlite3
from flask_cors import CORS ,cross_origin
from datetime import date  , timedelta
from sqlalchemy import Enum , and_ , or_
from sqlalchemy.orm import class_mapper , joinedload
from werkzeug.utils import secure_filename
import jwt
from flask_bcrypt import Bcrypt
import datetime
import json
import random
import re


app = Flask(__name__, static_folder='../frontend')
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

class Books(db.Model):
    bookID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    author = db.Column(db.Text)
    year_published = db.Column(db.Integer, nullable=False)
    book_type = db.Column(db.Enum('Up to 10 days' , 'Up to 5 days', 'Up to 2 days') )
    PIC_link = db.Column(db.String(1500))
    def __init__(self, name, author, year_published, book_type, PIC_link):
        self.name = name
        self.author = author
        self.year_published = year_published
        self.book_type = book_type
        self.PIC_link = PIC_link if PIC_link else 'https://clipart-library.com/images/6Tpo6G8TE.jpg'

    
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
        

class Friendship(db.Model):
    requester_id = db.Column(db.Integer, db.ForeignKey('customer.id'), primary_key=True)
    friend_id = db.Column(db.Integer, db.ForeignKey('customer.id'), primary_key=True)
    status = db.Column(db.String(10), default='pending')  # Possible values: pending, accepted, rejected
    def __init__(self, requester_id, friend_id, status):
        self.requester_id = requester_id
        self.friend_id = friend_id
        self.status = status


# set routes
# test route

@app.route("/")
def test():
    return "test is on"


# @app.route("/")
# def home():
#     return send_from_directory(app.static_folder, 'home.html')





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

        if book_type not in ['Up to 10 days', 'Up to 5 days', 'Up to 2 days']:
            return "Invalid book_type", 400

        new_book = Books(name=name, author=author, year_published=int(year_published),book_type=book_type, PIC_link=PIC_link)

        try:
            db.session.add(new_book)
            db.session.commit()
            return "Book added successfully", 201
        except Exception as e:
            db.session.rollback()
            return str(e), 500
    
    
    


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
 

@app.route("/show_loans", methods=["GET"])
@jwt_required()
def show_loans():
    current_custID = get_jwt_identity()
    if request.method == "GET":
        loans = Loans.query.filter_by(custID=current_custID).all()
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


@app.route("/loan_book", methods=["POST"])
@jwt_required()
def loan_book():
    current_custID = get_jwt_identity()
    if request.method == "POST":
        data = request.get_json()
        book_name = data.get("name")
        loanDate_str = data.get("LoanDate")
        if loanDate_str:
            year, month, day = map(int, loanDate_str.split('-'))
            loanDate = date(year, month, day)
        else:
            loanDate = date.today()

        if not book_name:
            return jsonify({"message": "Invalid request. Please provide the book name."}), 400

        book = Books.query.filter_by(name=book_name).first()
        if not book:
            return jsonify({"message": "Book not found."}), 404

        customer = Customers.query.filter_by(custID=current_custID).first()
        if not customer:
            return jsonify({"message": "Customer not found."}), 404

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


@app.route("/return_book", methods=['POST'])
@jwt_required()
def return_book():
    current_custID = get_jwt_identity()
    if request.method == 'POST':
        data = request.get_json()
        book_name = data.get('name')

        if not book_name:
            return jsonify({'message': 'Invalid request. Please provide the book name in the request.'}), 400

        book = Books.query.filter_by(name=book_name).first()
        if not book:
            return jsonify({'message': 'Book not found.'}), 404

        loan = Loans.query.filter_by(bookID=book.bookID, custID=current_custID).first()
        if not loan:
            return jsonify({'message': 'No active loan found for this book and user.'}), 404

        return_date = data.get('ReturnDate')
        if return_date:
            year, month, day = map(int, return_date.split('-'))
            loan.ReturnDate = date(year, month, day)
            db.session.commit()
            
            db.session.delete(loan)
            db.session.commit()

            return jsonify({'message': 'Book returned successfully and loan deleted.'})
        else:
            return jsonify({'message': 'Invalid request. Please provide ReturnDate in the request.'}), 400



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
                'book_type': book.book_type,
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

    
@app.route("/display_late_loans", methods=['GET'])
@jwt_required()
def display_late_loans():
    current_custID = get_jwt_identity()
    today = date.today()

    late_loans = db.session.query(Loans, Books).join(Books, Loans.bookID == Books.bookID) \
        .filter(Loans.custID == current_custID, Loans.ReturnDate < today).all()

    late_loan_list = []
    for loan, book in late_loans:
        late_loan_data = {
            'id': loan.loanID,
            'custID': loan.custID,
            'bookID': book.bookID,
            'bookName': book.name,
            'LoanDate': loan.LoanDate.strftime('%Y-%m-%d'),
            'ReturnDate': loan.ReturnDate.strftime('%Y-%m-%d'),
            'BookType': book.book_type
        }
        late_loan_list.append(late_loan_data)
    return jsonify({'late_loans': late_loan_list})

def get_loan_duration_days(book_type):
    duration_mapping = {
        'Up to 10 days': 10,
        'Up to 5 days': 5,
        'Up to 2 days': 2
    }
    return duration_mapping.get(book_type, 0)

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
                "PIC_link": "https://clipart-library.com/images/6Tpo6G8TE.jpg",
            },
            {
                "name": "One Hundred Years of Solitude",
                "author": "Gabriel García Márquez",
                "year_published": 1967,
                "book_type": "Up to 5 days",
                "PIC_link": "https://clipart-library.com/images/6Tpo6G8TE.jpg",
            },
            {
                "name": "The Little Prince",
                "author": "Antoine de Saint-Exupéry",
                "year_published": 1943,
                "book_type": "Up to 10 days",
                "PIC_link": "https://clipart-library.com/images/6Tpo6G8TE.jpg",
            },
            {
                "name": "The Diary of Anne Frank",
                "author": "Anne Frank",
                "year_published": 1947,
                "book_type": "Up to 10 days",
                "PIC_link": "https://clipart-library.com/images/6Tpo6G8TE.jpg",
            },
            {
                "name": "The Adventures of Huckleberry Finn",
                "author": "Mark Twain",
                "year_published": 1884,
                "book_type": "Up to 5 days",
                "PIC_link": "https://clipart-library.com/images/6Tpo6G8TE.jpg",
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




@app.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    
    try:
        invalidated_tokens.add(jti)
        session.clear() 
        return jsonify({"message": "Logout successful"}), 200
    except Exception as e: 
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500


@app.route('/customer_book_list', methods=['GET'])
def get_customer_book_list():
    result = db.session.query(Customers.name, Books.name)\
                    .join(Loans, Customers.custID == Loans.custID)\
                    .join(Books, Loans.bookID == Books.bookID)\
                    .all()
    return jsonify([{"customer": customer_name, "book": book_name} for customer_name, book_name in result])


def generate_token(custID):
    expiration_time = datetime.timedelta(minutes=20)
    token = create_access_token(identity=custID, expires_delta=expiration_time)
    return token


if __name__ == "__main__":
    with app.app_context():
        db.create_all()  
    app.run(debug=True, port=5000)
