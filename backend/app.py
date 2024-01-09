from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
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
    year_published = db.Column(db.Integer)
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

@app.route("/return_book", methods=['POST'])
def return_book():
    if request.method == 'POST':
        data = request.get_json()
        loan = Loans.query.filter_by(loanID=data['loanID']).first()
        loan.ReturnDate = data['ReturnDate']
        db.session.commit()
        return jsonify({'message': 'Book returned successfully'})

@app.route("/search_book", methods=['POST'])
def search_book():
    if request.method == 'POST':
        data = request.get_json()
        book = Books.query.filter_by(book.name).first()
        book_data = {
            'bookID': book.bookID,
            'name': book.name,
            'author': book.author,
            'year_published': book.year_published,
            'Type': book.Type
        }
        return jsonify({'book': book_data})
    
@app.route("/search_customer", methods=['POST'])
def search_customer():
    if request.method == 'POST':
        data = request.get_json()
        customer = Customers.query.filter_by(customer.name).first()
        customer_data = {
            'id': customer.custID,
            'name': customer.name,
            'city': customer.city,
            'age': customer.age,
            # 'password': <PASSWORD>
        }
        return jsonify({'customer': customer_data})
    
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
    test_book_data = {
    "name": "Test Book",
    "author": "Test Author",
    "year_published": 2022,
    "Type": "Fiction"
}


    test_book = Books(**test_book_data)
    db.session.add(test_book)
    db.session.commit()

    return jsonify({'message': 'Test book created successfully'})


# unit test - create a test customer
@app.route("/customer_test", methods=['POST'])
def customer_test():
    pass

# unit test - create a test loan
@app.route("/loan_test", methods=['POST'])
def loan_test():
    pass



# entry point of the app 
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create the database tables before running the app
    app.run(debug=True, port=5000)
