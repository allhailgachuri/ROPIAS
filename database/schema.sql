-- Stores every query a farmer makes
CREATE TABLE queries (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    latitude        REAL NOT NULL,
    longitude       REAL NOT NULL,
    onset_result    TEXT,          -- 'True Onset', 'False Onset', etc.
    onset_color     TEXT,          -- 'green', 'red', 'grey'
    moisture_pct    REAL,          -- GWETROOT as percentage
    irrigation_status TEXT,
    data_start      TEXT,          -- Start date of NASA window
    data_end        TEXT           -- End date of NASA window
);

-- Stores cached NASA API responses (avoid repeated API calls)
CREATE TABLE api_cache (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key   TEXT UNIQUE,       -- lat_lon_start_end hash
    fetched_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at  DATETIME,          -- 48hrs after fetch
    payload     TEXT               -- JSON string of API response
);

-- Stores SMS alert subscriptions
CREATE TABLE alert_subscriptions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    phone       TEXT NOT NULL,
    latitude    REAL NOT NULL,
    longitude   REAL NOT NULL,
    active      BOOLEAN DEFAULT TRUE,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Stores historical validation records (for ML training labels)
CREATE TABLE historical_onsets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    latitude        REAL,
    longitude       REAL,
    year            INTEGER,
    season          TEXT,          -- 'long_rains' or 'short_rains'
    onset_date      TEXT,          -- Actual onset date from KMD records
    true_onset      BOOLEAN,       -- Ground truth label
    system_result   TEXT,          -- What ROPIAS classified it as
    correct         BOOLEAN        -- Did system get it right?
);
