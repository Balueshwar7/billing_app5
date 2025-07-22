from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_file
from db import (
    get_menu_items,
    add_menu_item_to_db,
    save_bill_to_db,
    delete_menu_item_from_db,
    get_all_bills
)

from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import mm

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # required for session management

# 🔐 Admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password123'

# -------------------- Web Pages --------------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/admin/login", methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            return render_template('admin_login.html', error="Invalid credentials")
    return render_template('admin_login.html')

@app.route("/admin/logout")
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route("/admin")
def admin_panel():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    menu_items = get_menu_items()
    bills = get_all_bills()
    return render_template("admin_panel.html", menu=menu_items, bills=bills)

@app.route("/admin/add-item", methods=['POST'])
def admin_add_item():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    name = request.form['name']
    price = request.form['price']
    if name and price:
        add_menu_item_to_db(name, float(price))
    return redirect(url_for('admin_panel'))

@app.route("/admin/delete-item", methods=['POST'])
def admin_delete_item():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    name = request.form['name']
    delete_menu_item_from_db(name)
    return redirect(url_for('admin_panel'))

# -------------------- API Endpoints --------------------

@app.route("/api/menu", methods=["GET"])
def get_menu():
    try:
        return jsonify(get_menu_items())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/menu", methods=["POST"])
def add_menu_item():
    data = request.json
    name = data.get("name")
    price = data.get("price")
    if not name or not price:
        return jsonify({"error": "Name and price are required"}), 400
    try:
        add_menu_item_to_db(name, float(price))
        return jsonify({"message": "Item added successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/bill", methods=["POST"])
def save_bill():
    data = request.json
    bill_items = data.get("items", [])
    total = data.get("total", 0)
    if not bill_items:
        return jsonify({"error": "No items in bill"}), 400
    try:
        save_bill_to_db(bill_items, total)
        return jsonify({"message": "Bill saved successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------- 🧾 Print PDF (Thermal Format) --------------------

@app.route("/print-pdf", methods=["POST"])
def print_pdf():
    data = request.json
    items = data.get("items", [])
    total = data.get("total", 0)

    if not items:
        return jsonify({"error": "No bill items provided"}), 400

    buffer = BytesIO()

    # 58mm wide paper (width = 58mm, height = arbitrary long page, e.g., 200mm)
    thermal_width = 58 * mm
    thermal_height = 200 * mm
    c = canvas.Canvas(buffer, pagesize=(thermal_width, thermal_height))

    x = 5 * mm
    y = thermal_height - 10 * mm
    line_height = 6 * mm

    def draw(text, size=10, offset=0):
        nonlocal y
        c.setFont("Courier", size)
        c.drawString(x + offset, y, text)
        y -= line_height

    # Header
    draw("* FOOD TRUCK BILL *", 10)
    draw("Near Main Road, City", 8)
    draw("Mob: 9876543210", 8)
    draw("-" * 32)

    # Metadata
    from datetime import datetime
    now = datetime.now()
    draw(f"Date: {now.strftime('%d/%m/%Y')}   Time: {now.strftime('%H:%M:%S')}", 8)
    draw("-" * 32)
    draw("Item            Qty   Amt", 8)
    draw("-" * 32)

    total_qty = 0
    for item in items:
        name = item["name"][:13].ljust(13)
        qty = str(item.get("qty", 1)).rjust(3)
        amt = str(int(item["price"] * item.get("qty", 1))).rjust(6)
        draw(f"{name} {qty} {amt}", 8)
        total_qty += item.get("qty", 1)

    draw("-" * 32)
    draw(f"Total Qty: {total_qty}    Rs. {total:.2f}", 8)
    draw("-" * 32)
    draw("Thank you! Visit Again 🙏", 8)

    c.showPage()
    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=False,
        download_name='bill.pdf'
    )

# -------------------- App Run --------------------

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
