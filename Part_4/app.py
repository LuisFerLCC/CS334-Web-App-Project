from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/shop')
def shop():
    return "Shop Page Coming Soon!"

@app.route('/team')
def team():
    return "Team Page Coming Soon!"

@app.route('/contact')
def contact():
    return "Contact Page Coming Soon!"

@app.route('/cart')
def cart():
    return "Cart Page Coming Soon!"

@app.route('/admin/login')
def admin_login():
    return "Admin Login Page Coming Soon!"

if __name__ == "__main__":
    app.run(debug=True)