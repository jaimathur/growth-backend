-- Reference data: the category list that used to be hard-coded in the frontend
-- (dropdown order, names and emoji icons).
INSERT INTO categories (user_id, name, type, icon, sort_order) VALUES
  (NULL, 'Food',          'Expense', '🍜', 10),
  (NULL, 'Groceries',     'Expense', '🛒', 20),
  (NULL, 'Transport',     'Expense', '🚕', 30),
  (NULL, 'Bills',         'Expense', '🧾', 40),
  (NULL, 'Shopping',      'Expense', '🛍️', 50),
  (NULL, 'Health',        'Expense', '💊', 60),
  (NULL, 'Entertainment', 'Expense', '🎬', 70),
  (NULL, 'Other',         'Expense', '📌', 900),
  (NULL, 'Salary',        'Income',  '💼', 10),
  (NULL, 'Freelance',     'Income',  '✨', 20),
  (NULL, 'Other',         'Income',  '📌', 900);
