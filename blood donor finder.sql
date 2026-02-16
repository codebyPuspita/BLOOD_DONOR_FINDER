USE blood_donor_finder;

-- Drop the old version so we can make the columns bigger
DROP TABLE IF EXISTS donor;

CREATE TABLE donor (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    blood_group VARCHAR(10) NOT NULL, -- Increased size
    location VARCHAR(255),            -- Increased size
    phone VARCHAR(20),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    eligibility_status VARCHAR(50) DEFAULT 'Eligible',
    availability_status VARCHAR(50) DEFAULT 'Active',
    last_login DATETIME NULL,
    last_donation_date DATE NULL,
    role VARCHAR(20) DEFAULT 'donor',
    approved BOOLEAN DEFAULT FALSE
);
