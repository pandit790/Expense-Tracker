from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Create database if not exists
def init_db():
    conn = sqlite3.connect('expense_tracker.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        title TEXT,
                        amount REAL,
                        category TEXT,
                        date TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect('expense_tracker.db')
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
            conn.commit()
            conn.close()
            flash("Registration successful. Please log in.", "success")
            return redirect('/login')
        except:
            conn.close()
            flash("User already exists! Try logging in.", "danger")
            return redirect('/register')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect('expense_tracker.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ? AND password = ?", (email, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            flash("Login successful!", "success")
            return redirect('/dashboard')
        else:
            flash("Invalid credentials", "danger")
            return redirect('/login')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Logged out successfully.", "info")
    return redirect('/login')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('expense_tracker.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        title = request.form['title']
        amount = float(request.form['amount'])
        category = request.form['category']
        date = request.form['date']
        cursor.execute("INSERT INTO expenses (user_id, title, amount, category, date) VALUES (?, ?, ?, ?, ?)",
                       (session['user_id'], title, amount, category, date))
        conn.commit()
        flash("Expense added successfully.", "success")

    cursor.execute("SELECT id, title, amount, category, date FROM expenses WHERE user_id = ?", (session['user_id'],))
    expenses = cursor.fetchall()

    expense_list = []
    total_expense = 0
    category_data = {}

    for e in expenses:
        expense = {
            'id': e[0],
            'title': e[1],
            'amount': e[2],
            'category': e[3],
            'date': e[4]
        }
        expense_list.append(expense)
        total_expense += e[2]

        if e[3] in category_data:
            category_data[e[3]] += e[2]
        else:
            category_data[e[3]] = e[2]

    conn.close()

    return render_template(
        'dashboard.html',
        expenses=expense_list,
        total=total_expense,
        category_labels=list(category_data.keys()),
        category_values=list(category_data.values())
    )

@app.route('/delete/<int:id>')
def delete_expense(id):
    if 'user_id' not in session:
        return redirect('/login')
    conn = sqlite3.connect('expense_tracker.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (id, session['user_id']))
    conn.commit()
    conn.close()
    flash("Expense deleted.", "warning")
    return redirect('/dashboard')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_expense(id):
    if 'user_id' not in session:
        return redirect('/login')
    conn = sqlite3.connect('expense_tracker.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        title = request.form['title']
        amount = float(request.form['amount'])
        category = request.form['category']
        date = request.form['date']
        cursor.execute("""
            UPDATE expenses SET title = ?, amount = ?, category = ?, date = ?
            WHERE id = ? AND user_id = ?
        """, (title, amount, category, date, id, session['user_id']))
        conn.commit()
        conn.close()
        flash("Expense updated successfully.", "success")
        return redirect('/dashboard')
    else:
        cursor.execute("SELECT title, amount, category, date FROM expenses WHERE id = ? AND user_id = ?", (id, session['user_id']))
        expense = cursor.fetchone()
        conn.close()
        if expense:
            return render_template('edit.html', expense_id=id, title=expense[0], amount=expense[1], category=expense[2], date=expense[3])
        else:
            flash("Expense not found.", "danger")
            return redirect('/dashboard')

if __name__ == '__main__':
    app.run(debug=True)
