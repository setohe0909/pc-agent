# 💻 Coder Web Sub-Agent v0.1.0

El **Coder Web Sub-Agent** es un agente autónomo diseñado para la creación y mantenimiento de plataformas e-commerce y proyectos de desarrollo web complejos.

## 🚀 Capacidades Principales

1. **Creación de E-commerce (Repo Puro):**
   - Generación de proyectos desde cero usando el stack: **React/TypeScript + Tailwind CSS + Supabase**.
   - Configuración automática de autenticación, base de datos y almacenamiento.
   - Integración con **Pilot AI** para el diseño de componentes y layouts.

2. **Memoria Proactiva (`!coder-web memory`):**
   - Almacena contextos de proyectos previos.
   - Recuerda preferencias de diseño y decisiones arquitectónicas.
   - Permite un seguimiento continuo del hilo de desarrollo.

## 🛠️ Comandos de Discord

| Comando | Descripción |
|---------|-------------|
| `!coder-web <desc>` | Inicia un nuevo proyecto o solicita un ajuste. Crea un hilo dedicado. |
| `!coder-web memory` | Muestra los aprendizajes y contextos actuales del agente. |
| `!coder-web memory --clean` | Borra la memoria del día (requiere confirmación). |

## 🏗️ Arquitectura Técnica

El agente utiliza **LangGraph** para orquestar sus estados:
- **Initialize:** Configura el entorno y stack.
- **Retrieve Context:** Inyecta memoria proactiva del contexto `coder-web`.
- **Analyze:** Diseña la arquitectura del repositorio.
- **Execute Task:** Interactúa con GitHub para crear el repositorio y genera código.
- **Finalize:** Reporta el estado final y guarda aprendizajes en MentisDB.

## 🖥️ Panel Administrativo

El portal administrativo permite configurar:
- **GitHub Tokens & Organizaciones.**
- **Stack Tecnológico Preferido.**
- **Nivel de Autonomía de Pilot AI.**

---
*PC Agent Pro - Autonomía en el Desarrollo Web*
