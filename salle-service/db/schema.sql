CREATE TABLE salles (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    capacite INTEGER NOT NULL CHECK (capacite > 0),
    equipements JSONB NOT NULL DEFAULT '[]'::jsonb,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX idx_salles_active ON salles(active);
CREATE INDEX idx_salles_capacite ON salles(capacite);