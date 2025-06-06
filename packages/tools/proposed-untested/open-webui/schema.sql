CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  full_name VARCHAR(100) NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL,
  invitation_code VARCHAR(20) UNIQUE NOT NULL,
  status VARCHAR(50),
  membership_key VARCHAR(50) UNIQUE,
  activity_logs TEXT
);

CREATE TABLE invitations (
  id SERIAL PRIMARY KEY,
  code VARCHAR(20) UNIQUE NOT NULL,
  full_name VARCHAR(100) NOT NULL,
  pin VARCHAR(4) NOT NULL
);
