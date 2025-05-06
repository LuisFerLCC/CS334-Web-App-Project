from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime # To be used when submitting order.
# from datetime import datetime # To be used when submitting order.
import os
import re

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

class Order(db.Model):
    __tablename__ = 'Order'
    __table_args__ = {'extend_existing': True}

    OrderID = db.Column(db.Integer, primary_key=True)
    CustomerFirstName = db.Column(db.String(50))
    CustomerLastName = db.Column(db.String(50))
    Email = db.Column(db.String(100))
    DateTime = db.Column(db.DateTime)
    Address = db.Column(db.String(200))
    Phone = db.Column(db.String(20))
    StatusID = db.Column(db.Integer)


class OrderedItems(db.Model):
    __tablename__ = 'OrderedItems'
    __table_args__ = {'extend_existing': True}

    OrderID = db.Column(db.Integer, db.ForeignKey('Order.OrderID'), primary_key=True)
    ItemID = db.Column(db.Integer, db.ForeignKey('Item.ItemID'), primary_key=True)
    Amount = db.Column(db.Integer, nullable=False)  # not Quantity
    SpecialInstructions = db.Column(db.String(100), nullable=True)

    order = db.relationship('Order', backref='order_items')
    item = db.relationship('Item')

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
    first = request.form['first_name'].strip()
    last = request.form['last_name'].strip()
    email = request.form['email'].strip()
    phone = request.form['phone'].strip()
    address = request.form['address'].strip()
    cardnumber = request.form.get('cardnumber', '').strip()
    expiration = request.form.get('expiration', '').strip()
    cvv = request.form.get('cvv', '').strip()

    if not all([first, last, email, phone, address, cardnumber, expiration, cvv]):
        flash("All fields are required.")
        return redirect(url_for('cart'))
    if not re.fullmatch(r'\d{13,19}', cardnumber):
        flash("Invalid card number. Must be 13–19 digits.")
        return redirect(url_for('cart'))
    if not re.fullmatch(r'\d{3,4}', cvv):
        flash("Invalid CVV. Must be 3 or 4 digits.")
        return redirect(url_for('cart'))
    if not re.fullmatch(r'(0[1-9]|1[0-2])/([0-9]{2})', expiration):
        flash("Expiration must be in MM/YY format.")
        return redirect(url_for('cart'))

    cart = session.get('cart', {})
    if not cart:
        flash("Your cart is empty.")
        return redirect(url_for('cart'))

    total = 0.0
    for item_id, qty in cart.items():
        item = Item.query.get(item_id)
        if item:
            total += item.Price * qty

    # Adding the order
    order = Order(
        CustomerFirstName=first,
        CustomerLastName=last,
        Email=email,
        DateTime=datetime.now(),
        Address=address,
        Phone=phone,
        StatusID=1
    )
    db.session.add(order)
    db.session.commit()

    # Add ordered items
    for item_id, quantity in cart.items():
        db.session.add(OrderedItems(OrderID=order.OrderID, ItemID=item_id, Amount=quantity))
    db.session.commit()

    session['cart'] = {}
    flash("Order submitted successfully!")
    return redirect(url_for('shop'))

#Creating the ORM model for user
class User(db.Model):
    __tablename__  = 'User'
    __table_args__ = {'extend_existing': True}

    UserID= db.Column(db.Integer,  primary_key=True)
    FirstName= db.Column(db.String(30), nullable=False)
    LastName = db.Column(db.String(30), nullable=False)
    Email= db.Column(db.String(50), unique=True, nullable=False)
    Password= db.Column(db.String(30), nullable=False)
    ManagesOrders= db.Column(db.Boolean,default=False, nullable=False)
    ManagesInventory= db.Column(db.Boolean,default=False, nullable=False)
    ManagesMessages= db.Column(db.Boolean,default=False, nullable=False)
    ManagesUsers= db.Column(db.Boolean,default=False, nullable=False)

    @property
    def full_name(self):
        return f"{self.FirstName} {self.LastName}"

