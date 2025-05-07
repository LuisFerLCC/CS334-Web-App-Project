from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_from_directory,
    jsonify,
)
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message as MailMessage
from werkzeug.utils import secure_filename
from datetime import datetime  # To be used when submitting order.

# from datetime import datetime # To be used when submitting order.
import os
import re
import config as cf

app = Flask(__name__)

app.config["MAIL_SERVER"] = cf.MAIL_SERVER
app.config["MAIL_PORT"] = cf.MAIL_PORT
app.config["MAIL_USERNAME"] = cf.MAIL_USERNAME
app.config["MAIL_PASSWORD"] = cf.MAIL_PASSWORD
app.config["MAIL_USE_TLS"] = cf.MAIL_USE_TLS
app.config["MAIL_USE_SSL"] = cf.MAIL_USE_SSL
app.config["MAIL_DEFAULT_SENDER"] = cf.MAIL_DEFAULT_SENDER

mail = Mail(app)

# secret_key used for session information in order to keep the cart information available for adding/removing items and eventually for submitting orders.
app.secret_key = "keyforusingsessions"

# SQLAlchemy setup in order to get it to work, had to use abspath command in order to get it to read the correct file, it kept throwing errors even though the DB was configured.
basedir = os.path.abspath(os.path.dirname(__file__))
item_images_dir = os.path.join(basedir, "static", "img", "products")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    basedir, "ITPot.sqlite"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# Creating the ORM for Item, using extend_existing because the database already existed and we're not creating from scratch.
class Item(db.Model):
    __tablename__ = "Item"
    __table_args__ = {"extend_existing": True}

    ItemID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(30))
    Description = db.Column(db.String(65))
    IsNoCaffeine = db.Column(db.Boolean)
    IsCold = db.Column(db.Boolean)
    Stock = db.Column(db.Integer)
    Price = db.Column(db.Float)
    ImageURL = db.Column(db.String(50))
    SeriesID = db.Column(db.Integer, db.ForeignKey("Series.SeriesID"))
    IsActive = db.Column(db.Boolean, default=True)


class Series(db.Model):
    __tablename__ = "Series"
    __table_args__ = {"extend_existing": True}

    SeriesID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(30))


# Creating the ORM model for Message, uses extend_existing because DB is already existing and not from scratch.
class Message(db.Model):
    __tablename__ = "Message"
    __table_args__ = {"extend_existing": True}

    MessageID = db.Column(db.Integer, primary_key=True)
    SenderName = db.Column(db.String(100))
    Email = db.Column(db.String(100))
    Phone = db.Column(db.String(20))
    Body = db.Column(db.Text)


class Order(db.Model):
    __tablename__ = "Order"
    __table_args__ = {"extend_existing": True}

    OrderID = db.Column(db.Integer, primary_key=True)
    CustomerFirstName = db.Column(db.String(50))
    CustomerLastName = db.Column(db.String(50))
    Email = db.Column(db.String(100))
    DateTime = db.Column(db.DateTime)
    Address = db.Column(db.String(200))
    Phone = db.Column(db.String(20))
    StatusID = db.Column(db.Integer)


class OrderedItems(db.Model):
    __tablename__ = "OrderedItems"
    __table_args__ = {"extend_existing": True}

    OrderID = db.Column(db.Integer, db.ForeignKey("Order.OrderID"), primary_key=True)
    ItemID = db.Column(db.Integer, db.ForeignKey("Item.ItemID"), primary_key=True)
    Amount = db.Column(db.Integer, nullable=False)  # not Quantity
    SpecialInstructions = db.Column(db.String(100), nullable=True)

    order = db.relationship("Order", backref="order_items")
    item = db.relationship("Item")


class Status(db.Model):
    __tablename__ = "Status"
    __table_args__ = {"extend_existing": True}

    StatusID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(25))


# This is the base page for index.html template, pulls 3 items to show as popular drinks.
@app.route("/")
def index():
    items = (
        Item.query.filter(Item.IsActive)
        .order_by(
            # Stock may be the best metric to use for popularity. For items with
            # the same stock, order by ItemID to prioritize newer items.
            Item.ItemID.desc()
        )
        .order_by(Item.Stock.desc())
        .limit(3)
        .all()
    )
    return render_template("index.html", featured=items)


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


