import os

from cs50 import SQL
#import sqlite3 as SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import datetime
from helpers import apology, login_required, usd, watt
import json
import secrets


# Configure application
app = Flask(__name__)


# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd
app.jinja_env.filters["watt"] = watt

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")#, check_same_thread=False)
# con = SQL.connect("finance.db")
# with con:
#     db = con.cursor()
try:
    db.execute("""CREATE TABLE 'history'('history_id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    'user_id' INTEGER NOT NULL, 'name' TEXT NOT NULL, 'price' NUMERIC NOT NULL,
    'quantity' INTEGER UNSIGNED NOT NULL, 'type' TEXT NOT NULL, 'date' DATE, FOREIGN KEY ('user_id') REFERENCES 'users'('id')); """)
    db.execute("""CREATE UNIQUE INDEX 'history_id' ON 'history'('history_id');""")
except:
    print("History Table already exists")

try:
    db.execute("""CREATE TABLE 'products'('product_id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 'name' TEXT NOT NULL,
    'api_key' TEXT NOT NULL, 'activated' TEXT NOT NULL, 'type' TEXT NOT NULL); """)
    db.execute("""CREATE UNIQUE INDEX 'product_id' ON 'product'('product_id');""")
except:
    print("Product Table already exists")

try:
    db.execute("""CREATE TABLE 'mails'('mail_id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    'user_id' INTEGER NOT NULL, 'description' TEXT NOT NULL, 'type' TEXT NOT NULL, is_read BIT(1) TEXT NOT NULL, 'date' DATE, FOREIGN KEY ('user_id') REFERENCES 'users'('id')); """)
    db.execute("""CREATE UNIQUE INDEX 'mail_id' ON 'mails'('mail_id');""")
except:
    print("Mails Table already exists")

try:
    db.execute("""CREATE TABLE 'devices'('device_id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
		'user_id' INTEGER NOT NULL, 'name' TEXT NOT NULL, 'state' TEXT NOT NULL,
		'consumption' INTEGER NOT NULL, FOREIGN KEY('user_id') REFERENCES 'users'('id'));""")
    db.execute("""CREATE UNIQUE INDEX 'device_id' ON 'device'('device_id');""")
except:
    print("Device Table already exists")

try:
    db.execute("""CREATE TABLE 'generators'('generator_id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
		'user_id' INTEGER NOT NULL, 'name' TEXT NOT NULL, 'state' TEXT NOT NULL,
		'unused_energy' INTEGER NOT NULL, 'selling_energy' INTEGER NOT NULL, 'total_energy' INTEGER NOT NULL, FOREIGN KEY('user_id') REFERENCES 'users'('id'));""")
    db.execute("""CREATE UNIQUE INDEX 'generator_id' ON 'generators'('generator_id');""")
except:
    print("Generators Table already exists")

try:
    db.execute("""CREATE TABLE 'energy'('energy_id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        'user_id' INTEGER NOT NULL, 'description' TEXT NOT NULL,
		'amount' INTEGER NOT NULL, 'expiration_date' DATE, 'price' INTEGER NOT NULL, FOREIGN KEY('user_id') REFERENCES 'users'('id'));""")
    db.execute("""CREATE UNIQUE INDEX 'energy_id' ON 'energy'('energy_id');""")
except:
    print("Energy Table already exists")

# Make sure API key is set
# if not os.environ.get("API_KEY"):
#     raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # db = SQL("sqlite:///finance.db")
    # rows = db.execute("SELECT * FROM users WHERE id = :user_id", user_id = session["user_id"])
    # cash = rows[0]['cash']
    # rows = db.execute("SELECT * FROM shares WHERE user_id = :user_id", user_id = session["user_id"])
    # prices = []
    # total = cash
    # for row in rows:
    #     temp = lookup(row['symbol'])['price']
    #     prices.append(temp)
    #     total += (temp * row['quantity'])
    db = SQL("sqlite:///finance.db")
    count = db.execute("SELECT COUNT(*) FROM mails WHERE user_id = :user_id AND is_read = :is_read", user_id=session["user_id"], is_read = 0)
    session["mail"] = count[0]['COUNT(*)']
    rows = db.execute("SELECT * FROM users WHERE id = :user_id", user_id = session["user_id"])
    session["cash"] = rows[0]['cash']
    return render_template("index.html") #, cash = cash, rows = rows, prices = prices, total = total)


