# Aprendizaje: explicaciones de código paso a paso

Explicaciones línea por línea del código del proyecto, escritas mientras se construye.
La vista general del proyecto (qué se hizo en cada hito y por qué) está en [`../bitacora_aprendizaje.md`](../bitacora_aprendizaje.md).

| # | Lección | Hito | Conceptos |
|---|---|---|---|
| 01 | [Funciones y tests: bloques horarios (RN-01)](01_funciones_y_tests_rn01.md) | H1.4 | función, *type hints*, `Literal`, cláusula de guarda, excepciones, pytest, decoradores, `parametrize`, TDD, funciones vs. POO |
| 02 | [Controles automáticos antes de cada commit (pre-commit)](02_pre_commit_hooks.md) | H1.5 | Git Hooks, Shift-Left, YAML, `rev` fijado, Conventional Commits, staging area, defensa en capas |
| 03 | [GitHub e Integración Continua (GitHub Actions)](03_github_y_ci.md) | H1.6 | remoto/`origin`/`push`, revisión previa a publicar, CI, workflow, runner, `--locked`, fallo silencioso |
| 04 | [Verificación de tipos con mypy](04_mypy_tipado_estatico.md) | H1.7 | tipado dinámico vs. estático, *type hints*, tipado gradual, `Any`, `strict`, `None`, hook local, límites de las herramientas |
| 05 | [Tu primera clase: configuración con pydantic-settings](05_primera_clase_configuracion.md) | H2.1 | Twelve-Factor, variables de entorno, `.env`; **POO: clase, instancia, atributo, herencia**; `SecretStr`; fixtures `monkeypatch`/`tmp_path` |
| 06 | [Cómo se construyó config.py y cómo se escribe un test, paso a paso](06_como_se_construyo_config_y_tests.md) | H2.1 | construcción incremental en 7 pasos; receta de 4 preguntas; Arrange/Act/Assert; 6 patrones de test; leer fallos. **Práctica:** [`practica/`](../../practica/README.md) |
| 07 | [Logging estructurado con run_id](07_logging_estructurado.md) | H2.2 | niveles de log, logger/handler/filter/formatter, JSON, Correlation ID; **POO: sobrescribir métodos, `self`, `__init__`, `super()`** |
| 08 | [Línea de comandos (CLI) y códigos de salida](08_cli_y_codigos_de_salida.md) | H2.3 | CLI, entry point, typer, **exit codes**, fail loud, regex, composición, `try`/`except`, `CliRunner` |
