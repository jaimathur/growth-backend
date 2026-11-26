-- Categories. user_id IS NULL  => system category, shared by everyone, read-only for users.
--             user_id NOT NULL => custom category owned by exactly one user.
-- Each category has a type so an Income transaction can never be filed under an Expense category.
CREATE TABLE categories (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id     BIGINT UNSIGNED NULL,
  name        VARCHAR(50)     NOT NULL,
  type        ENUM('Income','Expense') NOT NULL,
  icon        VARCHAR(16)     NOT NULL DEFAULT '📌',
  sort_order  SMALLINT UNSIGNED NOT NULL DEFAULT 100,
  created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  -- target of the composite FK from transactions (category_id, type)
  UNIQUE KEY uq_categories_id_type (id, type),
  -- per-user uniqueness (NULL user_id rows, i.e. system rows, are managed by migrations only)
  UNIQUE KEY uq_categories_user_type_name (user_id, type, name),
  KEY ix_categories_user (user_id),
  CONSTRAINT fk_categories_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
