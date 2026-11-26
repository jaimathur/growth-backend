CREATE TABLE transactions (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id         BIGINT UNSIGNED NOT NULL,
  category_id     BIGINT UNSIGNED NOT NULL,
  title           VARCHAR(70)     NOT NULL,
  amount          DECIMAL(12,2)   NOT NULL,
  type            ENUM('Income','Expense') NOT NULL,
  payment_method  ENUM('UPI','Cash','Card','Bank transfer') NOT NULL,
  txn_date        DATE            NOT NULL,
  created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_txn_user_date (user_id, txn_date, id),
  KEY ix_txn_user_type_date (user_id, type, txn_date),
  CONSTRAINT ck_txn_amount_positive CHECK (amount > 0),
  CONSTRAINT fk_txn_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
  -- (category_id, type) must match a category row => type can't disagree with its category
  CONSTRAINT fk_txn_category_type FOREIGN KEY (category_id, type) REFERENCES categories (id, type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
