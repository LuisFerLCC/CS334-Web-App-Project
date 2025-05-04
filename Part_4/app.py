from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
# from datetime import datetime # To be used when submitting order.
import os

app = Flask(__name__)

# secret_key used for session information in order to keep the cart information available for adding/removing items and eventually for submitting orders.
app.secret_key = 'keyforusingsessions'

# SQLAlchemy setup in order to get it to work, had to use abspath command in order to get it to read the correct file, it kept throwing errors even though the DB was configured.
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'ITPot.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Creating the ORM for Item, using extend_existing because the database already existed and we're not creating from scratch.
class Item(db.Model):
    __tablename__ = 'Item'
    __table_args__ = {'extend_existing': True}
    
    ItemID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(50))
    Price = db.Column(db.Float)
    ImageURL = db.Column(db.String(100))
    IsCold = db.Column(db.Boolean)
    IsNoCaffeine = db.Column(db.Boolean)

# Creating the ORM model for Message, uses extend_existing because DB is already existing and not from scratch.
class Message(db.Model):
    __tablename__ = 'Message'
    __table_args__ = {'extend_existing': True}

    MessageID = db.Column(db.Integer, primary_key=True)
    SenderName = db.Column(db.String(100))
    Email = db.Column(db.String(100))
    Phone = db.Column(db.String(20))
    Body = db.Column(db.Text)

# This is the base page for index.html template, pulls 3 items to show as popular drinks.
@app.route('/')
def index():
    items = Item.query.order_by(Item.ItemID.desc()).limit(3).all()
    return render_template('index.html', featured=items)

# This is the shop page and it pulls all items from the DB in order to populate the page on the template.
@app.route('/shop')
def shop():
    items = Item.query.all()
    return render_template('shop.html', items=items)

# This is the cart page and uses the session to pull the cart information tied to it on the server side, then pulls all the items information for the cart and calculates the subtotal and total.
@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    entries = []
    total = 0.0
    for itemId, qunatity in cart.items():
        item = Item.query.get(itemId)
        if item:
            sub = item.Price * qunatity
            total += sub
            entries.append({'item': item, 'quantity': qunatity, 'subtotal': sub})
    return render_template('cart.html', entries=entries, total=total)

# This is the team page and is a static page.
@app.route('/team')
def team():
    return render_template('team.html')

# This is the contact page and is configured when using GET to just show the page, but then if it's POST, it pulls the information from the page and submits into DB using ORM. Redirects back to contact page when complete.
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        msg = Message(
            SenderName=request.form['name'],
            Email=request.form['email'],
            Phone=request.form['number'],
            Body=request.form['message']
        )
        db.session.add(msg)
        db.session.commit()
        return redirect(url_for('contact'))
    return render_template('contact.html')

# This is a POST command to use when adding one of the items from the Shop page into the cart, used to bring into the session's cart object, creates a Flash message, and then ensures stays on same page.
@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    itemId = str(request.form['itemId'])
    quantity = int(request.form['quantity'])
    cart = session.get('cart', {})
    cart[itemId] = cart.get(itemId, 0) + quantity
    session['cart'] = cart
    flash("Item added to cart!")
    return redirect(url_for('shop'))

# This is a POST command to use on the cart page when looking to remove an item from the cart, pulls the cart information for the session and then removes based on the itemId being removed.
@app.route('/remove-from-cart', methods=['POST'])
def remove_from_cart():
    itemId = request.form['itemId']
    cart = session.get('cart', {})
    if itemId in cart:
        del cart[itemId]
    session['cart'] = cart
    flash("Item removed from cart.")
    return redirect(url_for('cart'))

# Currently just clears the cart, creates a flash message that the payment was submitted, and then redirects to shop.
@app.route('/checkout', methods=['POST'])
def checkout():
    session['cart'] = {}
    flash("Payment submitted successfully!")
    return redirect(url_for('shop'))

if __name__ == '__main__':
    app.run(debug=True)