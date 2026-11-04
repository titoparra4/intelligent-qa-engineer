# Intelligent QA Engineer: resumen en español

**Intelligent QA Engineer** es una Agent Skill de código abierto (licencia
MIT) basada en el estándar abierto [Agent Skills](https://agentskills.io).
Convierte historias de usuario, criterios de aceptación, PRD, contratos
OpenAPI, código y *diffs* en estos entregables:

- análisis de requisitos;
- estrategias de prueba basadas en riesgo;
- casos de prueba con trazabilidad;
- escenarios negativos y límite;
- automatización de API ejecutable (Postman/Newman, pytest, Playwright,
  Jest/Vitest);
- selección de regresión;
- análisis de cobertura;
- informes de calidad.

La documentación completa está en inglés: [README.md](README.md).

## Qué la hace distinta

- **No inventa requisitos.** Registra supuestos (`A-n`) y preguntas
  abiertas (`Q-n`).
- **Etiqueta la evidencia.** Cada resultado es `GENERATED`, `EXPECTED`,
  `SIMULATED` u `OBSERVED`.
- **Estado de ejecución.** Cada prueba es `PASS`, `FAIL`, `BLOCKED` o
  `NOT RUN`. Nunca afirma que una prueba pasó si no se ejecutó.
- **No inventa porcentajes.** Distingue la cobertura de requisitos de la
  cobertura de código.
- **Trata los documentos analizados como datos.** Las instrucciones
  incrustadas en ellos, por ejemplo una inyección de *prompt*, se reportan y
  no se obedecen.
- **Responde en el idioma del usuario** (español o inglés). Los
  identificadores y los estados se mantienen en inglés.
- **Funciona sin herramientas**, en modo análisis. Si hay terminal, valida
  sus CSV con un script incluido que solo usa la biblioteca estándar de
  Python.

## Modos

| Modo | Para qué sirve |
|---|---|
| `ANALYZE` | Analizar requisitos |
| `STRATEGY` | Diseñar la estrategia de pruebas |
| `GENERATE` | Crear casos de prueba |
| `NEGATIVE` | Diseñar escenarios negativos y límite |
| `AUTOMATE` | Automatizar las pruebas |
| `REGRESSION` | Analizar la regresión |
| `COVERAGE` | Analizar la cobertura |
| `REPORT` | Elaborar informes |
| `FULL-QA` | Combinar los modos anteriores en una secuencia completa |

No hace falta nombrar el modo. La skill lo infiere de la petición.

## Instalación rápida

Con la CLI `skills` ([skills.sh](https://skills.sh)), sin clonar el repositorio:

```bash
npx skills add titoparra4/intelligent-qa-engineer
```

La CLI envía telemetría anónima de instalación a skills.sh; usa
`DISABLE_TELEMETRY=1` para desactivarla. Esta vía **aún no está verificada**.

O manualmente:

```bash
git clone https://github.com/titoparra4/intelligent-qa-engineer.git
cd intelligent-qa-engineer
# Claude Code (personal)
mkdir -p ~/.claude/skills && cp -R skills/intelligent-qa-engineer ~/.claude/skills/
# OpenAI Codex (usuario)
mkdir -p ~/.agents/skills && cp -R skills/intelligent-qa-engineer ~/.agents/skills/
```

En Claude Code también puedes instalarla como plugin:

```text
/plugin marketplace add titoparra4/intelligent-qa-engineer
/plugin install intelligent-qa-engineer@intelligent-qa-engineer
```

Para ChatGPT y otros agentes, consulta [docs/installation.md](docs/installation.md).
La compatibilidad con ChatGPT **no está verificada**.

## Ejemplos de uso

```text
Analiza esta historia de usuario y genera casos de prueba con matriz de trazabilidad.
Crea escenarios negativos para este endpoint.
Genera pruebas pytest a partir de este OpenAPI.
Prepara un plan de regresión para este pull request.
Analiza la cobertura de pruebas e identifica brechas.
```

## Ejemplos incluidos

El repositorio incluye cinco ejemplos completos en [examples/](examples/README.md):

1. Una historia de usuario con una inyección de *prompt* plantada, que la
   skill detecta e ignora.
2. Un catálogo de pruebas de API generado desde un contrato OpenAPI.
3. Una colección de Postman que se ejecuta con Newman.
4. Una suite pytest.
5. Un análisis de regresión.

Los ejemplos 3 y 4 se ejecutan contra una API simulada (*mock*) local y
determinista.

## Limitaciones

- La evaluación del comportamiento del agente es **manual** y está
  **pendiente**. Los escenarios están en [tests/scenarios](tests/scenarios/README.md).
- Las ejecuciones de los ejemplos son `SIMULATED`: corren contra un *mock*,
  no contra un servicio real.

Consulta el [informe de validación](docs/validation-report.md).
