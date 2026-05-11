# Influencer & Collab Finder (Buscador de Colaboraciones)

Este módulo facilita la expansión de la audiencia de la marca identificando perfiles y estrategias de colaboración alineadas con la identidad del negocio.

## Funcionalidad
El agente utiliza su capacidad de análisis para proponer socios estratégicos y dinámicas de colaboración.

- **Comando**: `!marketer collab [marca/perfil]`
- **Propuestas**:
    - **Micro-Influencers**: Sugiere tipos de cuentas con audiencias comprometidas y nicho.
    - **Cuentas de Complemento**: Identifica marcas no competidoras para sorteos o co-branding.
    - **Formatos de Campaña**: Propone ideas como Takeovers, Unboxings o Guest Posting.

## Implementación Técnica
- **Workflow**: `MarketingWorkflow._find_collaborations()`
- **Lógica**: Basada en el perfil de la marca, el LLM genera una lista de criterios de búsqueda y ejemplos de colaboración que maximizan la credibilidad y el alcance.

## Beneficios
- Ahorra tiempo en la fase de prospección de influencers.
- Asegura que las colaboraciones tengan una base estratégica y no sean solo transaccionales.
- Fomenta el crecimiento mediante la validación por terceros.
