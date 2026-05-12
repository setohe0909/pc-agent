# Observabilidad en PC Agent

Este documento describe el stack de observabilidad implementado en el sistema PC Agent para monitorear el rendimiento, depurar errores y rastrear la ejecución de los agentes.

## 1. Stack Tecnológico

El sistema utiliza las siguientes herramientas para observabilidad:

*   **Langfuse**: Plataforma de ingeniería de LLMs para rastreo (tracing), evaluación y gestión de prompts.
    *   **Uso**: Rastreo de cadenas de LLM, medición de latencia y costos (tokens).
    *   **Configuración**: `LANGFUSE_HOST`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`.
*   **FastAPI Health Checks**: Endpoints estandarizados en cada servicio para monitorear la salud.
    *   `/health`: Verifica que el servicio esté arriba.
    *   `/status`: (En `control-api`) Realiza una verificación profunda de integraciones (Supabase, Mentis, etc.).
*   **Docker Logs**: Los logs de todos los servicios se centralizan en la salida estándar (stdout) para su consumo mediante `docker logs` o agregadores de logs.

## 2. Monitoreo de Integraciones

El servicio `control-api` actúa como el centro de monitoreo de las dependencias:

### Supabase (Vector Store & DB)
*   **Endpoint**: `/api/supabase/verify`
*   **Verifica**: Conectividad, capacidad de lectura y escritura en las tablas de conocimiento y memoria.

### MentisDB (Memoria a Corto Plazo)
*   **Endpoint**: `/api/mentis/verify`
*   **Verifica**: Disponibilidad del servicio de memoria volátil/rápida.

## 3. Rastreo de Agentes (Tracing)

Cada solicitud al `assistant-runtime` debe ser rastreada. Actualmente, estamos integrando Langfuse para capturar:
1.  **Prompt original** enviado por el usuario.
2.  **Contexto recuperado** de la memoria (RAG).
3.  **Llamadas a herramientas** (Tool Calling).
4.  **Respuesta final** del modelo.

## 4. Gestión de Errores

Los errores se capturan en los bloques `try-except` de los workflows y se devuelven en un formato JSON estandarizado:
```json
{
  "status": "error",
  "reason": "Descripción técnica",
  "message": "Mensaje amigable para el usuario"
}
```

## 5. Próximos Pasos

*   [ ] Implementar **Dashboards en Langfuse** para medir la calidad de las respuestas (User Feedback).
*   [ ] Configurar **Alertas** (ej. Discord) cuando un servicio crítico (Supabase) falle.
*   [ ] Agregar **Métricas de Negocio** (ej. cuántos leads cualificados se generan por día).
