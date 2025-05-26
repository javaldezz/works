DROP database haotasty_v1;
CREATE DATABASE haotasty_v1 CHARACTER SET utf8;
USE haotasty_v1;

CREATE TABLE user_t (
    user_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_added_by INT NULL,
    django_user_id INT NOT NULL UNIQUE,
    user_type ENUM('Administrator', 'Employee') NOT NULL DEFAULT 'Employee',
    user_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE menu_item_t (
    menu_item_id INT AUTO_INCREMENT PRIMARY KEY,
    menu_item_name VARCHAR(100) NOT NULL,
    menu_item_price DECIMAL(10,2) NOT NULL CHECK (menu_item_price >= 1.00), -- Matches MinValueValidator(1.00)
    menu_item_cost DECIMAL(10,2) NOT NULL CHECK (menu_item_cost >= 0.00),     -- Matches MinValueValidator(0.00)
    menu_item_profit DECIMAL(10,2) NULL, -- No GENERATED ALWAYS because Django doesn't support computed fields natively
    menu_item_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    item_availability_status INT NOT NULL DEFAULT 1, -- Matches IntegerField in Django model
    menu_item_type VARCHAR(20) NOT NULL  -- Added because it exists in Django but was missing in SQL
);

CREATE TABLE order_t (
    order_id INT NOT NULL auto_increment,
    payment_type VARCHAR(20) NOT NULL DEFAULT 'Cash',
    order_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reference_num VARCHAR(100) NULL,
    order_total DECIMAL(10,2) NULL, -- Added to store order total cost
    CONSTRAINT order_pk PRIMARY KEY (order_id)
);

CREATE TABLE order_line_t (
    order_line_id INT NOT NULL auto_increment,
    menu_item_id INT NOT NULL,
    order_id INT NOT NULL,
    order_quantity INT NOT NULL CHECK (order_quantity > 0),
    order_subtotal DECIMAL(10,2) NULL, -- Added to store order line subtotal
    CONSTRAINT order_line_pk PRIMARY KEY (order_line_id),
    CONSTRAINT order_line_fk1 FOREIGN KEY (menu_item_id) REFERENCES menu_item_t(menu_item_id),
    CONSTRAINT order_line_fk2 FOREIGN KEY (order_id) REFERENCES order_t(order_id)
);

CREATE TABLE expense_cat_t (
    expense_cat_id INT NOT NULL auto_increment,
    expense_cat_name VARCHAR(50) NOT NULL,
    category_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT expense_cat_pk PRIMARY KEY (expense_cat_id)
);

CREATE TABLE expense_t (
    expense_id INT NOT NULL auto_increment,
    expense_cat INT NOT NULL,
    expense_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    expense_amount DECIMAL(10,2) NOT NULL,
    expense_name VARCHAR(255) NOT NULL,
    expense_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT expense_pk PRIMARY KEY (expense_id),
    CONSTRAINT expense_fk FOREIGN KEY (expense_cat) REFERENCES expense_cat_t(expense_cat_id)
);