from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'expense-only-secret-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

CATEGORIES = [
    ('housing',       'السكن والإيجار',      '🏠'),
    ('food',          'الطعام والمطاعم',     '🍔'),
    ('groceries',     'البقالة والمشتريات',  '🛒'),
    ('coffee',        'القهوة والمشروبات',   '☕'),
    ('petrol',        'البترول والوقود',     '⛽'),
    ('carwash',       'غسيل السيارة',        '🚿'),
    ('carmaint',      'صيانة السيارة',       '🔧'),
    ('health',        'الصحة والطب',         '💊'),
    ('pharmacy',      'الصيدلية',            '💉'),
    ('education',     'التعليم',             '📚'),
    ('entertainment', 'الترفيه والأنشطة',    '🎬'),
    ('clothing',      'الملابس والأحذية',    '👔'),
    ('utilities',     'الفواتير والخدمات',   '💡'),
    ('internet',      'الإنترنت والهاتف',    '📱'),
    ('subscriptions', 'الاشتراكات',          '📺'),
    ('savings',       'الادخار',             '💰'),
    ('gifts',         'الهدايا',             '🎁'),
    ('travel',        'السفر والترحال',      '✈️'),
    ('other',         'أخرى',               '📦'),
]


class User(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False, unique=True)
    pin_hash   = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expenses   = db.relationship('Expense', backref='user', lazy=True, cascade='all, delete-orphan')