# This is the shop page and it pulls all items from the DB in order to populate the page on the template.
@app.route("/shop")
def shop():
    items = Item.query.filter(Item.IsActive).all()
    return render_template("shop.html", items=items)


# This is the cart page and uses the session to pull the cart information tied to it on the server side, then pulls all the items information for the cart and calculates the subtotal and total.
@app.route("/cart")
def cart():
    cart = session.get("cart", {})
    entries = []
    total = 0.0
    for itemId, order_descriptor in cart.items():
        item = Item.query.get(itemId)
        if item:
            sub = item.Price * order_descriptor[0]
            total += sub
            entries.append(
                {
                    "item": item,
                    "quantity": order_descriptor[0],
                    "specialInstructions": order_descriptor[1],
                    "subtotal": sub,
                }
            )
    return render_template("cart.html", entries=entries, total=total)


# This is the team page and is a static page.
@app.route("/team")
def team():
    return render_template("team.html")


# This is the contact page and is configured when using GET to just show the page, but then if it's POST, it pulls the information from the page and submits into DB using ORM. Redirects back to contact page when complete.
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        msg = Message(
            SenderName=request.form["name"],
            Email=request.form["email"],
            Phone=request.form["number"],
            Body=request.form["message"],
        )
        db.session.add(msg)
        db.session.commit()
        flash("Message sent!")
        return redirect(url_for("contact"))
    return render_template("contact.html")


# This is a POST command to use when adding one of the items from the Shop page into the cart, used to bring into the session's cart object, creates a Flash message, and then ensures stays on same page.
@app.route("/add-to-cart", methods=["POST"])
def add_to_cart():
    itemId = str(request.form["itemId"])
    quantity = int(request.form["quantity"])
    specialInstructions = request.form.get("specialInstructions", "").strip()

    if len(specialInstructions) == 0:
        specialInstructions = None

    cart = session.get("cart", {})
    cart[itemId] = [cart.get(itemId, [0])[0] + quantity, specialInstructions]
    session["cart"] = cart
    flash("Item added to cart!", category="success")
    return redirect(url_for("shop"))


# This is a POST command to use on the cart page when looking to remove an item from the cart, pulls the cart information for the session and then removes based on the itemId being removed.
@app.route("/remove-from-cart", methods=["POST"])
def remove_from_cart():
    itemId = request.form["itemId"]
    cart = session.get("cart", {})
    if itemId in cart:
        del cart[itemId]
    session["cart"] = cart
    flash("Item removed from cart.")
    return redirect(url_for("cart"))


