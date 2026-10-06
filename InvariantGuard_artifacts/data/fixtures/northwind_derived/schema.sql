CREATE TABLE departments (department_id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    department_id INTEGER NOT NULL REFERENCES departments(department_id) ON DELETE RESTRICT,
    manager_id INTEGER REFERENCES employees(employee_id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    salary_cents INTEGER NOT NULL CHECK (salary_cents >= 0)
);
CREATE TABLE customers (customer_id INTEGER PRIMARY KEY, name TEXT NOT NULL, region TEXT);
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    freight_cents INTEGER NOT NULL CHECK (freight_cents >= 0)
);
CREATE TABLE products (product_id INTEGER PRIMARY KEY, name TEXT NOT NULL, unit_price_cents INTEGER NOT NULL CHECK (unit_price_cents >= 0));
CREATE TABLE order_items (
    order_id INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(product_id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (order_id, product_id)
);
CREATE TABLE tags (tag_id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
CREATE TABLE order_tags (order_id INTEGER REFERENCES orders(order_id) ON DELETE CASCADE, tag_id INTEGER REFERENCES tags(tag_id) ON DELETE CASCADE, PRIMARY KEY (order_id, tag_id));
CREATE TABLE audit_events (event_id INTEGER PRIMARY KEY, detail TEXT NOT NULL);
CREATE TABLE regions (region_id INTEGER PRIMARY KEY, code TEXT NOT NULL UNIQUE, description TEXT NOT NULL);
CREATE TABLE customer_regions (
    customer_id INTEGER REFERENCES customers(customer_id) ON DELETE CASCADE,
    region_id INTEGER REFERENCES regions(region_id) ON DELETE RESTRICT,
    assigned_at DATE NOT NULL,
    PRIMARY KEY (customer_id, region_id)
);
CREATE TABLE suppliers (supplier_id INTEGER PRIMARY KEY, company_name TEXT NOT NULL UNIQUE, country TEXT NOT NULL);
CREATE TABLE product_suppliers (
    product_id INTEGER REFERENCES products(product_id) ON DELETE CASCADE,
    supplier_id INTEGER REFERENCES suppliers(supplier_id) ON DELETE CASCADE,
    lead_days INTEGER NOT NULL CHECK (lead_days >= 0),
    PRIMARY KEY (product_id, supplier_id)
);
CREATE TABLE shipments (
    shipment_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    shipped_at DATE,
    carrier TEXT NOT NULL,
    tracking_code TEXT UNIQUE
);
