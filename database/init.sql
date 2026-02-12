-- ============================================================
-- 松哥的智能数据分析系统 — 电商演示数据库初始化脚本
-- 包含 5 张表 + 完整中文字段注释 + 约 10,000 条模拟数据
-- ============================================================

-- 创建只读用户
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'readonly_user') THEN
        CREATE ROLE readonly_user WITH LOGIN PASSWORD 'password';
    END IF;
END
$$;

-- ============================================================
-- 1. 商品分类表
-- ============================================================
CREATE TABLE IF NOT EXISTS categories (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    parent_id   INTEGER REFERENCES categories(id)
);

COMMENT ON TABLE  categories IS '商品分类表';
COMMENT ON COLUMN categories.id IS '分类ID，主键自增';
COMMENT ON COLUMN categories.name IS '分类名称';
COMMENT ON COLUMN categories.parent_id IS '父分类ID，为空表示顶级分类';

-- ============================================================
-- 2. 用户表
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    email           VARCHAR(200) UNIQUE NOT NULL,
    city            VARCHAR(100),
    registered_at   TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE  users IS '用户表';
COMMENT ON COLUMN users.id IS '用户ID，主键自增';
COMMENT ON COLUMN users.name IS '用户姓名';
COMMENT ON COLUMN users.email IS '用户邮箱，唯一';
COMMENT ON COLUMN users.city IS '所在城市';
COMMENT ON COLUMN users.registered_at IS '注册时间';

-- ============================================================
-- 3. 商品表
-- ============================================================
CREATE TABLE IF NOT EXISTS products (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    category_id     INTEGER REFERENCES categories(id),
    price           NUMERIC(10,2) NOT NULL,
    stock           INTEGER DEFAULT 0,
    created_at      TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE  products IS '商品表';
COMMENT ON COLUMN products.id IS '商品ID，主键自增';
COMMENT ON COLUMN products.name IS '商品名称';
COMMENT ON COLUMN products.category_id IS '所属分类ID';
COMMENT ON COLUMN products.price IS '商品价格（元）';
COMMENT ON COLUMN products.stock IS '库存数量';
COMMENT ON COLUMN products.created_at IS '创建时间';

-- ============================================================
-- 4. 订单表
-- ============================================================
CREATE TABLE IF NOT EXISTS orders (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER REFERENCES users(id),
    total_amount    NUMERIC(12,2) NOT NULL,
    status          VARCHAR(20) DEFAULT 'pending',
    created_at      TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE  orders IS '订单表';
COMMENT ON COLUMN orders.id IS '订单ID，主键自增';
COMMENT ON COLUMN orders.user_id IS '下单用户ID';
COMMENT ON COLUMN orders.total_amount IS '订单总金额（元）';
COMMENT ON COLUMN orders.status IS '订单状态：pending/paid/shipped/completed/cancelled';
COMMENT ON COLUMN orders.created_at IS '下单时间';

-- ============================================================
-- 5. 订单明细表
-- ============================================================
CREATE TABLE IF NOT EXISTS order_items (
    id              SERIAL PRIMARY KEY,
    order_id        INTEGER REFERENCES orders(id),
    product_id      INTEGER REFERENCES products(id),
    quantity        INTEGER NOT NULL,
    unit_price      NUMERIC(10,2) NOT NULL
);

COMMENT ON TABLE  order_items IS '订单明细表';
COMMENT ON COLUMN order_items.id IS '明细ID，主键自增';
COMMENT ON COLUMN order_items.order_id IS '所属订单ID';
COMMENT ON COLUMN order_items.product_id IS '商品ID';
COMMENT ON COLUMN order_items.quantity IS '购买数量';
COMMENT ON COLUMN order_items.unit_price IS '下单时单价（元）';

-- ============================================================
-- 插入演示数据
-- ============================================================

-- 分类数据（2 级分类）
INSERT INTO categories (id, name, parent_id) VALUES
    (1, '电子产品', NULL),
    (2, '服装', NULL),
    (3, '食品', NULL),
    (4, '家居', NULL),
    (5, '手机', 1),
    (6, '电脑', 1),
    (7, '耳机', 1),
    (8, '男装', 2),
    (9, '女装', 2),
    (10, '零食', 3),
    (11, '饮品', 3),
    (12, '家具', 4),
    (13, '厨具', 4)
ON CONFLICT DO NOTHING;

SELECT setval('categories_id_seq', 13);

-- 用户数据（500 用户，分布在 10 个城市）
INSERT INTO users (name, email, city, registered_at)
SELECT
    '用户' || i,
    'user' || i || '@example.com',
    (ARRAY['北京','上海','广州','深圳','杭州','成都','武汉','南京','重庆','西安'])[1 + (i % 10)],
    NOW() - (random() * INTERVAL '365 days')
FROM generate_series(1, 500) AS s(i)
ON CONFLICT (email) DO NOTHING;

-- 商品数据（200 个商品）
INSERT INTO products (name, category_id, price, stock, created_at)
SELECT
    (ARRAY['智能手机','笔记本电脑','无线耳机','机械键盘','运动T恤','牛仔裤','连衣裙','休闲外套','坚果礼盒','进口咖啡','气泡水','实木书桌','不锈钢锅','智能手表','平板电脑','蓝牙音箱','充电宝','羽绒服','卫衣','瑜伽垫'])[1 + (i % 20)]
    || ' ' || UPPER(SUBSTR(MD5(i::text), 1, 4)),
    (ARRAY[5,6,7,8,9,10,11,12,13,5,6,7,8,9,10,11,12,13,5,6])[1 + (i % 20)],
    ROUND((random() * 5000 + 10)::numeric, 2),
    (random() * 1000)::integer,
    NOW() - (random() * INTERVAL '180 days')
FROM generate_series(1, 200) AS s(i);

-- 订单数据（5000 单，近 12 个月）
INSERT INTO orders (user_id, total_amount, status, created_at)
SELECT
    1 + (random() * 499)::integer,
    ROUND((random() * 10000 + 50)::numeric, 2),
    (ARRAY['pending','paid','shipped','completed','cancelled'])[1 + (random() * 4)::integer],
    NOW() - (random() * INTERVAL '365 days')
FROM generate_series(1, 5000) AS s(i);

-- 订单明细（每单 1-3 个商品，约 10000 条）
INSERT INTO order_items (order_id, product_id, quantity, unit_price)
SELECT
    o.id,
    1 + (random() * 199)::integer,
    1 + (random() * 4)::integer,
    ROUND((random() * 5000 + 10)::numeric, 2)
FROM orders o,
     generate_series(1, 1 + (random() * 2)::integer) AS items;

-- ============================================================
-- 授权只读用户
-- ============================================================
GRANT CONNECT ON DATABASE demo_ecommerce TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly_user;
