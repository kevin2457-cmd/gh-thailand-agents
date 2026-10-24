-- GH Thailand 仓储库存 + CRM 数据库结构（SQLite）
-- 设计原则：数据库保存事实，确定性代码负责计算，LLM 只负责理解和解释。
-- 库存不单独存一个"当前数量"字段：当前库存 = stock_moves 的累计和（见 v_stock），这样每一次变动都有记录可查。
-- 所有数量的单位都是 products.unit（桶/瓶，和采购 Excel 的"当量"一致）。金额单位是美元（USD）。

PRAGMA foreign_keys = ON;

-- 用户和角色：staff 录单，owner 审批
CREATE TABLE users (
    id          TEXT PRIMARY KEY,                -- 例如 U01
    name        TEXT NOT NULL,
    role        TEXT NOT NULL CHECK (role IN ('owner', 'staff'))
);

CREATE TABLE suppliers (
    id                      TEXT PRIMARY KEY,    -- 例如 S01
    name                    TEXT NOT NULL,
    country                 TEXT,
    default_lead_time_days  INTEGER NOT NULL CHECK (default_lead_time_days > 0)
);

CREATE TABLE products (
    sku              TEXT PRIMARY KEY,           -- 例如 MONSTER-BLOOM
    brand            TEXT NOT NULL DEFAULT '',
    name             TEXT NOT NULL,              -- 标准英文名，统计都用它
    size             TEXT NOT NULL DEFAULT '',   -- 例如 25lb, 5G, 1L
    unit             TEXT NOT NULL DEFAULT 'unit',
    cost_usd         REAL NOT NULL CHECK (cost_usd >= 0),        -- 拿货价（最近一柜）
    freight_usd      REAL NOT NULL DEFAULT 0 CHECK (freight_usd >= 0),  -- 每桶分摊运费（最近一柜）
    price_usd        REAL NOT NULL CHECK (price_usd >= 0),       -- 建议零售价
    floor_price_usd  REAL NOT NULL CHECK (floor_price_usd >= 0), -- 建议销售底价，低于它要警告
    safety_stock     INTEGER NOT NULL CHECK (safety_stock >= 0),
    lead_time_days   INTEGER NOT NULL CHECK (lead_time_days > 0),
    supplier_id      TEXT NOT NULL REFERENCES suppliers(id),
    aliases          TEXT NOT NULL DEFAULT '',   -- 中文俗称和各种写法，用 | 分隔，例如 "紫粉|MB|Monster"
    active          INTEGER NOT NULL DEFAULT 1
);

-- 客户。code 是发给模型时用的代号；name/phone/address 是隐私字段，永远不发给模型。
CREATE TABLE customers (
    id            TEXT PRIMARY KEY,              -- 例如 C001
    code          TEXT NOT NULL UNIQUE,          -- 例如 CUST-001
    name          TEXT NOT NULL,
    phone         TEXT,
    address       TEXT,
    wechat_alias  TEXT,                          -- 微信里显示的名字
    region        TEXT NOT NULL,
    type          TEXT NOT NULL CHECK (type IN ('grow_shop', 'farm', 'reseller', 'retail')),
    created_at    TEXT NOT NULL                  -- YYYY-MM-DD
);

CREATE TABLE sales (
    id            TEXT PRIMARY KEY,              -- 例如 SO-000123
    sale_date     TEXT NOT NULL,                 -- YYYY-MM-DD
    customer_id   TEXT NOT NULL REFERENCES customers(id),
    source        TEXT NOT NULL DEFAULT 'import' CHECK (source IN ('import', 'wechat', 'excel', 'invoice', 'report', 'chat')),
    note          TEXT
);

CREATE TABLE sale_items (
    sale_id     TEXT NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    sku         TEXT NOT NULL REFERENCES products(sku),
    qty         INTEGER NOT NULL CHECK (qty > 0),
    unit_price  REAL NOT NULL CHECK (unit_price >= 0),
    PRIMARY KEY (sale_id, sku)
);

CREATE TABLE purchases (
    id             TEXT PRIMARY KEY,             -- 例如 PO-0042
    supplier_id    TEXT NOT NULL REFERENCES suppliers(id),
    order_date     TEXT NOT NULL,
    expected_date  TEXT NOT NULL,
    received_date  TEXT,                         -- NULL 表示还在路上（在途库存）
    status         TEXT NOT NULL CHECK (status IN ('ordered', 'received', 'cancelled')),
    note           TEXT
);