@app.route("/account", methods=["POST", "GET"])
@login_required
def account():
    db = SQL("sqlite:///finance.db")

    count = db.execute("SELECT COUNT(*) FROM mails WHERE user_id = :user_id AND is_read = :is_read", user_id=session["user_id"], is_read = 0)
    session["mail"] = count[0]['COUNT(*)']
    rows = db.execute("SELECT * FROM users WHERE id = :user_id", user_id = session["user_id"])
    session["cash"] = rows[0]['cash']

    if request.method == "GET":
        gen_rows = db.execute("SELECT * FROM generators WHERE user_id = :user_id", user_id = session["user_id"])
        dev_rows = db.execute("SELECT * FROM devices WHERE user_id = :user_id", user_id = session["user_id"])
        # generated_key = secrets.token_urlsafe(16)
        # hashed = generate_password_hash(generated_key)
        # print(generated_key)
        # print(hashed)
        # print(check_password_hash(hashed, generated_key))
        return render_template("account.html", gen_rows=gen_rows, dev_rows=dev_rows)
    else:
        res = request.get_json()
        if res['method'] == 'generator':
            row = db.execute("SELECT * FROM products WHERE api_key = :api_key", api_key = res['api_key'])
            if len(row) != 1:
                return "not found", 200
            elif row[0]['type'] != 'generator':
                return 'not generator', 200
            elif row[0]['activated'] != "no":
                return "already owned", 200
            else:
                db.execute("UPDATE products SET activated = :activated WHERE product_id = :product_id", activated = "yes", product_id = row[0]['product_id'])
                db.execute("""INSERT INTO generators (user_id, name, state, unused_energy, selling_energy, total_energy)
                            VALUES (:user_id, :name, :state, :unused_energy, :selling_energy, :total_energy)""",
                            user_id=session["user_id"], name=row[0]['name'], state="initialized", unused_energy=1000, selling_energy=0, total_energy=1000)
                return "activated!", 200
        elif res['method'] == 'smart_plug':
            row = db.execute("SELECT * FROM products WHERE api_key = :api_key", api_key = res['api_key'])
            if len(row) != 1:
                return "not found", 200
            elif row[0]['type'] != 'device':
                return 'not device', 200
            elif row[0]['activated'] != "no":
                return "already owned", 200
            else:
                # set activated
                db.execute("UPDATE products SET activated = :activated WHERE product_id = :product_id", activated = "yes", product_id = row[0]['product_id'])
                db.execute("""INSERT INTO devices (user_id, name, state, consumption)
                            VALUES (:user_id, :name, :state, :consumption)""",
                            user_id=session["user_id"], name=row[0]['name'], state="initialized", consumption=0)
                return "activated!", 200


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    db = SQL("sqlite:///finance.db")

    count = db.execute("SELECT COUNT(*) FROM mails WHERE user_id = :user_id AND is_read = :is_read", user_id=session["user_id"], is_read = 0)
    session["mail"] = count[0]['COUNT(*)']
    rows = db.execute("SELECT * FROM users WHERE id = :user_id", user_id = session["user_id"])
    session["cash"] = rows[0]['cash']

    if request.method == 'POST':
        res = request.get_json()
        # delete contract from "energy"
        # add "buy" to "history"
        # subtract "cash" from "users"
        # proceed to transport energy
        if db.execute("SELECT 1 FROM energy WHERE energy_id = :energy_id", energy_id=res['energy_id']):
            id_check = db.execute("SELECT user_id FROM energy WHERE energy_id=:energy_id", energy_id=res['energy_id'])
            id_check = id_check[0]['user_id']
            if id_check == session["user_id"]:
                return 'your auction', 200
            else:
                ## delete energy auction from energy table
                db.execute("DELETE FROM energy WHERE user_id = :user_id AND energy_id = :energy_id",
                        user_id = res['user_id'], energy_id = res['energy_id'])
                ## add history (buy) to the buyer
                db.execute("INSERT INTO history (user_id, name, price, quantity, type, date) VALUES (:user_id, :name, :price, :quantity, :type, :date)",
                        user_id=session["user_id"], name="Energy transaction", price=res['price'], quantity=res['amount'], type='buy', date = datetime.datetime.now())
                ## remove cash buyer
                db.execute("UPDATE users SET cash = cash - :amount WHERE id = :user_id", amount=res['price'], user_id = session["user_id"])
                ## add cash to the owner of that contract
                db.execute("UPDATE users SET cash = cash + :amount WHERE id = :user_id", amount=res['price'], user_id = id_check)
                ## add history to the owner (sold)
                db.execute("INSERT INTO history (user_id, name, price, quantity, type, date) VALUES (:user_id, :name, :price, :quantity, :type, :date)",
                        user_id=id_check, name="Energy transaction", price=res['price'], quantity=res['amount'], type='sold', date = datetime.datetime.now())
                ## send a mesasge to the owner of that contract
                description = "Your contract has been sold for " + str(res['amount']) + " Watts, " + str(res['price']) + "$, at " + str(datetime.datetime.now())
                db.execute("INSERT INTO mails (user_id, description, type, is_read, date) VALUES (:user_id, :description, :type, :is_read, :date)", user_id=id_check, description=description, type="sold", is_read =0, date=datetime.datetime.now())
                return 'OK', 200
        else:
            return 'its gone', 200



