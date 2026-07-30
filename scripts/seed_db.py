import os
import random
import sqlite3
from datetime import datetime, timedelta

from faker import Faker

from sql_reflection_agent.db import DB_DIR, DB_PATH

fake = Faker()
Faker.seed(42)
random.seed(42)

COUNTRIES = ["Poland", "Germany", "France", "USA", "Ukraine", "Italy", "Spain"]


def setup_database():
    os.makedirs(DB_DIR, exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON")

    cursor.execute("""
        CREATE TABLE clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            country TEXT NOT NULL,
            signup_date TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            order_date TEXT NOT NULL,
            status TEXT NOT NULL,
            total_amount REAL NOT NULL,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
    """)

    conn.commit()
    return conn, cursor


def generate_clients(cursor):
    trap_clients = {}

    def get_signup_date():
        days_ago = random.randint(180, 240)
        return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO clients (name, email, country, signup_date) VALUES (?, ?, ?, ?)",
        (
            "Anna Kowalski",
            "anna.k1@example.com",
            random.choice(COUNTRIES),
            get_signup_date(),
        ),
    )
    trap_clients["anna_1"] = cursor.lastrowid

    cursor.execute(
        "INSERT INTO clients (name, email, country, signup_date) VALUES (?, ?, ?, ?)",
        (
            "Anna Kowalska",
            "anna.k2@example.com",
            random.choice(COUNTRIES),
            get_signup_date(),
        ),
    )
    trap_clients["anna_2"] = cursor.lastrowid

    cursor.execute(
        "INSERT INTO clients (name, email, country, signup_date) VALUES (?, ?, ?, ?)",
        ("Ghost Ghostovski", "Ghost.G@example.com", fake.country(), get_signup_date()),
    )
    trap_clients["ghost"] = cursor.lastrowid

    for _ in range(random.randint(15, 20)):
        cursor.execute(
            "INSERT INTO clients (name, email, country, signup_date) VALUES (?, ?, ?, ?)",
            (fake.name(), fake.email(), fake.country(), get_signup_date()),
        )

    return trap_clients


def generate_orders(cursor, trap_clients):
    trap_orders = {
        "all_cancelled_client_id": None,
        "cancelled_order_ids": [],
        "math_trap_ids": [],
    }

    cursor.execute("SELECT id FROM clients")
    all_client_ids = [row[0] for row in cursor.fetchall()]

    ghost_id = trap_clients["ghost"]
    all_client_ids.remove(ghost_id)

    unlucky_client_id = random.choice(all_client_ids)
    trap_orders["all_cancelled_client_id"] = unlucky_client_id

    total_orders = random.randint(60, 80)
    cancelled_indices = random.sample(range(total_orders), random.randint(5, 8))

    for i in range(total_orders):
        client_id = random.choice(all_client_ids)

        today = datetime.now()
        random_days_ago = timedelta(days=random.randint(0, 120))
        date_str = (today - random_days_ago).strftime("%Y-%m-%d %H:%M:%S")

        num_items = random.randint(1, 4)
        items_to_insert = []
        real_total = 0.0

        for _ in range(num_items):
            item_name = fake.word()
            item_quantity = random.randint(1, 3)
            item_price = round(random.uniform(10.0, 100.0), 2)

            real_total += item_price * item_quantity
            items_to_insert.append((item_name, item_quantity, item_price))

        if client_id == unlucky_client_id or i in cancelled_indices:
            status = "cancelled"
        else:
            status = "completed"

        is_math_trap = False
        if random.random() < 0.15:
            real_total += round(random.uniform(5.0, 15.0), 2)
            is_math_trap = True

        real_total = round(real_total, 2)

        cursor.execute(
            "INSERT INTO orders (client_id, order_date, status, total_amount) VALUES (?,?,?,?)",
            (client_id, date_str, status, real_total),
        )

        current_order_id = cursor.lastrowid

        for item in items_to_insert:
            cursor.execute(
                "INSERT INTO order_items (order_id, product_name, quantity, unit_price) VALUES (?, ?, ?, ?)",
                (current_order_id, item[0], item[1], item[2]),
            )

        if status == "cancelled" and client_id != unlucky_client_id:
            trap_orders["cancelled_order_ids"].append(current_order_id)

        if is_math_trap:
            trap_orders["math_trap_ids"].append(current_order_id)

    return trap_orders


if __name__ == "__main__":
    conn, cursor = setup_database()
    trap_clients = generate_clients(cursor)
    trap_orders = generate_orders(cursor, trap_clients)
    conn.commit()

    print("\n" + "=" * 50)
    print(" 🎉 БАЗА ДАННЫХ УСПЕШНО СГЕНЕРИРОВАНА 🎉")
    print("=" * 50)

    cursor.execute("SELECT COUNT(*) FROM clients")
    clients_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM orders")
    orders_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM order_items")
    items_count = cursor.fetchone()[0]

    print("\n📊 СТАТИСТИКА ПО ТАБЛИЦАМ:")
    print(f"Клиентов: {clients_count}")
    print(f"Заказов: {orders_count}")
    print(f"Товаров: {items_count}")

    print("\n🪤 ЛОВУШКИ ДЛЯ ТЕСТИРОВАНИЯ АГЕНТА:")
    print(
        f"1. Похожие имена: ID {trap_clients.get('anna_1')} (Kowalski) и ID {trap_clients.get('anna_2')} (Kowalska)"
    )
    print(f"2. Клиент без заказов: ID {trap_clients.get('ghost')} (Ghost User)")
    print(
        f"3. Клиент-неудачник (все отменено): ID {trap_orders.get('all_cancelled_client_id')}"
    )
    print(
        f"4. Разбросанные отмененные заказы: ID {trap_orders.get('cancelled_order_ids')}"
    )
    print(
        f"5. Математические ловушки (total != sum(items)): ID {trap_orders.get('math_trap_ids')}"
    )
    print("=" * 50 + "\n")

    conn.close()
