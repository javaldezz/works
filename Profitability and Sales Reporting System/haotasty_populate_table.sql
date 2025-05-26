DELETE FROM user_t;
DELETE FROM menu_item_t;
DELETE FROM order_t;
DELETE FROM order_line_t;
DELETE FROM expense_cat_t;
DELETE FROM expense_t;

ALTER TABLE user_t
ADD FOREIGN KEY (user_added_by) REFERENCES auth_user(id) ON DELETE SET NULL,
ADD FOREIGN KEY (django_user_id) REFERENCES auth_user(id) ON DELETE CASCADE;


-- Insert Users
-- No more INSERT USERS; make admin user using command line
-- then add new users using interface after logged in
-- to hao tasty as admin

-- Insert Menu Items
INSERT INTO menu_item_t (menu_item_name, menu_item_price, menu_item_cost, menu_item_profit,
item_availability_status, menu_item_type)
VALUES
('Siomai', 60, 30, 30, 1, 'Side'),
('Siomai Rice', 75, 35, 40, 1, 'Side'),
('Hongkong Style Fried Noodles', 75, 35, 40, 1, 'Side'),
('Hongkong Style Fried Noodles with Siomai', 100, 40, 60, 1, 'Side'),
('Taiwanese Chicken Chops', 150, 50, 100, 1,'Main'),
('Chicken Chops Rice', 165, 60, 105, 1, 'Main'),
('Lechon Macau Rice', 180, 70, 110, 1, 'Main'),
('Sweet & Sour Pork Rice', 195,	75, 120, 1, 'Main'),
('Egg',	15,	5, 10, 1, 'Addon'),
('Rice', 15,	5, 10, 1, 'Addon'),
('Bottled Water',	25,	5, 20, 1, 'Addon'),
('Soft Drinks',	45,	10, 35, 1, 'Addon');

-- Insert Expense Categories
INSERT INTO expense_cat_t (expense_cat_name)
VALUES
('Supplies'),
('Transportation'),
('Salaries'),
('Miscellaneous');