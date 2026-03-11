
CREATE TABLE IF NOT EXISTS calculation_runs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    city VARCHAR(128) NOT NULL,
    latitude DOUBLE,
    longitude DOUBLE,
    gregorian_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS prayer_times (
    run_id BIGINT UNSIGNED,
    fajr DATETIME,
    sunrise DATETIME,
    dhuhr DATETIME,
    asr DATETIME,
    maghrib DATETIME,
    isha DATETIME,
    PRIMARY KEY (run_id),
    FOREIGN KEY (run_id) REFERENCES calculation_runs(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS moon_data (
    run_id BIGINT UNSIGNED,
    moon_age_hours DOUBLE,
    altitude_deg DOUBLE,
    elongation_deg DOUBLE,
    lag_time_minutes DOUBLE,
    PRIMARY KEY (run_id),
    FOREIGN KEY (run_id) REFERENCES calculation_runs(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS visibility_results (
    run_id BIGINT UNSIGNED,
    criterion_name VARCHAR(64),
    raw_value DOUBLE,
    category VARCHAR(64),
    explanation TEXT,
    PRIMARY KEY (run_id, criterion_name),
    FOREIGN KEY (run_id) REFERENCES calculation_runs(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