# Currently just clears the cart, creates a flash message that the payment was submitted, and then redirects to shop.
@app.route("/checkout", methods=["POST"])
def checkout():
    first = request.form["first_name"].strip()
    last = request.form["last_name"].strip()
    email = request.form["email"].strip()
    phone = request.form["phone"].strip()
    address = request.form["address"].strip()
    cardnumber = request.form.get("cardnumber", "").strip()
    expiration = request.form.get("expiration", "").strip()
    cvv = request.form.get("cvv", "").strip()

    if not all([first, last, email, phone, address, cardnumber, expiration, cvv]):
        flash("All fields are required.", category="danger")
        return redirect(url_for("cart"))
    if not re.fullmatch(r"\d{13,19}", cardnumber):
        flash("Invalid card number. Must be 13–19 digits.", category="danger")
        return redirect(url_for("cart"))
    if not re.fullmatch(r"\d{3,4}", cvv):
        flash("Invalid CVV. Must be 3 or 4 digits.", category="danger")
        return redirect(url_for("cart"))
    if not re.fullmatch(r"(0[1-9]|1[0-2])/([0-9]{2})", expiration):
        flash("Expiration must be in MM/YY format.", category="danger")
        return redirect(url_for("cart"))

    cart = session.get("cart", {})
    if not cart:
        flash("Your cart is empty.", category="danger")
        return redirect(url_for("cart"))

    total = 0.0
    for item_id, order_descriptor in cart.items():
        item = Item.query.get(item_id)
        if item:
            total += item.Price * order_descriptor[0]

    # Adding the order
    order = Order(
        CustomerFirstName=first,
        CustomerLastName=last,
        Email=email,
        DateTime=datetime.now(),
        Address=address,
        Phone=phone,
        StatusID=1,
    )
    db.session.add(order)
    # Removed .commit() here since we need all INSERTs to be in the same
    # transaction, so that they either all succeed or all fail.

    # Get order ID
    order = Order.query.order_by(Order.OrderID.desc()).first()
    if not order:
        flash("Failed to create order.", category="danger")
        return redirect(url_for("cart"))

    # Add ordered items
    for item_id, order_descriptor in cart.items():
        db.session.add(
            OrderedItems(
                OrderID=order.OrderID,
                ItemID=item_id,
                Amount=order_descriptor[0],
                SpecialInstructions=order_descriptor[1],
            )
        )

        # Reduce each item's stock by the ordered amount
        item = Item.query.get(item_id)
        if item:
            item.Stock -= order_descriptor[0]
            if item.Stock < 0:
                flash(f"Not enough stock for {item.Name}.", category="danger")
                db.session.rollback()
                return redirect(url_for("cart"))

            db.session.add(item)

    db.session.commit()

    # Compose email body
    body_lines = [
        f"Dear {first} {last},",
        "",
        "Thank you for your purchase! Here is your receipt:",
        "",
        f"Order ID: {order.OrderID}",
        f"Date: {order.DateTime.strftime('%Y-%m-%d %H:%M:%S') if order.DateTime else ''}",
        f"Address: {order.Address}",
        "",
    ]

    total = 0
    for itemId, order_descriptor in session.get("cart", {}).items():
        item = Item.query.get(itemId)
        if item:
            subtotal = item.Price * order_descriptor[0]
            total += subtotal
            body_lines.append(
                f"{item.Name} x{order_descriptor[0]} @ ${item.Price:.2f} = ${subtotal:.2f}"
            )

    body_lines.append("")
    body_lines.append(f"Total: ${total:.2f}")
    body_lines.append("")
    body_lines.append("The IT-Pot Team")

    # Send email
    msg = MailMessage("Your IT-Pot Order Receipt", recipients=[email])
    msg.body = "\n".join(body_lines)
    mail.send(msg)

    session["cart"] = {}
    flash("Order submitted successfully!", category="success")
    return redirect(url_for("shop"))


# Creating the ORM model for user
class User(db.Model):
    __tablename__ = "User"
    __table_args__ = {"extend_existing": True}

    UserID = db.Column(db.Integer, primary_key=True)
    FirstName = db.Column(db.String(30), nullable=False)
    LastName = db.Column(db.String(30), nullable=False)
    Email = db.Column(db.String(50), unique=True, nullable=False)
    Password = db.Column(db.String(30), nullable=False)
    ManagesOrders = db.Column(db.Boolean, default=False, nullable=False)
    ManagesInventory = db.Column(db.Boolean, default=False, nullable=False)
    ManagesMessages = db.Column(db.Boolean, default=False, nullable=False)
    ManagesUsers = db.Column(db.Boolean, default=False, nullable=False)

    @property
    def full_name(self):
        return f"{self.FirstName} {self.LastName}"


@app.route("/admin")
def admin():
    if "user_id" in session:
        return redirect(url_for("admin_dashboard"))

    return redirect(url_for("admin_login"))


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if "user_id" in session:
        return redirect(url_for("admin_dashboard"))

    error = None
    if request.method == "POST":
        user = User.query.filter_by(
            Email=request.form["email"], Password=request.form["password"]
        ).first()
        if user:
            session["user_id"] = user.UserID
            session["can_manage_orders"] = user.ManagesOrders
            session["can_manage_inventory"] = user.ManagesInventory
            session["can_manage_messages"] = user.ManagesMessages
            session["can_manage_users"] = user.ManagesUsers
            return redirect(url_for("admin_dashboard"))
        error = "Invalid credentials."
    return render_template("admin/login.html", error=error)


