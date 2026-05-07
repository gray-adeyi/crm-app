"""Lightweight SQLite column migrations (no Alembic) for local dev; use Alembic for PostgreSQL."""

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def _sqlite_columns(conn, table: str) -> set[str]:
    rows = conn.execute(text(f'PRAGMA table_info("{table}")')).fetchall()
    return {r[1] for r in rows}


def run_sqlite_migrations(engine: Engine) -> None:
    if not str(engine.url).startswith("sqlite"):
        return

    with engine.begin() as conn:
        insp = inspect(conn)
        if not insp.has_table("users"):
            return

        users_cols = _sqlite_columns(conn, "users")
        alters_users = [
            ("role", "ALTER TABLE users ADD COLUMN role VARCHAR DEFAULT 'admin'"),
            ("subscription_plan", "ALTER TABLE users ADD COLUMN subscription_plan VARCHAR DEFAULT 'starter'"),
            ("subscription_status", "ALTER TABLE users ADD COLUMN subscription_status VARCHAR DEFAULT 'active'"),
            ("subscription_ends_at", "ALTER TABLE users ADD COLUMN subscription_ends_at DATETIME"),
            ("business_name", "ALTER TABLE users ADD COLUMN business_name VARCHAR"),
            ("currency", "ALTER TABLE users ADD COLUMN currency VARCHAR DEFAULT 'NGN'"),
            ("logo_url", "ALTER TABLE users ADD COLUMN logo_url VARCHAR"),
            ("onboarding_completed", "ALTER TABLE users ADD COLUMN onboarding_completed INTEGER DEFAULT 0"),
            ("current_plan", "ALTER TABLE users ADD COLUMN current_plan VARCHAR DEFAULT 'starter'"),
            ("billing_cycle", "ALTER TABLE users ADD COLUMN billing_cycle VARCHAR DEFAULT 'monthly'"),
            ("renewal_date", "ALTER TABLE users ADD COLUMN renewal_date DATETIME"),
            ("trial_end_date", "ALTER TABLE users ADD COLUMN trial_end_date DATETIME"),
            ("trial_started_at", "ALTER TABLE users ADD COLUMN trial_started_at DATETIME"),
            ("trial_ends_at", "ALTER TABLE users ADD COLUMN trial_ends_at DATETIME"),
            ("business_phone", "ALTER TABLE users ADD COLUMN business_phone VARCHAR"),
            ("business_address", "ALTER TABLE users ADD COLUMN business_address TEXT"),
            ("notification_preferences", "ALTER TABLE users ADD COLUMN notification_preferences TEXT"),
            ("subscription_reference", "ALTER TABLE users ADD COLUMN subscription_reference VARCHAR"),
            ("paystack_customer_code", "ALTER TABLE users ADD COLUMN paystack_customer_code VARCHAR"),
            ("subscription_grace_until", "ALTER TABLE users ADD COLUMN subscription_grace_until DATETIME"),
        ]
        for col, stmt in alters_users:
            if col not in users_cols:
                conn.execute(text(stmt))
        conn.execute(text("UPDATE users SET onboarding_completed = 0 WHERE onboarding_completed IS NULL"))
        conn.execute(text("UPDATE users SET current_plan = subscription_plan WHERE current_plan IS NULL"))
        conn.execute(text("UPDATE users SET renewal_date = subscription_ends_at WHERE renewal_date IS NULL"))
        conn.execute(text("UPDATE users SET trial_ends_at = trial_end_date WHERE trial_ends_at IS NULL"))

        if insp.has_table("customers"):
            customers_cols = _sqlite_columns(conn, "customers")
            if "created_at" not in customers_cols:
                conn.execute(text("ALTER TABLE customers ADD COLUMN created_at DATETIME"))
                conn.execute(text("UPDATE customers SET created_at = datetime('now') WHERE created_at IS NULL"))

        if not insp.has_table("orders"):
            return

        orders_cols = _sqlite_columns(conn, "orders")
        alters_orders = [
            ("product_id", "ALTER TABLE orders ADD COLUMN product_id INTEGER"),
            ("quantity", "ALTER TABLE orders ADD COLUMN quantity INTEGER DEFAULT 1"),
            ("notes", "ALTER TABLE orders ADD COLUMN notes TEXT"),
            ("payment_method", "ALTER TABLE orders ADD COLUMN payment_method VARCHAR"),
            ("created_at", "ALTER TABLE orders ADD COLUMN created_at DATETIME"),
            ("delivery_date", "ALTER TABLE orders ADD COLUMN delivery_date DATE"),
            ("delivery_time", "ALTER TABLE orders ADD COLUMN delivery_time TIME"),
            ("delivery_notes", "ALTER TABLE orders ADD COLUMN delivery_notes TEXT"),
            ("reminder_sent", "ALTER TABLE orders ADD COLUMN reminder_sent INTEGER DEFAULT 0"),
            ("reminder_status", "ALTER TABLE orders ADD COLUMN reminder_status VARCHAR DEFAULT 'pending'"),
            ("stock_deducted", "ALTER TABLE orders ADD COLUMN stock_deducted INTEGER DEFAULT 0"),
            ("fulfillment_type", "ALTER TABLE orders ADD COLUMN fulfillment_type VARCHAR DEFAULT 'delivery'"),
            ("delivery_address", "ALTER TABLE orders ADD COLUMN delivery_address TEXT"),
        ]
        for col, stmt in alters_orders:
            if col not in orders_cols:
                conn.execute(text(stmt))
        conn.execute(text("UPDATE orders SET created_at = datetime('now') WHERE created_at IS NULL"))
        conn.execute(text("UPDATE orders SET quantity = 1 WHERE quantity IS NULL"))
        conn.execute(text("UPDATE orders SET reminder_sent = 0 WHERE reminder_sent IS NULL"))
        conn.execute(text("UPDATE orders SET reminder_status = 'pending' WHERE reminder_status IS NULL"))
        conn.execute(text("UPDATE orders SET stock_deducted = 0 WHERE stock_deducted IS NULL"))
        conn.execute(text("UPDATE orders SET fulfillment_type = 'delivery' WHERE fulfillment_type IS NULL"))

        if not insp.has_table("products"):
            conn.execute(
                text(
                    """
                    CREATE TABLE products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name VARCHAR NOT NULL,
                        sku VARCHAR,
                        category VARCHAR,
                        description TEXT,
                        unit_price INTEGER NOT NULL DEFAULT 0,
                        quantity_in_stock INTEGER NOT NULL DEFAULT 0,
                        reorder_threshold INTEGER NOT NULL DEFAULT 0,
                        image VARCHAR,
                        created_at DATETIME DEFAULT (datetime('now')),
                        updated_at DATETIME,
                        user_id INTEGER NOT NULL
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_products_user_id ON products(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_products_sku ON products(sku)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_products_category ON products(category)"))

        if insp.has_table("products"):
            product_cols = _sqlite_columns(conn, "products")
            product_alters = [
                ("peak_quantity", "ALTER TABLE products ADD COLUMN peak_quantity INTEGER NOT NULL DEFAULT 0"),
                ("is_low_stock", "ALTER TABLE products ADD COLUMN is_low_stock INTEGER NOT NULL DEFAULT 0"),
            ]
            for col, stmt in product_alters:
                if col not in product_cols:
                    conn.execute(text(stmt))
            conn.execute(
                text("UPDATE products SET peak_quantity = quantity_in_stock WHERE peak_quantity IS NULL OR peak_quantity = 0")
            )

        if not insp.has_table("inventory_movements"):
            conn.execute(
                text(
                    """
                    CREATE TABLE inventory_movements (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        kind VARCHAR NOT NULL,
                        delta_quantity INTEGER NOT NULL,
                        reason VARCHAR,
                        related_order_id INTEGER,
                        created_at DATETIME DEFAULT (datetime('now'))
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_inventory_movements_product_id ON inventory_movements(product_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_inventory_movements_user_id ON inventory_movements(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_inventory_movements_related_order_id ON inventory_movements(related_order_id)"))

        if not insp.has_table("notifications"):
            conn.execute(
                text(
                    """
                    CREATE TABLE notifications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        type VARCHAR NOT NULL,
                        title VARCHAR NOT NULL,
                        body TEXT,
                        severity VARCHAR NOT NULL DEFAULT 'info',
                        is_read INTEGER NOT NULL DEFAULT 0,
                        related_order_id INTEGER,
                        related_product_id INTEGER,
                        created_at DATETIME DEFAULT (datetime('now'))
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notifications_user_id ON notifications(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notifications_is_read ON notifications(is_read)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notifications_related_order_id ON notifications(related_order_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notifications_related_product_id ON notifications(related_product_id)"))

        if not insp.has_table("subscriptions"):
            conn.execute(
                text(
                    """
                    CREATE TABLE subscriptions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        plan_id VARCHAR NOT NULL,
                        status VARCHAR NOT NULL DEFAULT 'inactive',
                        billing_cycle VARCHAR NOT NULL DEFAULT 'monthly',
                        renewal_date DATETIME,
                        trial_end_date DATETIME,
                        paystack_subscription_code VARCHAR,
                        paystack_customer_code VARCHAR,
                        subscription_reference VARCHAR,
                        cancelled_at DATETIME,
                        created_at DATETIME DEFAULT (datetime('now')),
                        updated_at DATETIME
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_subscriptions_user_id ON subscriptions(user_id)"))

        if not insp.has_table("billing_transactions"):
            conn.execute(
                text(
                    """
                    CREATE TABLE billing_transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        plan_id VARCHAR NOT NULL,
                        amount INTEGER NOT NULL,
                        currency VARCHAR NOT NULL DEFAULT 'NGN',
                        reference VARCHAR NOT NULL UNIQUE,
                        paystack_access_code VARCHAR,
                        paystack_authorization_url VARCHAR,
                        paystack_transaction_id VARCHAR,
                        status VARCHAR NOT NULL DEFAULT 'initialized',
                        paid_at DATETIME,
                        created_at DATETIME DEFAULT (datetime('now'))
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_billing_transactions_user_id ON billing_transactions(user_id)"))

        if not insp.has_table("invoices"):
            conn.execute(
                text(
                    """
                    CREATE TABLE invoices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        transaction_id INTEGER,
                        invoice_number VARCHAR NOT NULL UNIQUE,
                        plan_id VARCHAR NOT NULL,
                        amount INTEGER NOT NULL,
                        currency VARCHAR NOT NULL DEFAULT 'NGN',
                        reference VARCHAR,
                        status VARCHAR NOT NULL DEFAULT 'issued',
                        issued_at DATETIME DEFAULT (datetime('now')),
                        paid_at DATETIME
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_invoices_user_id ON invoices(user_id)"))

        if not insp.has_table("billing_history"):
            conn.execute(
                text(
                    """
                    CREATE TABLE billing_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        action VARCHAR NOT NULL,
                        from_plan VARCHAR,
                        to_plan VARCHAR,
                        status VARCHAR NOT NULL,
                        reference VARCHAR,
                        note TEXT,
                        created_at DATETIME DEFAULT (datetime('now'))
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_billing_history_user_id ON billing_history(user_id)"))

        if not insp.has_table("user_activity_logs"):
            conn.execute(
                text(
                    """
                    CREATE TABLE user_activity_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        action VARCHAR NOT NULL,
                        entity_type VARCHAR NOT NULL,
                        entity_id INTEGER,
                        summary VARCHAR,
                        metadata_json TEXT,
                        created_at DATETIME DEFAULT (datetime('now'))
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_user_activity_logs_user_id ON user_activity_logs(user_id)"))

        if not insp.has_table("transaction_logs"):
            conn.execute(
                text(
                    """
                    CREATE TABLE transaction_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        category VARCHAR NOT NULL,
                        summary VARCHAR NOT NULL,
                        payload_json TEXT,
                        created_at DATETIME DEFAULT (datetime('now'))
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_transaction_logs_user_id ON transaction_logs(user_id)"))

        if not insp.has_table("vendor_report_dispatch"):
            conn.execute(
                text(
                    """
                    CREATE TABLE vendor_report_dispatch (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        report_kind VARCHAR NOT NULL,
                        period_key VARCHAR NOT NULL,
                        sent_at DATETIME DEFAULT (datetime('now'))
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_vendor_report_dispatch_user_kind_period ON vendor_report_dispatch(user_id, report_kind, period_key)"))

        if insp.has_table("payment_events"):
            payment_cols = _sqlite_columns(conn, "payment_events")
            payment_alters = [
                ("event_type", "ALTER TABLE payment_events ADD COLUMN event_type VARCHAR"),
                ("status", "ALTER TABLE payment_events ADD COLUMN status VARCHAR DEFAULT 'received'"),
                ("processed_at", "ALTER TABLE payment_events ADD COLUMN processed_at DATETIME"),
                ("payload", "ALTER TABLE payment_events ADD COLUMN payload TEXT"),
            ]
            for col, stmt in payment_alters:
                if col not in payment_cols:
                    conn.execute(text(stmt))

        if insp.has_table("users"):
            ucols = _sqlite_columns(conn, "users")
            if "email_verified" not in ucols:
                conn.execute(text("ALTER TABLE users ADD COLUMN email_verified INTEGER NOT NULL DEFAULT 1"))
            conn.execute(text("UPDATE users SET email_verified = 1 WHERE email_verified IS NULL"))

        if not insp.has_table("email_verification_tokens"):
            conn.execute(
                text(
                    """
                    CREATE TABLE email_verification_tokens (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email VARCHAR NOT NULL,
                        user_id INTEGER NOT NULL,
                        otp_hash VARCHAR NOT NULL,
                        expires_at DATETIME NOT NULL,
                        failed_attempts INTEGER NOT NULL DEFAULT 0,
                        consumed_at DATETIME,
                        last_sent_at DATETIME,
                        created_at DATETIME DEFAULT (datetime('now')),
                        FOREIGN KEY(user_id) REFERENCES users(id)
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_email_verification_tokens_email ON email_verification_tokens(email)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_email_verification_tokens_user_id ON email_verification_tokens(user_id)"))
