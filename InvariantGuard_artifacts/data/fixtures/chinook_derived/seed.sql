INSERT INTO artists (artist_id, name) VALUES
    (1, 'Ada Quartet'),
    (2, 'Boundary Conditions'),
    (3, 'Serializable');

INSERT INTO albums (album_id, title, artist_id, is_published) VALUES
    (1, 'Conservative Bounds', 1, TRUE),
    (2, 'State Transitions', 1, TRUE),
    (3, 'Rollback', 2, TRUE),
    (4, 'Unknown Predicate', 3, FALSE);

INSERT INTO customers
    (customer_id, email, country, account_status, credit_cents, created_at)
VALUES
    (1, 'alice@example.test', 'US', 'active', 2500, '2025-01-01T00:00:00Z'),
    (2, 'bob@example.test', 'GB', 'active', 0, '2025-02-01T00:00:00Z'),
    (3, 'carol@example.test', 'US', 'suspended', 1000, '2025-03-01T00:00:00Z'),
    (4, 'dave@example.test', 'DE', 'active', 500, '2025-04-01T00:00:00Z'),
    (5, 'eve@example.test', 'US', 'closed', 0, '2025-05-01T00:00:00Z');

INSERT INTO invoices (invoice_id, customer_id, total_cents, status, issued_at) VALUES
    (1, 1, 1999, 'paid', '2025-06-01T00:00:00Z'),
    (2, 1, 500, 'open', '2025-06-02T00:00:00Z'),
    (3, 2, 1299, 'paid', '2025-06-03T00:00:00Z'),
    (4, 3, 2500, 'void', '2025-06-04T00:00:00Z'),
    (5, 4, 999, 'open', '2025-06-05T00:00:00Z');

INSERT INTO invoice_lines
    (invoice_line_id, invoice_id, album_id, quantity, unit_price_cents)
VALUES
    (1, 1, 1, 1, 1999),
    (2, 2, 2, 1, 500),
    (3, 3, 3, 1, 1299),
    (4, 4, 4, 1, 2500),
    (5, 5, 1, 1, 999);

SELECT setval(pg_get_serial_sequence('artists', 'artist_id'), 3, TRUE);
SELECT setval(pg_get_serial_sequence('albums', 'album_id'), 4, TRUE);
SELECT setval(pg_get_serial_sequence('customers', 'customer_id'), 5, TRUE);
SELECT setval(pg_get_serial_sequence('invoices', 'invoice_id'), 5, TRUE);
SELECT setval(pg_get_serial_sequence('invoice_lines', 'invoice_line_id'), 5, TRUE);

ANALYZE;

