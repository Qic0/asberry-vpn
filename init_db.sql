PRAGMA foreign_keys = ON;

-- USERS
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    balance INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- VPN DEVICES
CREATE TABLE vpn_devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    telegram_id INTEGER NOT NULL,

    xui_client_uuid TEXT NOT NULL,
    device_index INTEGER NOT NULL,   -- 1..15

    enabled INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    disabled_at DATETIME,

    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- BILLING LOG
CREATE TABLE billing_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    device_id INTEGER NOT NULL,
    amount INTEGER NOT NULL, -- 5 rub
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(device_id) REFERENCES vpn_devices(id)
);

