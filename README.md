# StockRiskTracker

StockRiskTracker is a comprehensive Django-based web application designed to help users track stock investments, evaluate their investment risk tolerance, manage a virtual wallet, and maintain a personal investment journal.

---

## 🚀 Features

### 👤 User Authentication & Profiles
- **Secure Registration & Login**: Traditional login/signup flow.
- **OTP Verification**: Multi-factor security check during registration.
- **Guest Access**: Explore the application layout without registering.
- **Profile Customization**: Update user information and manage account settings.

### 📊 Portfolio & Stock Tracking
- **Interactive Dashboard**: Overview of current assets, risk distribution, and wallet status.
- **Virtual Wallet**: Trade stocks using a simulated starting balance of ₹10,000.00.
- **Stock Transactions**: Buy and sell stocks dynamically with real-time wallet adjustments and detailed history logs.
- **Interactive Watchlist**: Save preferred tickers and access portfolio optimization suggestions.

### 📝 Investment Tools
- **Investment Diary**: Log thoughts, track market observations, and manage notes (Create, Read, Update, Delete).
- **Financial Dictionary**: Look up complex trading and financial terms on demand.
- **Risk Tolerance Quiz**: A personalized assessment determining whether you are a **Safe**, **Neutral**, or **Risky** investor, adjusting your profile parameters accordingly.

### 🛡️ Admin Dashboard
- **User Management**: View, edit, or delete registered users.
- **Quiz Configuration**: Add, update, or remove risk assessment questions.
- **Dictionary Management**: Expand the financial dictionary with new terms and meanings.

---

## 🛠️ Tech Stack
- **Backend**: Django 4+ (Python)
- **Database**: SQLite3 (default, easily configurable to PostgreSQL/MySQL)
- **Frontend**: Responsive HTML5, Custom Vanilla CSS, JavaScript
- **Security**: OTP Authentication, Session-based auth

---

## ⚙️ Installation & Setup

### Prerequisites
Make sure you have Python 3.8+ installed on your system.

### 1. Clone the Repository
```bash
git clone https://github.com/Tanish428/StockRiskTracker.git
```

### 2. Set Up a Virtual Environment
```bash
# Navigate to the Django project root folder
cd stock_risk_manager

# Activate virtual environment
# On Windows (Command Prompt)
.venv\Scripts\activate
# On Windows (PowerShell)
.\venv\Scripts\Activate.ps1
# On macOS/Linux
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Apply Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create a Superuser (Admin Access)
```bash
python manage.py createsuperuser
```

### 6. Run the Development Server
```bash
python manage.py runserver
```
Visit the local server in your browser at `http://127.0.0.1:8000/`.

---

## 📂 Project Structure
```text
stock_risk_manager/
│
├── manage.py                # Django CLI utility
├── db.sqlite3               # Database
│
├── mysite/                  # Django configuration directory
│   ├── __init__.py
│   ├── settings.py          # App settings
│   ├── urls.py              # Main URL routing
│   └── wsgi.py / asgi.py
│
└── tracker/                 # Core application directory
    ├── migrations/          # DB Migrations
    ├── static/              # CSS, JS, and image assets
    ├── templates/           # HTML Templates
    ├── models.py            # Database schemas (Profile, Transaction, Watchlist, DiaryNote, Dictionary, QuizQuestion)
    ├── views/               # Controllers / Views logic
    ├── urls.py              # App-specific URL routing
    └── forms.py             # User inputs forms (Profile, Diary, Auth)
```

---

## 🤝 Contributing
Contributions are welcome! If you'd like to improve the risk algorithm, add new charts, or optimize the backend:
1. Fork the Project.
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the Branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.
