from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api
import sqlite3
from datetime import date

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///library.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://user:MYSQL@localhost/library'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# set models 
class Books(db.Model):
    bookID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    author = db.Column(db.Text)
    year_published = db.Column(db.Integer, nullable=False)
    Type = db.Column(db.String(10))
    
class Customers(db.Model):
    custID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(255))
    age = db.Column(db.Integer)
    password = db.Column(db.String(500))
    
class Loans(db.Model):
    loanID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    custID = db.Column(db.Integer, nullable=False)
    bookID = db.Column(db.Integer, nullable=False)
    LoanDate = db.Column(db.Date)
    ReturnDate = db.Column(db.Date)


# test route
@app.route("/")
def test():
    return "test is on"

# display all books
@app.route("/show_books", methods=['GET'])
def show_books():
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
def add_book():
    if request.method == 'POST':
        data = request.get_json()

        new_book = Books(
            bookID=data['bookID'],
            name=data['name'],
            author=data['author'],
            year_published=data['year_published'],
            Type=data['Type']
        )

        db.session.add(new_book)
        db.session.commit()

        return jsonify({'message': 'Book added successfully'})
    
    
    

# show all customers 
@app.route("/show_customers", methods=['GET'])
def show_customers():
    if request.method == 'GET':
        customers = Customers.query.all()
        customer_list = []
        for customer in customers:
            customer_data = {
                'customerID': customer.custID,
                'name': customer.name,
                'city': customer.city,
                'age': customer.age,
                'password': customer.password
            }
            customer_list.append(customer_data)

        return jsonify({'customers': customer_list})

# add new customer to table customers
@app.route("/add_customer", methods=['POST'])
def add_customer():
    if request.method == 'POST':
        data = request.get_json()
        new_customer = Customers(
            custID = data['custID'],
            name=data['name'],
            city=data['city'],
            age=data['age'],
            password=data['password']
        )
        db.session.add(new_customer)
        db.session.commit()
        return jsonify({'message': 'Customer added successfully'})
 
# show all loans
@app.route("/show_loans", methods=['GET'])
def show_loans():
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
# need to update loan_book without loanID - auto incremnt 
@app.route("/loan_book", methods=['POST'])
def loan_book():
    if request.method == 'POST':
        data = request.get_json()
        new_loan = Loans(
            loanID = data['loanID'],
            custID=data['custID'],
            bookID=data['bookID'],
            LoanDate=data['LoanDate'],
            ReturnDate=data['ReturnDate']
        )
        db.session.add(new_loan)
        db.session.commit()
        return jsonify({'message': 'Book loaned successfully'})

# return book and delete loan from db 
@app.route("/return_book", methods=['POST'])
def return_book():
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
@app.route("/search_book/", methods=['POST'])
def search_book():
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
def search_customer():
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
def display_late_loans():
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
def book_test():
    if request.method == 'POST':
        test_book_data = {
        "name": "Test Book",
        "author": "Test Author",
        "year_published": 2023,
        "Type": "2 days"
    }


        test_book = Books(
            name=test_book_data['name'],
            author=test_book_data['author'],
            year_published=test_book_data['year_published'],
            Type=test_book_data['Type']
        )

        db.session.add(test_book)
        db.session.commit()

        return jsonify({'message': 'Test book added successfully'})

# unit test - create a test customer
@app.route("/customer_test", methods=['POST'])
def customer_test():
    if request.method == 'POST':
        test_customer_data = {
        "name": "<NAME>",
        "city": "Test City",
        "age": 20,
        "password": "<PASSWORD>"
    }   
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
# need fix to make this as add loan 
@app.route("/loan_test", methods=['POST'])
def loan_test():
    if request.method == 'POST':
        test_loan_data = {
        "loanID": 1,
        "custID": 1,
        "bookID": 1,
        "LoanDate": "2021-01-01",
        "ReturnDate": "2021-01-03"
    }
        test_loan = Loans(
            loanID=test_loan_data['loanID'],
            custID=test_loan_data['custID'],
            bookID=test_loan_data['bookID'],
            LoanDate=test_loan_data['LoanDate'],
            ReturnDate=test_loan_data['ReturnDate']
        )
        db.session.add(test_loan)
        db.session.commit()
        return jsonify({'message': 'Test loan added successfully'})


@app.route("/login", methods=['POST'])
def login():
    if request.method == 'POST':
        pass
    
    
@app.route("/register", methods=['POST'])
def register():
    if request.method == 'POST':
        pass


@app.route("/logout", methods=['POST'])
def logout():
    if request.method == 'POST':
        pass



# entry point of the app 
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create the database tables before running the app
    app.run(debug=True, port=5000)
