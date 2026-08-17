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

VI.   MULTI-DOCUMENT FRAGMENT RETRIEVAL & INTERNAL CONFIG FALLBACK
      - Added MULTI_DOC (`multi-document-retrieval`) to Resolver.Type and implemented dynamic multi-file resolution with per-document fragment tags in OutputAssemblyService._resolve().
      - Standardized prompt assembly around aggregated fragment placeholders (§base_fragments§, §domain_fragments§, §prompt_fragments§).
      - Migrated CLANK_DOMAINS and DEFAULT_DOMAINS render resolvers to the multi-document retrieval schema, including multi-file prompt fragments such as prompt-script-dev.md + backlog.md.
      - Embedded CLANK_CONFIG as the internal configuration source when executing from the script directory, eliminating the need to maintain a duplicate external configuration for the development/runtime environment.
      - Result: Dynamic, extensible multi-file prompt assembly with centralized internal configuration and no duplicate configuration maintenance.

VII. FLATTENED ASSET RETRIEVAL BY FILENAME
      - MULTI_DOC resolver now builds a name→path map over the entire assets directory tree.
      - Lookup is by basename only; user can freely reorganize subfolders without updating resolver file lists.
      
VIII. SCRIPT-DEV DOMAIN PROMPT ORGANIZATION
      - Replaced single monolithic render with three explicit flows: bl-add, bl-impl, bl-drain.
      - Each flow pulls the appropriate instruction fragment + backlog (+ history for drain).