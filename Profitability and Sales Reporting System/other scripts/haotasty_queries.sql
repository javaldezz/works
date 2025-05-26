
-- Get all items in the order line by order_id, the payment type used, what menu
-- item was purchased, and how much the menu_item costs
SELECT order_line_t.order_id, payment_type, menu_item_name, menu_item_price
FROM order_t, order_line_t, menu_item_t
WHERE (order_line_t.order_id = order_t.order_id)
AND (order_line_t.menu_item_id = menu_item_t.menu_item_id);