@app.route("/admin/dashboard", methods=["GET", "POST"])
def admin_dashboard():
    if "user_id" not in session:
        return redirect(url_for("admin_login"))

    raw_items = (
        Item.query.filter(Item.IsActive).order_by(Item.Stock.asc()).limit(5).all()
    )
    raw_series = Series.query.all()
    series_map = {s.SeriesID: s.Name for s in raw_series}
    inventory = []
    for i in raw_items:
        inventory.append(
            {
                "sku": i.ItemID,
                "series": series_map.get(i.SeriesID, "Unknown"),
                "name": i.Name,
                "notCaffeinated": i.IsNoCaffeine,
                "cold": i.IsCold,
                "stock": getattr(i, "Stock", 0),
                "price": i.Price,
            }
        )

    messages = Message.query.order_by(Message.MessageID.asc()).limit(3).all()

    users = User.query.all()

    raw_statuses = Status.query.all()
    status_map = {s.StatusID: s.Name for s in raw_statuses}
    completed_id = max(status_map.keys()) if status_map else 0
    raw_orders = (
        Order.query.where(Order.StatusID != completed_id)
        .order_by(Order.DateTime.desc())
        .limit(5)
        .all()
    )
    orders = [
        {
            "id": o.OrderID,
            "date": o.DateTime.strftime("%Y-%m-%d - %H:%M:%S") if o.DateTime else "",
            "customer_name": f"{o.CustomerFirstName} {o.CustomerLastName}",
            "item_count": sum(i.Amount for i in o.order_items),
            "address": o.Address,
            "status": status_map.get(o.StatusID, "Unknown"),
            "status_class": ("secondary" if o.StatusID == 0 else "warning"),
        }
        for o in raw_orders
    ]
    return render_template(
        "admin/dashboard.html",
        inventory=inventory,
        messages=messages,
        users=users,
        orders=orders,
    )


