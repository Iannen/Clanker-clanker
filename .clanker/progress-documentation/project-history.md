I: RESOLVE BASE PATH BINDING
Locked the base path during bridge initialization instead of injecting it dynamically at runtime.
Result: deterministic, working-directory-independent file resolution.

II: REFACTOR CONFIGURATION & SESSION SERVICE
Moved configuration persistence/validation from KeyboardService into SessionService.
Decoupled KeyboardService from file IO and began its transition toward CommandRouter.
Updated GameEngine bootstrap to use SessionService for configuration lifecycle.

III: EXTRACT BASE ENGINE & EXCEPTION ABSTRACTION
Extracted lifecycle execution, abstract hooks, exit signaling, and exception policy into a generic Engine base class.
Result: GameEngine became declarative, with runtime orchestration and exception boundaries centralized in the base infrastructure.

IV: STANDARDIZE RENDER PIPELINES
Unified rendering and prompt compilation through stateless OutputAssemblyService.hydrate(template, repl_map).
Moved flow orchestration/template ownership into GameEngine and replaced dynamic builders/tag assembly with get_repl_map(prompt_config).
Result: a single declarative template-hydration pipeline with reduced builder overhead.

V: YAML + BOOT / RENDER PIPELINE STANDARDIZATION
Established raw YAML → hydrated App Data Tree flow using strict Pydantic models.
Added dynamic BootService for config ingestion, type resolution, list hydration, and zip_add.
Consolidated keyboard lifecycle under SessionService and removed legacy KeyboardService/SymbolSet dependencies.

VI: MULTI-DOCUMENT FRAGMENT RETRIEVAL & INTERNAL CONFIG
Added MULTI_DOC resolution with aggregated fragment placeholders (§base_fragments§, §domain_fragments§, §prompt_fragments§).
Migrated domain/prompt rendering to the multi-document schema.
Embedded CLANK_CONFIG as the development/runtime configuration source, eliminating duplicate external config.

VII: FLATTENED ASSET RETRIEVAL
Changed MULTI_DOC lookup to build a filename→path map across the entire assets tree.
Result: assets can be reorganized into subfolders without resolver configuration changes.

VIII: SCRIPT-DEV DOMAIN PROMPT ORGANIZATION
Split the monolithic script-dev render into explicit bl-add, bl-impl, and bl-drain flows.
Each flow now resolves only the fragments relevant to its operation, with drain additionally including history.

IX: REMOVAL OF PLAN ABSTRACTION & TEMPLATE OPTIMIZATION
Completely excised legacy 'plan' references from runtime, configuration, and prompt construction pipelines.
Streamlined PROMPT_TEMPLATE down to core multi-document and repo-content placeholders to reduce token overhead.

X: NORMALIZE RUAMEL INSTANCES
Consolidated YAML parsing/dumping across the application to utilize a single shared ruamel.yaml instance.
Result: Eliminated redundant parser instantiation and standardized YAML processing behavior across services.

XI: MAKE TEMPLATES SCRIPT INTERNAL
Refactored AssemblyService to resolve templates directly from built-in memory mappings instead of checking disk assets. Updated Render model defaults to fallback to prompt_template and configured UI renders to explicitly disable base/domain resolution. Removed explicit template references across domain YAML definitions.
Result: Eliminated runtime disk resolution overhead for templates and standardized internal template lookups.

XII: ADD TAIL TRUNCATION TO MULTI-DOCUMENT-RETRIEVAL (MDR)
Updated AssemblyService._resolve() to support both string filenames and objects containing `file` and `tail_lines` keys. Added conditional line slicing logic to prepend `**truncated**\n` when document line count exceeds `tail_lines`. Updated `CLANK_DOMAINS` for `bl-drain` render to apply `{ file: "history-doc.md", tail_lines: 8 }`.
Result: Resolved multi-document retrieval files can now be safely bounded by tail line counts without blowing up prompt size.

XIII: DISPLAY MSG FROM LAST ACTION & UI TEMPLATE UPDATE
Updated UI_TEMPL to feature a top border status bar slot (`§ msg §`). Refactored GameEngine._compile_to_clipboard() to include character counts alongside line counts in ActionResult. Updated GameEngine._render() to inject formatted message string into the UI replacement map prior to hydration.
Result: Last action status messages and prompt metrics are now dynamically displayed inside the TUI header.

XIV: REFACTOR MULTI-DOCUMENT RETRIEVAL TO RESOLVE FROM REPO ROOT
Updated `AssemblyService._resolve()` MULTI_DOC block to expand paths across the repository using `self.files.expand_paths(["."])`. Built an `asset_map` lookup table keyed by file basenames (`path.name`), allowing multi-doc resolvers to locate referenced files across subdirectories without requiring explicit relative paths.
Result: Multi-document retrieval now dynamically resolves file references relative to the project root directory.

XV: RELOCATE YAML CONFIGURATIONS TO DISK ASSETS
Migrated hardcoded configuration strings and domain definitions out of the main script and onto disk within the `.clanker/shared-assets/config-fragments/` directory as individual YAML files. Updated configuration assembly logic to dynamically load and merge `kb_def.yaml` from script resources and `config.yaml` from the workspace root into a unified runtime config, introducing the `ConfigAssemblyFailure` exception type for missing or invalid fragment states.
    - Relocated configuration definitions to disk storage under `.clanker/`
    - Unified configuration loading flow across Clanker and external projects

XVI: STREAMLINE PUD INITIALIZATION & DOCUMENTATION SEEDING
Updated workspace initialization routines to scaffold `.clanker/progress-documentation` and `.clanker/prompt-fragments` subdirectories automatically. Implemented template seeding logic to discover documentation templates with the `.template` extension relative to script assets and populate new progress documentation files using the `.cdoc` extension.
    - Added directory scaffolding for progress tracking and prompt fragments
    - Seeded project workspace with default `.cdoc` documentation templates

XVII: IMPLEMENT DUAL-SOURCE ASSET DISCOVERY (PREPARATORY MIGRATION)
    - Split 'FileBridge.base_path' into 'FileBridge.clanker_path' and 'FileBridge.pud_path' members
    - Updated 'FileBridge.__init__' to correctly assign values to both path attributes
    - Refactored path expansion into distinct 'FileBridge.get_clanker_files' and 'FileBridge.get_pud_files' methods
    - Divided file content reading into dedicated 'FileBridge.read_clanker_asset' and 'FileBridge.read_pud_asset' utilities
    - Migrated 'AssemblyService._resolve' to adopt PUD-specific asset retrieval calls as a foundation for upcoming collision handling