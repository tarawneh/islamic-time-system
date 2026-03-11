CREATE TABLE IF NOT EXISTS authorities (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    authority_code VARCHAR(64) NOT NULL,
    authority_name VARCHAR(255) NOT NULL,
    country_code CHAR(2) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_authority_code (authority_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS profiles (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    profile_code VARCHAR(64) NOT NULL,
    profile_name VARCHAR(255) NOT NULL,
    country_code CHAR(2) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_profile_code (profile_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS official_decisions (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    authority_id BIGINT UNSIGNED NOT NULL,
    profile_id BIGINT UNSIGNED NOT NULL,
    hijri_year SMALLINT UNSIGNED NOT NULL,
    hijri_month TINYINT UNSIGNED NOT NULL,
    gregorian_start_date DATE NOT NULL,
    announcement_utc DATETIME(6) NOT NULL,
    decision_status VARCHAR(64) NOT NULL,
    decision_title VARCHAR(255) NULL,
    decision_text MEDIUMTEXT NOT NULL,
    source_reference VARCHAR(255) NULL,
    source_url VARCHAR(1024) NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_by VARCHAR(128) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_official_decision (authority_id, profile_id, hijri_year, hijri_month),
    KEY idx_hijri_lookup (hijri_year, hijri_month),
    KEY idx_gregorian_start (gregorian_start_date),
    CONSTRAINT fk_decision_authority FOREIGN KEY (authority_id) REFERENCES authorities(id),
    CONSTRAINT fk_decision_profile FOREIGN KEY (profile_id) REFERENCES profiles(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS official_decision_audit_log (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    official_decision_id BIGINT UNSIGNED NOT NULL,
    action_type VARCHAR(32) NOT NULL,
    previous_snapshot_json LONGTEXT NULL,
    new_snapshot_json LONGTEXT NULL,
    performed_by VARCHAR(128) NULL,
    performed_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY idx_audit_decision (official_decision_id),
    CONSTRAINT fk_audit_decision FOREIGN KEY (official_decision_id) REFERENCES official_decisions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO authorities (authority_code, authority_name, country_code)
VALUES ('JO_DAR_AL_IFTAA', 'Jordan Dar Al-Iftaa', 'JO');

INSERT IGNORE INTO profiles (profile_code, profile_name, country_code)
VALUES ('JO_OFFICIAL', 'Jordan Official Profile', 'JO');
