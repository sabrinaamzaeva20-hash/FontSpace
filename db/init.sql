CREATE TABLE IF NOT EXISTS favorites (
    id SERIAL PRIMARY KEY,
    family VARCHAR(120) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL,
    project_name VARCHAR(120) NOT NULL DEFAULT 'Личная коллекция',
    notes VARCHAR(250) NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
INSERT INTO favorites (family, category, project_name, notes) VALUES
 ('Playfair Display', 'serif', 'Бутик-отель', 'Заголовки'),
 ('Inter', 'sans-serif', 'Веб-интерфейс', 'Основной текст')
ON CONFLICT (family) DO NOTHING;
