from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import random
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "campuseats-hackathon-secret-key"  # change this in production

DB_NAME = "canteen.db"
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    cursor.execute('''
        INSERT OR IGNORE INTO settings (key, value) 
        VALUES ('kitchen_load', 'Normal')
    ''')
    conn.commit()
    conn.close()

init_db()
HOSTEL_BLOCKS = ["A Block", "B Block", "C Block", "D Block", "PG Block"]

# All possible pickup slots, ordered from soonest to farthest out.
ALL_TIME_SLOTS = [
    "10:00 AM - 10:15 AM",
    "10:15 AM - 10:30 AM",
    "12:00 PM - 12:15 PM",
    "12:15 PM - 12:30 PM",
    "12:30 PM - 12:45 PM",
    "01:00 PM - 01:15 PM",
]

# Kitchen load set by staff: how many of the *soonest* slots get hidden from
# students. Busier kitchen -> nearest slots disappear -> everyone gets pushed
# further out so the kitchen isn't promising pickup times it can't hit.
KITCHEN_LOAD_LEVELS = {
    "Green": {"label": "Normal", "hide_nearest": 0},
    "Yellow": {"label": "Busy", "hide_nearest": 2},
    "Red": {"label": "Very Busy", "hide_nearest": 4},
}

# Expanded menu with categories so the grid has enough items to scroll,
# and a filter bar actually has something to filter.
DEFAULT_ITEMS = [
    # (name, price, image_url, category, veg)
    ("Masala Dosa", 60.0, "https://static.toiimg.com/thumb/54289752.cms?imgsize=495844&width=800&height=800", "Breakfast", 1),
    ("Idli Sambar", 35.0, "https://vaya.in/recipes/wp-content/uploads/2018/02/Idli-and-Sambar-1.jpg", "Breakfast", 1),
    ("Poha", 30.0, "https://images.pexels.com/photos/13063292/pexels-photo-13063292.jpeg?auto=compress&cs=tinysrgb&w=400", "Breakfast", 1),
    ("Veg Sandwich", 40.0, "https://images.unsplash.com/photo-1592415499556-74fcb9f18667?q=80&w=400&auto=format&fit=crop", "Snacks", 1),
    ("Samosa (2 pcs)", 25.0, "https://images.unsplash.com/photo-1601050690597-df0568f70950?q=80&w=400&auto=format&fit=crop", "Snacks", 1),
    ("Paneer Wrap", 70.0, "https://images.unsplash.com/photo-1626700051175-6818013e1d4f?q=80&w=400&auto=format&fit=crop", "Snacks", 1),
    ("French Fries", 50.0, "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?q=80&w=400&auto=format&fit=crop", "Snacks", 1),
    ("Veg Cutlet", 35.0, "https://www.cookwithmanali.com/wp-content/uploads/2021/04/Veg-Cutlet-500x500.jpg", "Snacks", 1),
    ("Chicken Burger", 80.0, "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?q=80&w=400&auto=format&fit=crop", "Meals", 0),
    ("Veg Biryani", 90.0, "https://www.cookingcarnival.com/wp-content/uploads/2025/09/Vegetable-Dum-Biryani-5-500x500.jpg", "Meals", 1),
    ("Chole Bhature", 65.0, "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ-1_d0RDorLVeTEgDNTJnB-5BPkjSlvemo-SAfIgMfmfWxVGO-VSymL2H5&s=10", "Meals", 1),
    ("Cold Coffee", 30.0, "https://mytastycurry.com/wp-content/uploads/2020/04/Cafe-style-cold-coffee-with-icecream.jpg", "Beverages", 1),
    ("Masala Chai", 15.0, "https://www.livingchirpy.com/wp-content/uploads/2025/07/masalachairecipe.01.jpg", "Beverages", 1),
    ("Fresh Lime Soda", 25.0, "https://sattvakitchen.com/wp-content/uploads/2024/05/SWEET-LIME-SODA-shutterstock_2309599743-copy-Copy-copy.jpg", "Beverages", 1),
    ("Gulab Jamun", 30.0, "https://upload.wikimedia.org/wikipedia/commons/c/c1/Gulab-jamun-wallpaper-1.jpg?utm_source=en.wikipedia.org&utm_campaign=index&utm_content=original", "Dessert", 1),
    ("Chocolate Brownie", 50.0, "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?q=80&w=400&auto=format&fit=crop", "Dessert", 1),
]


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            image_url TEXT,
            category TEXT DEFAULT 'Snacks',
            veg INTEGER DEFAULT 1,
            available INTEGER DEFAULT 1
        )
    ''')

    # Orders now only hold order-level info. Line items live in order_items,
    # which is what lets a single order contain several different dishes.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            hostel_block TEXT NOT NULL,
            time_slot TEXT NOT NULL,
            status TEXT DEFAULT 'Placed',
            est_time INTEGER DEFAULT 10,
            orders_ahead INTEGER DEFAULT 3,
            created_at TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (id)
        )
    ''')

    # Simple shared key/value store -- used for the staff-controlled kitchen
    # load sensor, so every student sees the same live value (this can't live
    # in a Flask session since that's per-browser, not shared).
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('kitchen_load', 'Green')")

    cursor.execute('SELECT COUNT(*) FROM menu_items')
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            'INSERT INTO menu_items (name, price, image_url, category, veg, available) VALUES (?, ?, ?, ?, ?, 1)',
            DEFAULT_ITEMS
        )

    conn.commit()
    conn.close()


