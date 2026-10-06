-- Banking held-out fixture.
-- Deliberately structurally distinct from the development fixture:
--   * composite primary key (account_holders)
--   * self-referencing foreign key (branches.parent_branch_id)
--   * many-to-many junction table (account_holders)
--   * nullable foreign key (accounts.closed_by_staff_id)
--   * CHECK constraints and a partial unique index
--   * multi-level ON DELETE CASCADE chain
CREATE TABLE branches (
    branch_id        INTEGER PRIMARY KEY,
    name             TEXT NOT NULL,
    parent_branch_id INTEGER REFERENCES branches(branch_id) ON DELETE SET NULL
);

CREATE TABLE staff (
    staff_id  INTEGER PRIMARY KEY,
    branch_id INTEGER NOT NULL REFERENCES branches(branch_id) ON DELETE CASCADE,
    name      TEXT NOT NULL
);

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    tier        TEXT NOT NULL CHECK (tier IN ('retail', 'premier', 'private'))
);

CREATE TABLE accounts (
    account_id          INTEGER PRIMARY KEY,
    branch_id           INTEGER NOT NULL REFERENCES branches(branch_id) ON DELETE CASCADE,
    balance_cents       BIGINT  NOT NULL,
    status              TEXT    NOT NULL CHECK (status IN ('open', 'frozen', 'closed')),
    closed_by_staff_id  INTEGER REFERENCES staff(staff_id) ON DELETE SET NULL
);

-- many-to-many with a composite primary key
CREATE TABLE account_holders (
    account_id  INTEGER NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    role        TEXT    NOT NULL CHECK (role IN ('primary', 'joint', 'signatory')),
    PRIMARY KEY (account_id, customer_id)
);

CREATE TABLE transactions (
    transaction_id INTEGER PRIMARY KEY,
    account_id     INTEGER NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
    amount_cents   BIGINT  NOT NULL,
    posted         BOOLEAN NOT NULL DEFAULT TRUE
);

-- exactly one primary holder per account
CREATE UNIQUE INDEX account_primary_holder
    ON account_holders (account_id) WHERE role = 'primary';