class Expense(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount      = db.Column(db.Float, nullable=False)
    category    = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    date        = db.Column(db.Date, default=date.today)
    month       = db.Column(db.Integer)
    year        = db.Column(db.Integer)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.date:
            self.month = self.date.month
            self.year  = self.date.year


with app.app_context():
    db.create_all()


def get_cat(key):
    for c in CATEGORIES:
        if c[0] == key:
            return c
    return (key, key, '📦')


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# ── AUTH ──────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name'].strip()
        pin  = request.form['pin'].strip()
        user = User.query.filter_by(name=name).first()
        if user and check_password_hash(user.pin_hash, pin):
            session['user_id']   = user.id
            session['user_name'] = user.name
            return redirect(url_for('index'))
        flash('الاسم أو الرمز غير صحيح ❌', 'error')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        pin  = request.form['pin'].strip()
        if len(pin) != 4 or not pin.isdigit():
            flash('الرمز يجب أن يكون 4 أرقام ❌', 'error')
            return render_template('register.html')
        if User.query.filter_by(name=name).first():
            flash('هذا الاسم مستخدم بالفعل ❌', 'error')
            return render_template('register.html')
        user = User(name=name, pin_hash=generate_password_hash(pin))
        db.session.add(user)
        db.session.commit()
        session['user_id']   = user.id
        session['user_name'] = user.name
        flash(f'مرحباً {name}! تم إنشاء حسابك 🎉', 'success')
        return redirect(url_for('index'))
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ── MAIN ──────────────────────────────────────────
@app.route('/')
@login_required
def index():
    user_id = session['user_id']
    today   = date.today()
    month   = request.args.get('month', today.month, type=int)
    year    = request.args.get('year',  today.year,  type=int)

    expenses = Expense.query.filter_by(user_id=user_id, month=month, year=year).all()
    total    = sum(e.amount for e in expenses)

    by_cat = {}
    for e in expenses:
        by_cat[e.category] = by_cat.get(e.category, 0) + e.amount

    arabic_months = {
        1:'يناير',2:'فبراير',3:'مارس',4:'أبريل',
        5:'مايو',6:'يونيو',7:'يوليو',8:'أغسطس',
        9:'سبتمبر',10:'أكتوبر',11:'نوفمبر',12:'ديسمبر'
    }
    years_list = list(range(today.year - 2, today.year + 2))

    return render_template('index.html',
        expenses=expenses,
        total=total,
        by_cat=by_cat,
        categories=CATEGORIES,
        current_month=month,
        current_year=year,
        years_list=years_list,
        arabic_months=arabic_months,
        get_cat=get_cat,
        user_name=session.get('user_name'),
    )


@app.route('/add_expense', methods=['POST'])
@login_required
def add_expense():
    amount      = float(request.form['amount'])
    category    = request.form['category']
    description = request.form.get('description', '')
    entry_date  = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
    e = Expense(user_id=session['user_id'], amount=amount,
                category=category, description=description, date=entry_date)
    db.session.add(e)
    db.session.commit()
    flash('تمت إضافة المصروف ✅', 'success')
    return redirect(url_for('index', month=entry_date.month, year=entry_date.year))


@app.route('/delete_expense/<int:id>')
@login_required
def delete_expense(id):
    e = Expense.query.filter_by(id=id, user_id=session['user_id']).first_or_404()
    month, year = e.month, e.year
    db.session.delete(e)
    db.session.commit()
    flash('تم الحذف ✅', 'info')
    return redirect(url_for('index', month=month, year=year))


@app.route('/api/chart')
@login_required
def chart():
    user_id = session['user_id']
    today   = date.today()
    mode    = request.args.get('mode', 'monthly')   # monthly | daily
    year    = request.args.get('year',  today.year,  type=int)
    month   = request.args.get('month', today.month, type=int)

    if mode == 'daily':
        import calendar
        days_in_month = calendar.monthrange(year, month)[1]
        labels = [str(d) for d in range(1, days_in_month + 1)]
        data = []
        for d in range(1, days_in_month + 1):
            try:
                day_date = date(year, month, d)
            except ValueError:
                data.append(0)
                continue
            total = db.session.query(db.func.sum(Expense.amount))\
                      .filter(Expense.user_id == user_id, Expense.date == day_date).scalar() or 0
            data.append(round(total, 3))
    else:
        labels = ['يناير','فبراير','مارس','أبريل','مايو','يونيو',
                  'يوليو','أغسطس','سبتمبر','أكتوبر','نوفمبر','ديسمبر']
        data = []
        for m in range(1, 13):
            total = db.session.query(db.func.sum(Expense.amount))\
                      .filter_by(user_id=user_id, month=m, year=year).scalar() or 0
            data.append(round(total, 3))

    return jsonify({'labels': labels, 'data': data, 'mode': mode})


@app.route('/scan_receipt', methods=['POST'])
@login_required
def scan_receipt():
    import requests as http_requests
    from PIL import Image
    import io, json, re, base64

    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return jsonify({'error': 'مفتاح Gemini غير موجود'}), 500

    if 'image' not in request.files:
        return jsonify({'error': 'لم يتم إرسال صورة'}), 400

    file = request.files['image']
    img_bytes = file.read()

    try:
        # Handle HEIC if pillow-heif available
        try:
            import pillow_heif
            pillow_heif.register_heif_opener()
        except ImportError:
            pass

        img = Image.open(io.BytesIO(img_bytes))
        if img.mode != 'RGB':
            img = img.convert('RGB')

        max_size = 1600
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            img = img.resize((int(img.size[0]*ratio), int(img.size[1]*ratio)), Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=85)
        jpeg_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

        prompt = (
            "You are a receipt reader. Look at this receipt image carefully.\n"
            "Reply with ONLY a raw JSON object, no markdown, no explanation:\n"
            '{"amount": <total amount as number>, '
            '"description": "<store name or description in Arabic>", '
            '"category": "<one of: food, groceries, coffee, petrol, carwash, carmaint, health, pharmacy, education, entertainment, clothing, utilities, internet, subscriptions, savings, gifts, travel, housing, other>", '
            '"date": "<date as YYYY-MM-DD or empty string>"}\n\n'
            "Category rules: coffee shop/cafe→coffee, gas station/fuel→petrol, restaurant→food, "
            "supermarket/grocery→groceries, pharmacy→pharmacy, hospital/clinic→health, "
            "clothes/shoes→clothing, electricity/water bill→utilities, carwash→carwash, "
            "car repair/parts→carmaint, otherwise→other. "
            "If amount unclear use 0. Write description in Arabic."
        )

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/jpeg", "data": jpeg_b64}}
                ]
            }]
        }

        # Support both AIza... and AQ... key formats
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        }
        resp = http_requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        text = result['candidates'][0]['content']['parts'][0]['text'].strip()

        # Remove markdown code blocks if present
        text = re.sub(r'```(?:json)?', '', text).strip()

        # Extract JSON
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            data = json.loads(text)

        # Ensure amount is a number
        try:
            data['amount'] = float(str(data.get('amount', 0)).replace(',', '.'))
        except Exception:
            data['amount'] = 0

        return jsonify({'success': True, 'data': data})

    except Exception as e:
        return jsonify({'error': str(e), 'detail': 'scan_failed'}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5051))
    app.run(host='0.0.0.0', debug=True, port=port)