def get_kitchen_load():
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key = 'kitchen_load'").fetchone()
    conn.close()
    load = row['value'] if row else 'Green'
    return load if load in KITCHEN_LOAD_LEVELS else 'Green'


def get_available_slots(load):
    hide = KITCHEN_LOAD_LEVELS[load]['hide_nearest']
    remaining = ALL_TIME_SLOTS[hide:]
    # Always leave at least the last 2 slots so ordering is never fully blocked.
    return remaining if remaining else ALL_TIME_SLOTS[-2:]


def ensure_profile():
    """First visit gets a default name + random block; after that it only
    changes if the student explicitly edits it via the profile modal."""
    if 'student_name' not in session:
        session['student_name'] = "Alex Smith"
    if 'hostel_block' not in session:
        session['hostel_block'] = random.choice(HOSTEL_BLOCKS)


@app.route('/')
def student_view():
    ensure_profile()
    conn = get_db()
    items = conn.execute(
        'SELECT name, price, image_url, category, veg, available FROM menu_items WHERE available = 1'
    ).fetchall()
    conn.close()

    kitchen_load = get_kitchen_load()
    time_slots = get_available_slots(kitchen_load)
    categories = sorted({item['category'] for item in items})

    profile = {"name": session['student_name'], "hostel": session['hostel_block']}

    return render_template(
        'index.html',
        items=items,
        categories=categories,
        time_slots=time_slots,
        profile=profile,
        hostel_blocks=HOSTEL_BLOCKS,
        items_json=json.dumps({i['name']: i['price'] for i in items}),
        kitchen_load=kitchen_load,
        kitchen_load_label=KITCHEN_LOAD_LEVELS[kitchen_load]['label'],
    )


@app.route('/profile', methods=['POST'])
def update_profile():
    name = request.form.get('student_name', '').strip()
    block = request.form.get('hostel_block', '').strip()
    if name:
        session['student_name'] = name
    if block in HOSTEL_BLOCKS:
        session['hostel_block'] = block
    return redirect(url_for('student_view'))


