"""
سكريبت لنقل البيانات من SQLite القديم إلى PostgreSQL
شغّله بعد إنشاء حسابك في التطبيق
"""
import os, sqlite3, sys
from app import app, db, User, Expense
from datetime import datetime

SQLITE_PATH = '/Users/mac/expense_tracker/instance/expenses.db'

def migrate(username):
    # قراءة المصروفات من SQLite
    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT amount, category, description, date FROM expense ORDER BY id')
    old_expenses = cursor.fetchall()
    conn.close()

    print(f"وجدت {len(old_expenses)} مصروف للنقل...")

    with app.app_context():
        user = User.query.filter_by(name=username).first()
        if not user:
            print(f"❌ المستخدم '{username}' غير موجود — سجّل أولاً في التطبيق")
            sys.exit(1)

        count = 0
        for amount, category, description, date_str in old_expenses:
            try:
                from datetime import date
                d = datetime.strptime(date_str, '%Y-%m-%d').date()
            except:
                d = date.today()

            e = Expense(
                user_id=user.id,
                amount=float(amount),
                category=category,
                description=description,
                date=d
            )
            db.session.add(e)
            count += 1
            print(f"  ✅ {amount} ر.ع - {description} ({date_str})")

        db.session.commit()
        print(f"\n🎉 تم نقل {count} مصروف بنجاح للمستخدم '{username}'!")

if __name__ == '__main__':
    username = input("أدخل اسم المستخدم (نفس الاسم في التطبيق): ").strip()
    migrate(username)