@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        user = User.query.filter_by(Email=request.form['email'], Password=request.form['password']).first()
        if user:
            session['user_id']= user.UserID
            session['can_manage_orders']= user.ManagesOrders
            session['can_manage_inventory']= user.ManagesInventory
            session['can_manage_messages']= user.ManagesMessages
            session['can_manage_users']= user.ManagesUsers
            return redirect(url_for('admin_dashboard'))
        error = "Invalid credentials."
    return render_template('admin/login.html', error=error)

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('admin_login'))       
    raw_items = Item.query.all()
    inventory = []
    for i in raw_items:
        inventory.append({
            'sku':i.ItemID,               
            'series':getattr(i, 'Series', ''),  
            'name':i.Name,                
            'caffeinated': not i.IsNoCaffeine,    
            'cold':i.IsCold,               
            'stock':getattr(i, 'Stock', 0),    
            'price':i.Price                 
        }) 
    messages= Message.query.order_by(Message.MessageID.desc()).all()  
    users= User.query.all()  
    return render_template('admin/dashboard.html',inventory=inventory,messages=messages,users=users)

@app.route('/admin/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('admin_login'))



@app.route('/admin/users', methods=['GET', 'POST'])
def users():
    if 'user_id' not in session:
        return redirect(url_for('admin_login'))

    edit_id   = request.args.get('edit_user',   type=int)
    delete_id = request.args.get('delete_user', type=int)

    if delete_id and request.method == 'POST':
        u = User.query.get_or_404(delete_id)
        db.session.delete(u)
        db.session.commit()
        return redirect(url_for('users'))

    if request.method == 'POST':
        fn = request.form['first_name']
        ln = request.form['last_name']
        em = request.form['email']
        pw = request.form.get('password', '')
        o  = bool(request.form.get('manage_orders'))
        i  = bool(request.form.get('manage_inventory'))
        m  = bool(request.form.get('manage_messages'))
        u  = bool(request.form.get('manage_users'))


        if not (o or i or m or u):
            flash('Please select at least one permission.', 'danger')
            if edit_id:
                return redirect(url_for('users', edit_user=edit_id))
            else:
                return redirect(url_for('users', new=1))


        dup = User.query.filter_by(Email=em).first()
        if dup and (not edit_id or dup.UserID != edit_id):
            flash('That email is already in use.', 'danger')
            if edit_id:
                return redirect(url_for('users', edit_user=edit_id))
            else:
                return redirect(url_for('users', new=1))

        if edit_id:
            user = User.query.get_or_404(edit_id)
            user.FirstName= fn
            user.LastName= ln
            user.Email= em
            if pw:
                user.Password= pw
            user.ManagesOrders= o
            user.ManagesInventory= i
            user.ManagesMessages= m
            user.ManagesUsers= u
        else:
            user = User(
                FirstName=fn,
                LastName=ln,
                Email=em,
                Password=pw,
                ManagesOrders=o,
                ManagesInventory=i,
                ManagesMessages=m,
                ManagesUsers=u
            )
            db.session.add(user)

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Could not save user. Please try again.', 'danger')
            return redirect(url_for('users', edit_user=edit_id) if edit_id else url_for('users', new=1))

        return redirect(url_for('users'))

    new_user  = 'new' in request.args
    edit_user = User.query.get(edit_id) if edit_id else None
    users     = User.query.order_by(User.UserID).all()
    return render_template('admin/users.html',users=users,edit_user=edit_user,new_user=new_user)

@app.route('/admin/messages')
def messages():
    if 'user_id' not in session:
        return redirect(url_for('admin_login'))
    return render_template('admin/messages.html')

@app.route('/admin/inventory')
def inventory():
    if 'user_id' not in session:
        return redirect(url_for('admin_login'))
    return render_template('admin/inventory.html')

@app.route('/admin/orders')
def orders():
    if 'user_id' not in session:
        return redirect(url_for('admin_login'))
    return render_template('admin/orders.html')
@app.route('/sw.js')
def serve_sw():
    return send_from_directory(app.static_folder, 'sw.js',
                               mimetype='application/javascript')

if __name__ == '__main__':
    app.run(debug=True)