@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    db = SQL("sqlite:///finance.db")

    count = db.execute("SELECT COUNT(*) FROM mails WHERE user_id = :user_id AND is_read = :is_read", user_id=session["user_id"], is_read = 0)
    session["mail"] = count[0]['COUNT(*)']
    rows = db.execute("SELECT * FROM users WHERE id = :user_id", user_id = session["user_id"])
    session["cash"] = rows[0]['cash']


    rows = db.execute("SELECT * FROM history WHERE user_id=:user_id", user_id=session["user_id"])
    return render_template("history.html", rows=rows)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()
    db = SQL("sqlite:///finance.db")
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        # con = SQL.connect("finance.db")
        # with con:
        #     con.row_factory = SQL.Row
        #     db = con.cursor()
        rows = db.execute("SELECT * FROM users WHERE username = :username", username = request.form.get("username"))
        # rows = db.fetchall()
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["cash"] = rows[0]['cash']
        count = db.execute("SELECT COUNT(*) FROM mails WHERE user_id = :user_id AND is_read = :is_read", user_id=session["user_id"], is_read = 0)
        session["mail"] = count[0]['COUNT(*)']

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/auction", methods=["GET", "POST"])
@login_required
def auction():
    """Shows list of available auctions:
    """
    if request.method == "POST":
        return "123"
    else:
        db = SQL("sqlite:///finance.db")
        rows = db.execute("SELECT * FROM users WHERE id = :user_id", user_id = session["user_id"])
        session["cash"] = rows[0]['cash']
        count = db.execute("SELECT COUNT(*) FROM mails WHERE user_id = :user_id AND is_read = :is_read", user_id=session["user_id"], is_read = 0)
        session["mail"] = count[0]['COUNT(*)']

        rows = db.execute("""SELECT * FROM energy""")
        cash = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id = session["user_id"])
        return render_template("auction.html", rows = rows, cash = cash)


