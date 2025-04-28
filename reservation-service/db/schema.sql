CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TABLE reservations (
    id SERIAL PRIMARY KEY,
    salle_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'confirmed' 
        CHECK (status IN ('confirmed', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    EXCLUDE USING GIST (
        salle_id WITH =,
        tstzrange(start_time, end_time) WITH &&
    ) WHERE (status = 'confirmed')
);

CREATE INDEX idx_reservations_salle ON reservations(salle_id);
CREATE INDEX idx_reservations_user ON reservations(user_id);
CREATE INDEX idx_reservations_time ON reservations(start_time, end_time);
CREATE INDEX idx_reservations_status ON reservations(status);