@app.route("/admin/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("admin_login"))


@app.route("/admin/users", methods=["GET", "POST"])
def users():
    if "user_id" not in session:
        return redirect(url_for("admin_login"))
    if not session.get("can_manage_users"):
        flash("You do not have permission to view this page.", "danger")
        return redirect(url_for("admin_dashboard"))

    edit_id = request.args.get("edit_user", type=int)
    delete_id = request.args.get("delete_user", type=int)

    if delete_id and request.method == "POST":
        u = User.query.get_or_404(delete_id)
        db.session.delete(u)
        db.session.commit()
        return redirect(url_for("users"))

    if request.method == "POST":
        fn = request.form["first_name"]
        ln = request.form["last_name"]
        em = request.form["email"]
        pw = request.form.get("password", "")
        o = bool(request.form.get("manage_orders"))
        i = bool(request.form.get("manage_inventory"))
        m = bool(request.form.get("manage_messages"))
        u = bool(request.form.get("manage_users"))

        if not (o or i or m or u):
            flash("Please select at least one permission.", "danger")
            if edit_id:
                return redirect(url_for("users", edit_user=edit_id))
            else:
                return redirect(url_for("users", new=1))

        dup = User.query.filter_by(Email=em).first()
        if dup and (not edit_id or dup.UserID != edit_id):
            flash("That email is already in use.", "danger")
            if edit_id:
                return redirect(url_for("users", edit_user=edit_id))
            else:
                return redirect(url_for("users", new=1))

        if edit_id:
            user = User.query.get_or_404(edit_id)
            user.FirstName = fn
            user.LastName = ln
            user.Email = em
            if pw:
                user.Password = pw
            user.ManagesOrders = o
            user.ManagesInventory = i
            user.ManagesMessages = m
            user.ManagesUsers = u
        else:
            user = User(
                FirstName=fn,
                LastName=ln,
                Email=em,
                Password=pw,
                ManagesOrders=o,
                ManagesInventory=i,
                ManagesMessages=m,
                ManagesUsers=u,
            )
            db.session.add(user)

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("Could not save user. Please try again.", "danger")
            return redirect(
                url_for("users", edit_user=edit_id)
                if edit_id
                else url_for("users", new=1)
            )

        return redirect(url_for("users"))

    new_user = "new" in request.args
    edit_user = User.query.get(edit_id) if edit_id else None
    users = User.query.order_by(User.UserID).all()
    return render_template(
        "admin/users.html", users=users, edit_user=edit_user, new_user=new_user
    )


@app.route("/admin/messages", methods=["GET", "POST"])
def messages():
    if "user_id" not in session:
        return redirect(url_for("admin_login"))
    if not session.get("can_manage_messages"):
        flash("You do not have permission to view this page.", "danger")
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        msg_id = request.form.get("message_id", type=int)
        msg = Message.query.get_or_404(msg_id)
        db.session.delete(msg)
        db.session.commit()
        flash("Message deleted.", "success")

    messages = Message.query.order_by(Message.MessageID.asc()).all()
    return render_template("admin/messages.html", messages=messages)


@app.route("/admin/inventory")
def inventory():
    if "user_id" not in session:
        return redirect(url_for("admin_login"))

    if not session.get("can_manage_inventory"):
        flash("You do not have permission to view this page.", "danger")
        return redirect(url_for("admin_dashboard"))

    raw_items = (
        Item.query.order_by(Item.ItemID.asc()).order_by(Item.IsActive.desc()).all()
    )
    raw_series = Series.query.all()
    inventory = [
        {
            "sku": i.ItemID,
            "series": next(
                (s.Name for s in raw_series if s.SeriesID == i.SeriesID), "Unknown"
            ),
            "name": f"{'' if i.IsActive else "[DISCONTINUED] "}{i.Name}",
            "notCaffeinated": i.IsNoCaffeine,
            "cold": i.IsCold,
            "stock": getattr(i, "Stock", 0),
            "price": i.Price,
        }
        for i in raw_items
    ]

    return render_template("admin/inventory/all.html", inventory=inventory)


@app.route("/admin/inventory/new", methods=["GET", "POST"])
def new_item():
    if "user_id" not in session:
        return redirect(url_for("admin_login"))

    if not session.get("can_manage_inventory"):
        flash("You do not have permission to view this page.", "danger")
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        item = Item(
            Name=request.form["name"],
            Description=request.form["description"],
            IsNoCaffeine=bool(request.form.get("notCaffeinated")),
            IsCold=bool(request.form.get("cold")),
            Stock=request.form["stock"],
            Price=request.form["price"],
            IsActive=True,
        )

        series_name = request.form.get("series")
        series = Series.query.filter_by(Name=series_name).first()
        if not series:
            series = Series(Name=series_name)
            db.session.add(series)
            series = Series.query.filter_by(Name=series_name).first()

        item.SeriesID = series.SeriesID

        if "image" not in request.files:
            db.session.rollback()
            flash("No file part (for the item image)", "danger")
            return redirect(url_for("new_item"))

        file = request.files["image"]
        if file.filename == "":
            db.session.rollback()
            flash("No selected file (for the item image)", "danger")
            return redirect(url_for("new_item"))

        if file and file.filename.rsplit(".", 1)[1].lower() in ["png", "jpg", "jpeg"]:
            filename = secure_filename(file.filename)
            file_path = os.path.join(item_images_dir, filename)
            file.save(file_path)

            item.ImageURL = filename

            db.session.add(item)
            db.session.commit()

            item_id = Item.query.order_by(Item.ItemID.desc()).first().ItemID
            flash("Item created successfully.", category="success")
            return redirect(url_for("edit_item", item_id=item_id))

        db.session.rollback()
        flash("Invalid file type. Only PNG, JPG, and JPEG are allowed.", "danger")
        return redirect(url_for("new_item"))

    raw_series = Series.query.all()
    series_map = {s.SeriesID: s.Name for s in raw_series}

    return render_template(
        "admin/inventory/new.html",
        series_map=series_map,
    )


@app.route("/admin/inventory/<int:item_id>", methods=["GET", "POST"])
def edit_item(item_id):
    if "user_id" not in session:
        return redirect(url_for("admin_login"))

    if not session.get("can_manage_inventory"):
        flash("You do not have permission to view this page.", "danger")
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        item = Item.query.get_or_404(item_id)
        item.Name = request.form["name"]
        item.Description = request.form["description"]
        item.IsNoCaffeine = bool(request.form.get("notCaffeinated"))
        item.IsCold = bool(request.form.get("cold"))
        item.Stock = request.form["stock"]
        item.Price = request.form["price"]

        series_name = request.form.get("series")
        series = Series.query.filter_by(Name=series_name).first()
        if not series:
            series = Series(Name=series_name)
            db.session.add(series)
            series = Series.query.filter_by(Name=series_name).first()

        item.SeriesID = series.SeriesID

        db.session.add(item)
        db.session.commit()
        flash("Item updated.", category="success")
        return redirect(url_for("edit_item", item_id=item_id))

    item = Item.query.get_or_404(item_id)
    raw_series = Series.query.all()
    series_map = {s.SeriesID: s.Name for s in raw_series}

    return render_template(
        "admin/inventory/edit.html",
        item=item,
        series_map=series_map,
    )


@app.route("/admin/inventory/<int:item_id>/image", methods=["POST"])
def upload_item_image(item_id):
    if "user_id" not in session:
        return redirect(url_for("admin_login"))

    if not session.get("can_manage_inventory"):
        flash("You do not have permission to view this page.", "danger")
        return redirect(url_for("admin_dashboard"))

    if "image" not in request.files:
        flash("No file part", "danger")
        return redirect(url_for("edit_item", item_id=item_id))

    file = request.files["image"]
    if file.filename == "":
        flash("No selected file", "danger")
        return redirect(url_for("edit_item", item_id=item_id))

    if file and file.filename.rsplit(".", 1)[1].lower() in ["png", "jpg", "jpeg"]:
        filename = secure_filename(file.filename)
        file_path = os.path.join(item_images_dir, filename)
        file.save(file_path)

        item = Item.query.get_or_404(item_id)
        item.ImageURL = filename
        db.session.commit()
        flash("Image uploaded successfully.", "success")
    else:
        flash("Invalid file type. Only PNG, JPG, and JPEG are allowed.", "danger")

    return redirect(url_for("edit_item", item_id=item_id))


@app.route("/admin/inventory/<int:item_id>/discontinue", methods=["POST"])
def discontinue_item(item_id):
    if "user_id" not in session:
        return redirect(url_for("admin_login"))

    if not session.get("can_manage_inventory"):
        flash("You do not have permission to view this page.", "danger")
        return redirect(url_for("admin_dashboard"))

    item = Item.query.get_or_404(item_id)
    item.IsActive = False
    db.session.add(item)
    db.session.commit()
    flash("Item discontinued.", category="success")
    return redirect(url_for("edit_item", item_id=item_id))


@app.route("/admin/inventory/<int:item_id>/reactivate", methods=["POST"])
def reactivate_item(item_id):
    if "user_id" not in session:
        return redirect(url_for("admin_login"))

    if not session.get("can_manage_inventory"):
        flash("You do not have permission to view this page.", "danger")
        return redirect(url_for("admin_dashboard"))

    item = Item.query.get_or_404(item_id)
    item.IsActive = True
    db.session.add(item)
    db.session.commit()
    flash("Item reactivated.", category="success")
    return redirect(url_for("edit_item", item_id=item_id))


@app.route("/admin/orders")
def orders():
    if "user_id" not in session:
        return redirect(url_for("admin_login"))

    if not session.get("can_manage_orders"):
        flash("You do not have permission to view this page.", "danger")
        return redirect(url_for("admin_dashboard"))

    statuses = Status.query.all()
    completed_id = max(s.StatusID for s in statuses) if statuses else 0
    raw_orders = Order.query.order_by(Order.DateTime.desc()).all()

    orders = [
        {
            "id": o.OrderID,
            "date": o.DateTime.strftime("%Y-%m-%d - %H:%M:%S") if o.DateTime else "",
            "customer_name": f"{o.CustomerFirstName} {o.CustomerLastName}",
            "item_count": sum(i.Amount for i in o.order_items),
            "address": o.Address,
            "status": next(
                (s.Name for s in statuses if s.StatusID == o.StatusID), "Unknown"
            ),
            "status_class": (
                "success"
                if o.StatusID == completed_id
                else "secondary" if o.StatusID == 0 else "warning"
            ),
        }
        for o in raw_orders
    ]

    return render_template("admin/orders/all.html", orders=orders)


@app.route("/admin/orders/<int:order_id>", methods=["GET", "POST"])
def edit_order(order_id):
    if "user_id" not in session:
        return redirect(url_for("admin_login"))

    if not session.get("can_manage_orders"):
        flash("You do not have permission to view this page.", "danger")
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        order = Order.query.get_or_404(order_id)

        status_name = request.form.get("status", type=int)
        order.StatusID = Status.query.filter_by(StatusID=status_name).first().StatusID

        db.session.commit()
        flash("Order status updated.", category="success")
        return redirect(url_for("edit_order", order_id=order_id))

    raw_statuses = Status.query.all()
    raw_order = Order.query.get_or_404(order_id)
    raw_ordered_items = (
        OrderedItems.query.filter_by(OrderID=order_id)
        .join(Item, OrderedItems.ItemID == Item.ItemID)
        .add_columns(
            OrderedItems.ItemID,
            OrderedItems.Amount,
            OrderedItems.SpecialInstructions,
            Item.ImageURL,
            Item.Name,
            Item.IsActive,
        )
        .all()
    )

    order = {
        "id": raw_order.OrderID,
        "date": (
            raw_order.DateTime.strftime("%Y-%m-%d - %H:%M:%S")
            if raw_order.DateTime
            else ""
        ),
        "customer_name": f"{raw_order.CustomerFirstName} {raw_order.CustomerLastName}",
        "address": raw_order.Address,
        "phone": raw_order.Phone,
        "email": raw_order.Email,
        "status": next(
            (s for s in raw_statuses if s.StatusID == raw_order.StatusID),
            "Unknown",
        ),
        "status_class": (
            "success"
            if raw_order.StatusID == max(s.StatusID for s in raw_statuses)
            else "secondary" if raw_order.StatusID == 0 else "warning"
        ),
        "itemsList": [
            {
                "id": ordered_item.ItemID,
                "imageURL": ordered_item.ImageURL,
                "name": ordered_item.Name,
                "amount": ordered_item.Amount,
                "specialInstructions": ordered_item.SpecialInstructions,
                "isActive": ordered_item.IsActive,
            }
            for ordered_item in raw_ordered_items
        ],
    }

    return render_template(
        "admin/orders/edit.html",
        order=order,
        statuses=raw_statuses,
        completed_id=max(s.StatusID for s in raw_statuses) if raw_statuses else 0,
    )


@app.route("/admin/orders/<int:order_id>/next-status")
def next_status(order_id):
    if "user_id" not in session:
        return redirect(url_for("admin_login"))

    if not session.get("can_manage_orders"):
        flash("You do not have permission to view this page.", "danger")
        return redirect(url_for("admin_dashboard"))

    order = Order.query.get_or_404(order_id)
    order.StatusID += 1
    db.session.commit()
    flash("Order status updated.", category="success")
    return redirect(url_for("edit_order", order_id=order_id))


@app.route("/admin/orders/<int:order_id>/cancel")
def cancel_order(order_id):
    if "user_id" not in session:
        return redirect(url_for("admin_login"))

    if not session.get("can_manage_orders"):
        flash("You do not have permission to view this page.", "danger")
        return redirect(url_for("admin_dashboard"))

    order = Order.query.get_or_404(order_id)
    order.StatusID = 0
    db.session.commit()
    flash("Order cancelled.", category="success")
    return redirect(url_for("edit_order", order_id=order_id))


@app.route("/sw.js")
def serve_sw():
    return send_from_directory(
        app.static_folder, "sw.js", mimetype="application/javascript"
    )


@app.route("/api/items", methods=["GET"])
def get_public_items():
    items = Item.query.with_entities(Item.Name, Item.Price).all()
    result = [{"name": item.Name, "price": float(item.Price)} for item in items]
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
