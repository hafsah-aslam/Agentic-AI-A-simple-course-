-- Healthcare held-out fixture.
-- Structurally distinct from banking as well as from the development fixture:
--   * composite primary key on a temporal junction (encounter_clinicians)
--   * self-referencing FK modelling supervision (clinicians.supervisor_id)
--   * three-level cascade chain (patients -> encounters -> orders -> administrations)
--   * nullable FK, CHECK constraints, and a UNIQUE business key
CREATE TABLE departments (
    department_id INTEGER PRIMARY KEY,
    name          TEXT NOT NULL UNIQUE
);

CREATE TABLE clinicians (
    clinician_id  INTEGER PRIMARY KEY,
    department_id INTEGER NOT NULL REFERENCES departments(department_id) ON DELETE CASCADE,
    supervisor_id INTEGER REFERENCES clinicians(clinician_id) ON DELETE SET NULL,
    npi           TEXT    NOT NULL UNIQUE
);

CREATE TABLE patients (
    patient_id INTEGER PRIMARY KEY,
    mrn        TEXT    NOT NULL UNIQUE,
    name       TEXT    NOT NULL,
    active     BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE encounters (
    encounter_id INTEGER PRIMARY KEY,
    patient_id   INTEGER NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    status       TEXT    NOT NULL CHECK (status IN ('open', 'discharged', 'cancelled'))
);

-- many-to-many with a composite primary key
CREATE TABLE encounter_clinicians (
    encounter_id INTEGER NOT NULL REFERENCES encounters(encounter_id) ON DELETE CASCADE,
    clinician_id INTEGER NOT NULL REFERENCES clinicians(clinician_id) ON DELETE CASCADE,
    role         TEXT    NOT NULL CHECK (role IN ('attending', 'consulting', 'nurse')),
    PRIMARY KEY (encounter_id, clinician_id, role)
);

CREATE TABLE orders (
    order_id     INTEGER PRIMARY KEY,
    encounter_id INTEGER NOT NULL REFERENCES encounters(encounter_id) ON DELETE CASCADE,
    dose_mg      INTEGER NOT NULL CHECK (dose_mg > 0),
    signed_by    INTEGER REFERENCES clinicians(clinician_id) ON DELETE SET NULL
);

CREATE TABLE administrations (
    administration_id INTEGER PRIMARY KEY,
    order_id          INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    given             BOOLEAN NOT NULL DEFAULT FALSE
);

-- every open encounter must have exactly one attending
CREATE UNIQUE INDEX encounter_attending
    ON encounter_clinicians (encounter_id) WHERE role = 'attending';
