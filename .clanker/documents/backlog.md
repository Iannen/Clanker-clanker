Most relevant stuff:

- FIX SHIP WHITESPACE SHYTE
- MOVE CONTROL OF PROMPT GEN OUT FROM OUTPUTASSEMBLYSERVICE INTO GAMEENGINE, STANDARDIZING RENDER PIPELINES
   a. [x] Standardize both UI rendering and Prompt compilation to share a single public hydration endpoint: `OutputAssemblyService.hydrate(template, repl_map)`.
   b. [x] Refactor `OutputAssemblyService` to expose fragment resolution via a dedicated map builder (`get_repl_map(prompt_config)`), removing internal template selection and dynamic XML generation.
   c. [x] Completely eliminate `_PromptBuilder` and redundant `SymbolSet` tag assembly logic across the pipeline.
   d. [x] Shift template ownership and flow orchestration to `GameEngine`:
      - UI Flow: `GameEngine` collects UI map -> calls `OAS.hydrate(MAIN_CONSOLE_TEMPLATE, repl_map)` -> outputs to UI.
      - Prompt Flow: `GameEngine` requests fragment map via `OAS.build_prompt_repl_map(prompt)` -> calls `OAS.hydrate(DEFAULT_PROMPT_TEMPLATE, repl_map)` -> pushes to clipboard.
   e. [x] Result: Unified, stateless declarative template-hydration pipeline with zero dynamic builder overhead and clean separation of concerns.

- PIVOT ARCHITECTURE: REFACTOR APP TO GET DATA AS YML CONFIGS
   -> keyboard changed from 'service' to data object. 
   -> kb is no longer part of di, and is not instantiated in main. Sessionservice gets the responsibility of delivering the finished KB to engine on boot.
      -> we have two datashapes:
         -> on disk the data exists as yaml files
         -> in the app the data has the shape of a tree, quite like now.
      -> Sessionservice converts from filestate to treestate in the most general way possible
         -> the distribution of domains onto buttons requires a 'step out' of generalization.
   -> there is no saving of configs. user edits configs outside app, via llm.  


- Bugs
    a. arrow keys interpreted as esc

Back of pipeline stuff:

- MOVE SELECTED BTN STUFF & HANDLERS INSIDE KB. MAYB IT JUST TAKES CONFIG RATHER THAN B ORCHESTRATED

- DYNAMIC GRID RENDERING ENGINE (EXTENSIBILITY PREREQUISITE)
   a. Decouple layout rendering from hardcoded MAIN_CONSOLE_TEMPLATE tokens.
   b. Implement programmatic button grid layout builder supporting flexible row sizes.
   c. Update OutputAssemblyService to render dynamic UI widths.
   d. result: Terminal console dynamically renders layouts based on arbitrary row key counts without template coupling.


Recently achieved(:

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