@app.route("/register", methods=["GET", "POST"])
def register():
    db = SQL("sqlite:///finance.db")
    if request.method == "POST":
        passed = True
        if not request.form.get("username"):
            passed = False
            text = "Must provide username"
        elif not request.form.get("email"):
            passed = False
            text = "Must provide e-mail"
        elif not request.form.get("password"):
            passed = False
            text = "Must provide password"
        elif not request.form.get("confirmation"):
            passed = False
            text = "Must provide password"
        elif request.form.get("password") != request.form.get("confirmation"):
            passed = False
            text = "Passwords don't match"
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                         username=request.form.get("username"))
        if len(rows) != 0:
            passed = False
            text = "Username already exists"

        if not passed:
            return apology(text, 403)
        else:
            username = request.form.get("username")
            hashed = generate_password_hash(request.form.get("password"))
            db.execute("INSERT INTO users (username, hash) VALUES (:username, :hashed)", username=username, hashed=hashed)
            #"""CREATE TABLE 'emails'('email_id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 'email' TEXT NOT NULL, 'user_id' INTEGER NOT NULL,
            #    FOREIGN KEY ('user_id') REFERENCES 'users'('id'));"""
            return redirect("/")
    else:
        return render_template("registration.html")

    """Register user"""
    #return apology("TODO")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    db = SQL("sqlite:///finance.db")
    rows = db.execute("SELECT * FROM users WHERE id = :user_id", user_id = session["user_id"])
    session["cash"] = rows[0]['cash']
    count = db.execute("SELECT COUNT(*) FROM mails WHERE user_id = :user_id AND is_read = :is_read", user_id=session["user_id"], is_read = 0)
    session["mail"] = count[0]['COUNT(*)']

    rows = db.execute("SELECT * FROM generators WHERE user_id LIKE (:user_id)", user_id = session["user_id"])
    if request.method == "POST":
        index = request.form.get("index")
        if index == 'Choose...':
            return apology("Enter valid response")
        else:
            index = int(index)
            energy = int(request.form.get("energy"))
            if energy > rows[index]['unused_energy']:
                return apology("You don't own that much of available energy")
            else:
                db.execute("UPDATE generators SET unused_energy = unused_energy - :energy, selling_energy = selling_energy + :energy WHERE generator_id = :generator_id",
                                energy = energy, generator_id = rows[index]['generator_id']);
                db.execute("INSERT INTO energy (user_id, description, amount, expiration_date, price) VALUES (:user_id, :description, :amount, :exp_date, :price)",
                                user_id = session["user_id"], description = request.form.get("description"), amount = energy, exp_date = datetime.datetime.now() + datetime.timedelta(days = 2), price = request.form.get("price"))
                db.execute("INSERT INTO history (user_id, name, price, quantity, type, date) VALUES (:user_id, :name, :price, :quantity, :type, :date)",
                                user_id=session["user_id"], name="Energy transaction", price=request.form.get("price"), quantity = energy, type='created auction', date = datetime.datetime.now())
                return redirect('/history')
    else:
        return render_template("sell.html", rows = rows)

@app.route("/inbox", methods = ["GET", "POST"])
@login_required
def inbox():
    db = SQL("sqlite:///finance.db")
    rows = db.execute("SELECT * FROM users WHERE id = :user_id", user_id = session["user_id"])
    session["cash"] = rows[0]['cash']
    if request.method == "POST":
        res = request.get_json()
        if res == "mark_all":
            db.execute("UPDATE mails SET is_read = 1 WHERE user_id=:user_id AND is_read=:is_read", user_id=session["user_id"], is_read=0)
            session["mail"] = 0
            return "marked_all"
        else:
            db.execute("UPDATE mails SET is_read = 1 WHERE user_id=:user_id AND mail_id=:mail_id", user_id=session["user_id"], mail_id=res['mail_id'])
            session["mail"] = session["mail"] - 1
            if session["mail"] < 0:
                session["mail"] = 0
            return "marked"
    else:
        rows = db.execute("SELECT * FROM mails WHERE user_id=:user_id", user_id=session["user_id"])
        #session["mail"] = 0
        return render_template("inbox.html", rows = rows)

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
