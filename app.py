from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import pickle
from traceback import format_exc
import numpy as np
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
import secrets
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

popular_df = pickle.load(open('popular.pkl', 'rb'))
pt = pickle.load(open('pt.pkl', 'rb'))
books = pickle.load(open('books.pkl', 'rb'))
similarity_scores = pickle.load(open('similarity_scores.pkl', 'rb'))

app = Flask(__name__)
bcrypt = Bcrypt(app)

# Configure the MySQL database connection
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
mail = Mail(app)

app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.Enum('Male', 'Female', 'Other', 'Prefer not to say'))
    logo = db.Column(db.String(10), nullable=False)
    terms_accepted = db.Column(db.Boolean, nullable=False)
    registration_date = db.Column(db.TIMESTAMP, server_default=db.func.now())
    verification_code = db.Column(db.String(100))
    verified = db.Column(db.Boolean, default=False)


class BookSummary(db.Model):
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    book_title = db.Column(db.String(255), unique=True, nullable=False)
    author = db.Column(db.String(255))
    summary = db.Column(db.Text, nullable=False)
    purchase_link = db.Column(db.String(255))
    imageUrl = db.Column(db.String(255))
    price = db.Column(db.Integer)


class UserSearchHistory(db.Model):
    __tablename__ = 'user_search_history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    search_query = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.TIMESTAMP, server_default=db.func.now())


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    purchase_date = db.Column(
        db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=False)
    book_quantity = db.Column(db.Integer, nullable=False)
    total_book_price = db.Column(db.Integer, nullable=False)
    book_type = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(255))
    purchase_method = db.Column(db.String(50), nullable=False)
    shipping_method = db.Column(db.String(50))
    delivery_date = db.Column(db.Date)
    tracking_number = db.Column(db.String(50))


def generate_sequential_tracking_number():
    last_order = Order.query.order_by(Order.id.desc()).first()
    if last_order:
        last_number = int(last_order.tracking_number.split('-')[-1])
        new_number = last_number + 1
    else:
        new_number = 1

    return f"TN-{new_number:04d}"


def get_user_data():
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)
        if user:
            user_is_logged_in = True
            username = user.username
            logo = user.logo
            email = user.email
            full_name = user.full_name

            return user_is_logged_in, username, logo, email, full_name
        else:
            # user_is_logged_in = False
            return False, "Create or Login your Account..."
    else:
        # user_is_logged_in = False
        return False, "Create or Login your Account..."


def recommend_books(user_input):
    if user_input:
        user_input = user_input.lower()  # Convert user input to lowercase
        pt_lower = pt.index.str.lower()  # Convert book titles in pt to lowercase
        data = "Book not found in recommendations."

        if user_input in pt_lower:
            index = np.where(pt_lower == user_input)[0]
            if len(index) > 0:
                index = index[0]
                similar_items = sorted(
                    enumerate(similarity_scores[index]), key=lambda x: x[1], reverse=True)[1:5]

                data = []
                for i in similar_items:
                    item = []
                    temp_df = books[books['Book-Title'] == pt.index[i[0]]]
                    item.extend(list(temp_df.drop_duplicates(
                        'Book-Title')['Book-Title'].values))
                    item.extend(list(temp_df.drop_duplicates(
                        'Book-Title')['Book-Author'].values))
                    item.extend(list(temp_df.drop_duplicates(
                        'Book-Title')['Image-URL-M'].values))
                    data.append(item)
                return data
            else:
                return data
        else:
            return data
    else:
        data = "Please enter a book title."
        return data


def top_50_books():
    book_name = list(popular_df['Book-Title'].values)
    author = list(popular_df['Book-Author'].values)
    image = list(popular_df['Image-URL-M'].values)
    votes = list(popular_df['num_ratings'].values)
    rating = list(popular_df['avg_rating'].values.round())

    return book_name, author, image, votes, rating

# --------------------------------------


# Route to handle user registration
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    try:
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            full_name = request.form['full-name']
            date_of_birth = request.form['date-of-birth']
            gender = request.form['gender']
            parts = full_name.split()
            first_name = parts[0]
            last_name = parts[-1] if len(parts) > 1 else ""

            # Get the first letter of each part and combine them
            logo = first_name[0] + last_name[0]
            terms_accepted = request.form.get('terms-accepted') == "on"

            # Hash the password using Flask-Bcrypt
            password_hash = bcrypt.generate_password_hash(
                password).decode('utf-8')

            # Create a new user instance and add it to the database
            new_user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                full_name=full_name,
                date_of_birth=date_of_birth,
                gender=gender,
                logo=logo,
                terms_accepted=terms_accepted
            )

            # Generate a random OTP (6 digits)
            otp = secrets.randbelow(1000000)
            new_user.verification_code = str(otp).zfill(
                6)  # Pad OTP with zeros if needed

            try:
                db.session.add(new_user)
                db.session.commit()

                # Send the verification email
                verification_link = url_for(
                    'verify_email', code=new_user.verification_code, _external=True)
                msg = Message('Email Verification',
                              sender='www.malcolmdsouza9552@gmail.com', recipients=[new_user.email])
                # Include the verification code here
                msg.body = f'Your Verification code is: {
                    new_user.verification_code}'
                print(msg)
                # mail.send(msg)
                print(msg)

                flash(
                    'Registration successful! Please check your email for verification.', 'success')

            # flash('Registration successful!', 'success')
            # Redirect to another page
                return redirect(url_for('verify_email'))
            except IntegrityError:
                db.session.rollback()
                flash('Username or email already exists', 'danger')

        return render_template('signup.html')
    except Exception as e:
        print(format_exc())  # print the full traceback for debugging
        return 'Error: {}'.format(str(e)), 500


