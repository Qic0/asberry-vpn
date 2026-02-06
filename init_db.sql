PRAGMA foreign_keys = ON;

-- USERS
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    first_name TEXT,
    username TEXT,
    balance_rub INTEGER NOT NULL DEFAULT 10,
    last_billed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- DEVICES (VPN)
CREATE TABLE devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    telegram_id INTEGER NOT NULL,

    xui_inbound_id INTEGER NOT NULL,
    xui_client_uuid TEXT NOT NULL,
    xui_client_subid TEXT NOT NULL,
    xui_client_email TEXT,

    name TEXT,
    device_index INTEGER NOT NULL,   -- 1..15

    enabled INTEGER NOT NULL DEFAULT 1, -- 1/0
    price_per_day INTEGER NOT NULL DEFAULT 5,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    disabled_at DATETIME,

    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- PAYMENTS (FUTURE)
CREATE TABLE payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount_rub INTEGER NOT NULL,
    type TEXT NOT NULL, -- topup / charge
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(user_id) REFERENCES users(id)
);
