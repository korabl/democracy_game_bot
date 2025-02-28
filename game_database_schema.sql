
-- psql -U postgres -d game_world

-- Создание базы данных игры

-- Таблица `USERS`
-- Таблица для хранения данных о пользователях игры.
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,            -- ID игрока в игре
    telegram_id INT NOT NULL UNIQUE,      -- ID пользователя из Telegram
    nickname VARCHAR(255),            -- Никнейм игрока (если есть)
    date_joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Дата присоединения
    in_game_year INT,                   -- Внутриигровой год
    is_active BOOLEAN DEFAULT TRUE    -- Флаг активности пользователя
);

-- Таблица `WORLDS`
-- Таблица для хранения данных о каждом сгенерированном мире в игре.
CREATE TABLE worlds (
    world_id SERIAL PRIMARY KEY,       -- Уникальный ID мира
    world_description TEXT,            -- Описание мира, сгенерированное GPT
    in_game_year INT,
    date_generated TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Дата генерации мира
);

-- Таблица `CHARACTERS`
-- Таблица для хранения связи user_id и world_id, а также описания персонажа.
CREATE TABLE characters (
    character_id SERIAL PRIMARY KEY,            -- Уникальный ID персонажа
    world_id INT REFERENCES worlds(world_id),   -- Ссылка на ID мира
    user_id INT REFERENCES users(user_id),      -- Ссылка на ID пользователя
    character_description TEXT,                 -- Описание персонажа, сгенерированное GPT
    date_generated TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Дата генерации персонажа
);

-- Таблица `WORLD_METRICS`
-- Таблица для хранения метрик мира. Каждая метрика имеет свой столбец в таблице, и все метрики обновляются в зависимости от внутриигрового года.
CREATE TABLE world_metrics (
    metric_id SERIAL PRIMARY KEY,         -- Уникальный ID метрики
    world_id INT REFERENCES worlds(world_id), -- Ссылка на мир
    world_news TEXT,                    -- Новостной дайджест к этому миру
    economy_metric INT,                 -- Метрика экономики
    social_stability_metric INT,        -- Метрика социальной стабильности  
    ecology_metric INT,                 -- Метрика экологии
    security_metric INT,                -- Метрика безопасности
    political_support_metric INT,       -- Метрика политической поддержки
    date_generated TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Время генерации метрики
);

-- Таблица `WORLD_STATISTICS`
-- Таблица для хранения статистики и изменений мира, таких как инициативы пользователей и их влияние на мир.
CREATE TABLE world_statistics (
    change_id SERIAL PRIMARY KEY,    -- Уникальный ID изменения
    world_id INT REFERENCES worlds(world_id), -- Ссылка на мир
    user_id INT REFERENCES users(user_id),  -- Ссылка на пользователя
    initiative_description TEXT,       -- Описание инициативы
    gpt_response TEXT,                 -- Ответ GPT
    change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Дата изменения
);

-- Таблица `WORLD_RESOURCES`
-- Таблица для хранения ресурсов мира
CREATE TABLE world_resources (
    id SERIAL PRIMARY KEY,
    world_id INT NOT NULL,
    money_resource DECIMAL(15, 2) DEFAULT 0,
    money_multiplier DECIMAL(5, 2) DEFAULT 1.00,
    people_resource INT DEFAULT 0,
    people_multiplier DECIMAL(5, 2) DEFAULT 1.00,
    date_generated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (world_id) REFERENCES worlds(world_id) ON DELETE CASCADE
);