@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    # Query the database to find the user by username
    user = User.query.filter_by(username=username).first()

    if user and bcrypt.check_password_hash(user.password_hash, password):
        # User is logged in successfully
        session['user_id'] = user.id  # Store user's ID in the session
        flash('Login successful!', 'success')
        return redirect(url_for('index'))
    else:
        flash('Login unsuccessful. <br> Please check your credentials.', 'danger')
        return redirect(url_for('loginPage'))


# routing to HTML Files-------------------

@app.route('/')
def index():
    user_data = get_user_data()
    return render_template('index.html', user_data=user_data)


@app.route('/aboutUs')
def aboutUs():
    return render_template('aboutUs.html')


@app.route('/recommend')
def recommend_ui():
    user_data = get_user_data()
    if user_data[0]:
        return render_template('recommend.html', user_data=user_data)
    else:
        return render_template('recommend.html', user_data=user_data, message=user_data[1])


@app.route('/recommend_books', methods=['post'])
def recommend():
    user_data = get_user_data()
    user_input = request.form.get('user_input')
    if user_data[0]:
        # Get user input from the form
        data = recommend_books(user_input)
        if isinstance(data, str):
            return render_template('recommend.html', user_data=user_data, message=data)
        else:
            return render_template('recommend.html', user_data=user_data, data=data)
    else:
        return render_template('recommend.html', user_data=user_data, message=user_data[1])


@app.route('/top50')
def top50():
    user_data = get_user_data()
    book_name, author, image, votes, rating = top_50_books()
    return render_template('top50.html', user_data=user_data, book_name=book_name, author=author, image=image, votes=votes, rating=rating)


@app.route('/signUp')
def signUp():
    return render_template('signup.html')


@app.route('/loginPage')
def loginPage():
    return render_template('login.html')


# Route to handle email verification
@app.route('/verify_email', methods=['GET', 'POST'])
def verify_email():
    if request.method == 'POST':
        user_input_code = request.form['otp']
        if user_input_code:
            user = User.query.filter_by(
                verification_code=user_input_code).first()
            if user:
                user.verified = True
                db.session.commit()
                flash('Email verified successfully!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid verification code', 'danger')
        else:
            flash('Invalid verification code', 'danger')

    return render_template('verify.html')


@app.route('/logout')
def logout():
    if 'user_id' in session:
        session.pop('user_id', None)
        flash('You have been logged out', 'success')
        session['_flashes'] = []
    else:
        flash('You are not logged in', 'info')
    return redirect(url_for('index'))


@app.route('/get_book_summary')
def get_book_summary():
    book_title = request.args.get('title')

    # Query the database for the book summary
    book = BookSummary.query.filter_by(book_title=book_title).first()

    if book:
        return jsonify({'summary': book.summary, 'amazonUrl': book.purchase_link})
    else:
        return jsonify({'error': 'Book not found'})


@app.route('/buynow/<book_title>')
def buynow(book_title):
    user_data = get_user_data()
    data = recommend_books(book_title)
    print(book_title)
    # Query the database to fetch book details by book_title
    book = BookSummary.query.filter_by(book_title=book_title).first()

    if book:
        return render_template('buynow.html', book=book, user_data=user_data, data=data)
    else:
        return render_template('buynow.html', book=book, user_data=user_data, error="Book not found")


@app.route('/proceed', methods=['post'])
def proceed():
    user_data = get_user_data()
    # Retrieve data from the form
    book_type = request.form.get('book_type')
    quantity = int(request.form.get('quantity'))
    total_price = int(request.form.get('book_price'))
    book_title = request.form.get('book_title')

    # Store book data in a variable
    book_data = {
        'book_type': book_type,
        'quantity': quantity,
        'total_price': total_price,
        'book_title': book_title
    }
    return render_template('placeOrder.html', user_data=user_data, book_data=book_data)


@app.route('/placeOrder', methods=['post'])
def placeOrder():
    address = request.form.get('address')
    purchase_method = request.form.get('purchase-method')
    shipping_method = request.form.get('shipping-method')
    book_title = request.form.get('book_title')
    book_type = request.form.get('book_type')
    quantity = int(request.form.get('quantity'))
    total_price = int(request.form.get('total-price'))
    shipping_date_str = request.form.get('shipping-date')

    shipping_date = datetime.strptime(shipping_date_str, '%d-%m-%y')

    new_order = Order(
        user_id=session['user_id'],  # Assuming user is logged in
        address=address,
        purchase_method=purchase_method,
        shipping_method=shipping_method,
        book_type=book_type,
        book_quantity=quantity,
        total_book_price=total_price,
        delivery_date=shipping_date,
        tracking_number=generate_sequential_tracking_number()
    )
    print(new_order)

    try:
        db.session.add(new_order)
        db.session.commit()
        flash('Order placed successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error placing order: {str(e)}', 'danger')

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.secret_key = "r)u'L4i<X&U;T4Pk*)#4,S3\(Okje?+5"
    app.run(debug=True)