@app.route('/order', methods=['POST'])
def place_order():
    ensure_profile()
    time_slot = request.form.get('time_slot')
    cart_raw = request.form.get('cart_json', '{}')

    try:
        cart = json.loads(cart_raw)
    except json.JSONDecodeError:
        cart = {}

    if not cart or not time_slot:
        return redirect(url_for('student_view'))

    conn = get_db()
    cursor = conn.cursor()

    est_time = random.randint(8, 20)
    orders_ahead = random.randint(1, 6)

    cursor.execute(
        'INSERT INTO orders (student_name, hostel_block, time_slot, est_time, orders_ahead, created_at) '
        'VALUES (?, ?, ?, ?, ?, ?)',
        (session['student_name'], session['hostel_block'], time_slot, est_time, orders_ahead,
         datetime.now().strftime('%I:%M %p'))
    )
    order_id = cursor.lastrowid

    for item_name, details in cart.items():
        qty = int(details.get('qty', 1))
        price = float(details.get('price', 0))
        if qty > 0:
            cursor.execute(
                'INSERT INTO order_items (order_id, item_name, quantity, price) VALUES (?, ?, ?, ?)',
                (order_id, item_name, qty, price)
            )

    conn.commit()
    conn.close()

    return redirect(url_for('track_order', order_id=order_id))


@app.route('/track/<int:order_id>')
def track_order(order_id):
    conn = get_db()
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    line_items = conn.execute(
        'SELECT item_name, quantity, price FROM order_items WHERE order_id = ?', (order_id,)
    ).fetchall()
    conn.close()

    if order is None:
        return redirect(url_for('student_view'))

    total = sum(li['price'] * li['quantity'] for li in line_items)
    return render_template('track.html', order=order, line_items=line_items, total=total)


@app.route('/api/order_status/<int:order_id>')
def order_status(order_id):
    """Lightweight JSON endpoint the tracking page polls so the status
    and progress bar can update without a full page reload."""
    conn = get_db()
    order = conn.execute('SELECT status, est_time, orders_ahead FROM orders WHERE id = ?', (order_id,)).fetchone()
    conn.close()
    if order is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(dict(order))


@app.route('/staff')
def staff_view():
    conn = get_db()
    orders = conn.execute('SELECT * FROM orders ORDER BY id DESC').fetchall()

    orders_with_items = []
    for order in orders:
        items = conn.execute(
            'SELECT item_name, quantity FROM order_items WHERE order_id = ?', (order['id'],)
        ).fetchall()
        order_dict = dict(order)
        order_dict['line_items'] = items  # not "items" -- that name collides with dict.items()
        orders_with_items.append(order_dict)

    prep_count = conn.execute("SELECT COUNT(*) FROM orders WHERE status = 'Preparing'").fetchone()[0]
    ready_count = conn.execute("SELECT COUNT(*) FROM orders WHERE status = 'Ready for Pickup'").fetchone()[0]
    comp_count = conn.execute("SELECT COUNT(*) FROM orders WHERE status = 'Completed'").fetchone()[0]

    conn.close()
    return render_template(
        'staff.html',
        orders=orders_with_items,
        total=len(orders_with_items),
        prep=prep_count,
        ready=ready_count,
        comp=comp_count,
        kitchen_load=get_kitchen_load(),
        load_levels=KITCHEN_LOAD_LEVELS,
    )


@app.route('/update_status/<int:order_id>', methods=['POST'])
def update_status(order_id):
    new_status = request.form['status']
    conn = get_db()
    conn.execute('UPDATE orders SET status = ? WHERE id = ?', (new_status, order_id))
    conn.commit()
    conn.close()
    return redirect(url_for('staff_view'))


@app.route('/staff/set_load', methods=['POST'])
def set_kitchen_load():
    load = request.form.get('load')
    if load in KITCHEN_LOAD_LEVELS:
        conn = get_db()
        conn.execute("UPDATE settings SET value = ? WHERE key = 'kitchen_load'", (load,))
        conn.commit()
        conn.close()
    return redirect(url_for('staff_view'))


@app.route('/api/kitchen_load')
def api_kitchen_load():
    """Lets the student page poll for load changes without a full reload."""
    load = get_kitchen_load()
    return jsonify({
        "load": load,
        "label": KITCHEN_LOAD_LEVELS[load]['label'],
        "slots": get_available_slots(load),
    })


if __name__ == '__main__':
    init_db()
    app.run(debug=True)