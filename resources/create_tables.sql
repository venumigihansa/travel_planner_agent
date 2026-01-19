CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE user_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT UNIQUE NOT NULL,
    username TEXT,
    interests TEXT[] NOT NULL DEFAULT '{}'
);

CREATE TABLE bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id TEXT UNIQUE NOT NULL,
    user_id TEXT NOT NULL,
    hotel_id TEXT NOT NULL,
    check_in_date DATE,
    check_out_date DATE,
    booking_status TEXT NOT NULL,
    booking_date TIMESTAMPTZ NOT NULL DEFAULT now(),
    confirmation_number TEXT NOT NULL,
    details JSONB NOT NULL,
    hotel_name TEXT
);

CREATE INDEX bookings_user_id_idx ON bookings (user_id);