CREATE TABLE purchase_items (
    purchase_id  TEXT NOT NULL REFERENCES purchases(id) ON DELETE CASCADE,
    sku          TEXT NOT NULL REFERENCES products(sku),
    qty          INTEGER NOT NULL CHECK (qty > 0),
    unit_cost    REAL NOT NULL CHECK (unit_cost >= 0),       -- 拿货价
    freight_per_unit REAL NOT NULL DEFAULT 0 CHECK (freight_per_unit >= 0),
    PRIMARY KEY (purchase_id, sku)
);

-- 库存流水：唯一的库存事实来源。出库为负数，入库为正数。
CREATE TABLE stock_moves (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sku         TEXT NOT NULL REFERENCES products(sku),
    move_date   TEXT NOT NULL,
    qty_change  INTEGER NOT NULL CHECK (qty_change <> 0),
    reason      TEXT NOT NULL CHECK (reason IN ('opening', 'sale', 'purchase_receipt', 'adjustment')),
    ref_id      TEXT                             -- sales.id / purchases.id / pending_records.id
);
CREATE INDEX idx_stock_moves_sku_date ON stock_moves (sku, move_date);

-- 待审批记录：员工或 Agent 提交的任何写入都先进这里，老板批准后才写入上面的业务表。
CREATE TABLE pending_records (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    kind          TEXT NOT NULL CHECK (kind IN ('sale', 'purchase', 'receipt', 'adjustment')),
    payload_json  TEXT NOT NULL,                 -- 结构化草稿（客户、SKU、数量、价格……）
    source_type   TEXT NOT NULL CHECK (source_type IN ('wechat', 'excel', 'invoice', 'report', 'chat')),
    source_text   TEXT,                          -- 原始输入（已脱敏），审批时对照
    warnings      TEXT NOT NULL DEFAULT '[]',    -- 校验发现的问题，JSON 数组
    submitted_by  TEXT NOT NULL REFERENCES users(id),
    submitted_at  TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    reviewed_by   TEXT REFERENCES users(id),
    reviewed_at   TEXT,
    review_note   TEXT,
    result_ref    TEXT                           -- 批准后生成的 sales.id / purchases.id
);
CREATE INDEX idx_pending_status ON pending_records (status);

-- 审计日志：每一次提交、批准、拒绝、写入都记一条
CREATE TABLE audit_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    ts           TEXT NOT NULL,
    actor        TEXT NOT NULL,                  -- users.id 或 agent 名
    role         TEXT NOT NULL,
    action       TEXT NOT NULL,                  -- submit / approve / reject / write / blocked ...
    entity       TEXT NOT NULL,
    entity_id    TEXT,
    detail_json  TEXT NOT NULL DEFAULT '{}'
);

-- 每次模型调用的 token 用量（Tokenomics 证据从第一天开始记录）
CREATE TABLE llm_usage (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ts              TEXT NOT NULL,
    run_id          TEXT NOT NULL,
    agent           TEXT NOT NULL,
    model           TEXT NOT NULL,
    input_tokens    INTEGER NOT NULL DEFAULT 0,
    cached_tokens   INTEGER NOT NULL DEFAULT 0,
    output_tokens   INTEGER NOT NULL DEFAULT 0,
    requests        INTEGER NOT NULL DEFAULT 1,
    cost_usd        REAL
);

-- 当前库存
CREATE VIEW v_stock AS
SELECT p.sku, p.name, p.size, p.unit, p.safety_stock, p.lead_time_days,
       COALESCE(SUM(m.qty_change), 0) AS on_hand
FROM products p
LEFT JOIN stock_moves m ON m.sku = p.sku
GROUP BY p.sku;

-- 在途库存（已下单、未到货）
CREATE VIEW v_in_transit AS
SELECT pi.sku, SUM(pi.qty) AS in_transit, MIN(pu.expected_date) AS next_arrival
FROM purchase_items pi
JOIN purchases pu ON pu.id = pi.purchase_id
WHERE pu.status = 'ordered'
GROUP BY pi.sku;

-- 每张销售单的总额
CREATE VIEW v_sale_totals AS
SELECT s.id AS sale_id, s.sale_date, s.customer_id,
       SUM(si.qty) AS total_qty, SUM(si.qty * si.unit_price) AS total_usd
FROM sales s
JOIN sale_items si ON si.sale_id = s.id
GROUP BY s.id;
