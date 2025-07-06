from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False
app.config['REMEMBER_COOKIE_HTTPONLY'] = True

# Security Headers
@app.after_request
def set_secure_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# Login Required Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists.', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    user_id = session['user_id']
    if request.method == 'POST':
        title = request.form['title']
        amount = float(request.form['amount'])
        category = request.form['category']
        date = request.form['date']

        new_expense = Expense(title=title, amount=amount, category=category, date=date, user_id=user_id)
        db.session.add(new_expense)
        db.session.commit()
        flash('Expense added!', 'success')
        return redirect(url_for('dashboard'))

    expenses = Expense.query.filter_by(user_id=user_id).all()
    total = sum(exp.amount for exp in expenses)
    return render_template('dashboard.html', expenses=expenses, total=total)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    expense = Expense.query.get_or_404(id)
    if request.method == 'POST':
        expense.title = request.form['title']
        expense.amount = float(request.form['amount'])
        expense.category = request.form['category']
        expense.date = request.form['date']
        db.session.commit()
        flash('Expense updated.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit.html', expense=expense)

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    expense = Expense.query.get_or_404(id)
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted.', 'info')
    return redirect(url_for('dashboard'))

@app.route('/analytics')
@login_required
def analytics():
    user_id = session['user_id']
    expenses = Expense.query.filter_by(user_id=user_id).all()

    category_data = {}
    for expense in expenses:
        category_data[expense.category] = category_data.get(expense.category, 0) + expense.amount

    labels = list(category_data.keys())
    values = list(category_data.values())

    return render_template('analytics.html', category_labels=labels, category_values=values)

# Run App
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)




