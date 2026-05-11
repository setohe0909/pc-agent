-- Crear tabla para configuración persistente del sistema
CREATE TABLE IF NOT EXISTS system_config (
    id TEXT PRIMARY KEY,
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Habilitar RLS
ALTER TABLE system_config ENABLE ROW LEVEL SECURITY;

-- Política para que el service_role pueda hacer todo
CREATE POLICY "service_role_full_access" ON system_config
    FOR ALL USING (true) WITH CHECK (true);

-- Política para lectura pública (opcional, dependiendo de si queremos que el bot la lea directo)
CREATE POLICY "public_read_access" ON system_config
    FOR SELECT USING (true);

-- Insertar registro inicial si no existe
INSERT INTO system_config (id, config)
VALUES ('default', '{}')
ON CONFLICT (id) DO NOTHING;
