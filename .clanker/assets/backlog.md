0: Dropbox
only 1 rualmel yml instance required i think

I. Long term goals

II. Medium term goals (appears successful)
  - Refactor document retrieval to dynamic multi-file fragments
      - Add `multi-document-retrieval` resolver handling to `OutputAssemblyService` in `clanker.py`
      - Simplify `DEFAULT_PROMPT_TEMPLATE` to expect aggregated fragment slot
      - Migrate domain render configs in default YAMLs to use the new resolver format

  - Make clank_conf work from internal - not requiring external conf
      - So I dont have to juggle 2x confs
     
III. Immediate goals
  - Extend Resolver model & execution path in clanker.py
      - Add MULTI_DOCUMENT_RETRIEVAL to Resolver.Type enum
      - Implement multi-file resolution logic with fragment tag formatting in OutputAssemblyService._resolve()
  - Simplify prompt template & embedded YAML definitions
      - Reduce DEFAULT_PROMPT_TEMPLATE to use aggregated fragment slot (§prompt_fragments§)
      - Migrate CLANK_CONFIG_YAML and DEFAULT_CONFIG render resolvers to multi-document-retrieval payload
  - Synchronize active workspace configuration
      - Update .clanker/config.yaml to match new resolver syntax

IV. Idea bucket:

V. Known Bugs
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

VI.   MULTI-DOCUMENT FRAGMENT RETRIEVAL & INTERNAL CONFIG FALLBACK
      - Added MULTI_DOCUMENT_RETRIEVAL to Resolver.Type enum and implemented dynamic tag-wrapping multi-file resolution in OutputAssemblyService._resolve().
      - Standardized prompt templates around dynamic fragment placeholders (§base_fragments§, §domain_fragments§, §prompt_fragments§).
      - Migrated CLANK_CONFIG_YAML and DEFAULT_CONFIG render resolvers to leverage the new multi-document retrieval schema.
      - Updated SessionService._get_raw_config() to bypass disk IO when executing from script directory, defaulting directly to in-memory CLANK_CONFIG.
      - Result: Eliminated duplicate configuration maintenance in repo root while enabling completely dynamic, extensible multi-file prompt assembly.