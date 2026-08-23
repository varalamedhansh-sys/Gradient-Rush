# CampusEats 🍔 — Skip the Queue, Grab Your Food

CampusEats is a campus canteen queue minimizer. Students pre-order food from their rooms and track it in real time, while kitchen staff manage the order flow from a live dashboard — cutting down the long rush-hour queues at the canteen.

Built for Gradient Rush as a campus-betterment project.

---

## 🚩 The Problem

During rush hours, canteens turn into 15–20 minute queues just to grab a quick snack between classes. Students waste time standing in line, and staff have no way to smooth out demand across the day.

## ✅ The Solution

- Students order ahead from their phone/laptop and pick a pickup slot.
- Orders can contain **multiple different items** in a single cart.
- Live order tracking with a status stepper (Placed → Preparing → Ready → Completed).
- Kitchen staff get a dashboard to manage incoming orders and update their status.
- A **kitchen load sensor** (🟢 Green / 🟡 Yellow / 🔴 Red) lets staff signal how busy the kitchen is — which automatically hides the nearest pickup slots from students so no one is promised a slot the kitchen can't hit.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🛒 Multi-item cart | Add as many different dishes as you want to one order, with live quantity controls |
| 🧑‍🎓 Editable profile | Student name & hostel block, editable anytime via a profile modal |
| 🍽️ Menu with categories | Filterable by Breakfast / Snacks / Meals / Beverages / Dessert, scrollable grid |
| 📦 Real-time order tracking | Progress stepper + ETA that auto-updates via polling, no manual refresh |
| 🧑‍🍳 Staff dashboard | Kanban-style board (Preparing / Ready / Completed) with order details |
| 🚦 Kitchen load sensor | Staff-controlled Green/Yellow/Red status that dynamically reduces available pickup slots |
| 🎨 Custom UI | Food-themed background, card-based menu, sticky cart sidebar |

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask
- **Database:** SQLite
- **Frontend:** HTML, CSS, vanilla JavaScript (Jinja2 templating)

---

## 📂 Project Structure

```
canteen_app/
├── app.py                  # Flask app: routes, DB logic, kitchen load logic
├── database.sql            # Reference schema (for manual inspection)
├── static/
│   └── style.css           # All styling — hero, menu grid, cart, dashboard
└── templates/
    ├── index.html           # Student ordering page
    ├── track.html           # Live order tracking page
    ├── staff.html           # Kitchen staff dashboard
    └── order_card.html      # Reusable order card partial (used in staff.html)
```

> `canteen.db` is auto-generated the first time you run the app — don't commit it, and delete it if you change the schema.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip

### Installation

```bash
# Clone the repo
git clone https://github.com/<your-username>/campuseats.git
cd campuseats/canteen_app

# Install dependencies
pip install flask

# Run the app
python app.py
```

The app will be available at **http://127.0.0.1:5000**

- Student ordering page: `https://gradient-rush.onrender.com/`
- Kitchen staff dashboard: `https://gradient-rush.onrender.com/staff`

### Resetting the database
If you pull schema changes or the app throws a DB error, delete `canteen.db` and restart — it's recreated automatically with fresh sample menu data.

---

## 🔮 Future Improvements

- Real student login/authentication (currently session-based, single device)
- Payment gateway integration
- Admin panel to add/edit/remove menu items from the UI
- Push notifications when an order is ready
- Analytics dashboard for canteen staff (peak hours, popular items)

---

## 👥 Team

Sprinters

---

## 📄 License

This project was built for a hackathon and is open for educational use. Add a license of your choice (MIT recommended) if you plan to keep developing it.
