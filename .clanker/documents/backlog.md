I. Long term goals

II. Medium term goals

III. Immediate goals

IV. Idea bucker:

- DYNAMIC GRID RENDERING ENGINE (EXTENSIBILITY PREREQUISITE)
   a. Decouple layout rendering from hardcoded MAIN_CONSOLE_TEMPLATE tokens.
   b. Implement programmatic button grid layout builder supporting flexible row sizes.
   c. Update OutputAssemblyService to render dynamic UI widths.
   d. result: Terminal console dynamically renders layouts based on arbitrary row key counts without template coupling.

V. Bugs
   - arrow keys interpreted as esc


HISTORY STASH (insert below)

I:    RESOLVE BASE PATH BINDING
      - Replaced dynamic runtime path injection at startup with an immutable base path locked in during bridge initialization.
      - Result: Guaranteed working-directory independence and deterministic path resolution across all file operations.

II:   REFACTOR CONFIGURATION & SESSION SERVICE
      - Transferred get_config() and save_config() persistence/validation logic from KeyboardService to SessionService.
      - Decoupled KeyboardService from direct file IO and annotated class with # new name proposal: CommandRouter.
      - Updated GameEngine.bootstrap() to query SessionService for configuration lifecycle operations.

III.  EXTRACT BASE ENGINE & EXCEPTION ABSTRACTION
      - Extracted generic lifecycle execution loop, abstract hooks, and centralized exception policy into base Engine class.
      - Delegated terminal loop mechanics, service exit signals (ProgramExitNotice), and error escalation away from GameEngine.
      - Result: GameEngine becomes purely declarative, leaving runtime orchestration and exception boundaries fully encapsulated in base infrastructure.

IV.   STANDARDIZE RENDER PIPELINES & SHIFT PROMPT GEN TO GAME ENGINE
      - Consolidated UI rendering and Prompt compilation under a single, stateless hydration endpoint (`OutputAssemblyService.hydrate(template, repl_map)`).
      - Shifted flow orchestration and template ownership to `GameEngine`, extracting fragment resolution into a dedicated map builder (`get_repl_map(prompt_config)`).
      - Completely removed internal template selection, dynamic XML generation, `_PromptBuilder`, and redundant `SymbolSet` tag assembly logic.
      - Result: Unified, stateless declarative template-hydration pipeline with zero dynamic builder overhead and clean separation of concerns.

V.    YML + BOOT WORK / RENDER PIPELINE STANDARDIZATION
      - Established dual data representation: raw YAML files in .clanker/configs and hydrated App Data Tree via strict Pydantic models.
      - Built dynamic BootService to ingest configs, resolve types, apply list hydration rules, and execute zip_add directives.
      - Consolidated Keyboard data object lifecycle into SessionService.get_keyboard() and removed legacy KeyboardService dependency.
      - Removed deprecated SymbolSet datamodels and enforced strict model validation across runtime objects.