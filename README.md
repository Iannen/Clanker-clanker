# Clanker: AIO HIL Solo Dev tool

Clanker is a homegrown TUI application which attempts to adress the various challenges facing the vibecoding solo develpoer, as experienced by its author.  


### textosaurus rex
- *Verbose LLM outputs, littered with redundant in-line commentary and error masking default values*  
    ```python
    # function to retrieve and return the users items
    def process_user_items(user_id, items):
        #todo: find nice example
    ```
- *Fear-inducing git operations*
    ```
    $ git add .
    $ git commit -m "fixed minor bug in process_user_items"
    [main 4f82a1c] fixed minor bug in process_user_items
    1 file changed, 2 insertions(+), 1 deletion(-)
    $ git push origin main
    To github.com:user/clanker.git
    ! [rejected]        main -> main (fetch first)
    error: failed to push some refs to 'github.com:user/clanker.git'
    hint: Updates were rejected because the remote contains work that you do
    ```

- *The perils of freedom*
    ```
    .
    ├── app/
    │   ├── main.py
    │   ├── main_old.py
    │   ├── main_v2_working.py
    │   ├── main_FINAL_v3.py
    │   └── utils_broken.py
    ├── scripts/
    │   ├── deploy.sh
    │   ├── deploy_fix.sh
    │   ├── quick_patch.sh
    │   └── DO_NOT_RUN.sh
    ├── notes/
    │   ├── todo.txt
    │   ├── todo2_real.txt
    │   └── scratchpad_untitled3.txt
    ├── config.json
    ├── config.json.bak
    ├── config.json.bak2
    └── .env.backup_copy
    ```
- *The monolithic single-file project, to facilitate ease of prompting*
    ```python
    import os, sys, json, time, sqlite3, asyncio, logging, re
    from dataclasses import dataclass
    from typing import Dict, List, Optional, Any, Union

    class ServerApplication:
        def __init__(self, config):
            ...
    
    # ... [450 lines of middleware, CORS, and startup hooks omitted] ...

    class UserController:
        def handle_user_request(self, request):
            ...

    # ... [800 lines of request parsing and route logic omitted] ...

    class UserService:
        def process_user_business_logic(self, payload):
            ...

    # ... [650 lines of validation, domain logic, and error handlers omitted] ...

    class UserRepository:
        def execute_raw_db_query(self, query, params):
            ...
    ```

- *KYC-themed registrations*

  ![SaaS Shaming Signup UI](presentation/saas_shaming.png)
    
Clanker attempts to adress such ills by way of its, per llm feedback, 'opinionated' feature set;

- *YAML-configured domain -> prompt model, makes it easy to 'get her in there'*

  ```yaml
  filesets:
  core: {includes: [clanker.py, models.py]}
  ad-hoc: {includes: [utilities.py, adapters.py], excludes: []} 
  
  domains:
  - name: script-dev
    resolvers:
      - { id: repo_content, type: repo_content, fileset: core }
      - { id: domain_fragments, type: multi-document-retrieval, files: [backlog.cdoc], }
    prompts:
      - name: plan
        render:
          resolvers:
            - { id: prompt_fragments, type: multi-document-retrieval, files: [plan-mode.md, backlog-output-instructions.md] }
      - name: impl
        render:
          resolvers:
            - {id: prompt_fragments, type: multi-document-retrieval, files: [do-mode.md, code-output-instruction.md]}
      - name: bl-drain
        render:
          resolvers:
            - {id: prompt_fragments, type: multi-document-retrieval, files: [doc-management-mode.md, {file: project-history.cdoc, tail_lines: 8}, history-output-instructions.md]}
  ```

- *The Clanker Loop*

    ```mermaid
    flowchart TD
        A[Optional: Draft thoughts in North Star doc] --> B[1. Plan backlog items]
        B --> C[2. Ask LLM to generate code]
        C --> D{3. Satisfied?}
        D -- Yes --> E[Accept outputs]
        D -- No --> C
        E --> F[4. LLM updates project history]
        F --> G[5. Rinse & Repeat]
    ```



- A semistructured LLM-assisted development workflow built around explicit domains and development operations.
- A closed development loop spanning planning, implementation, review, refinement, and documentation.
- Persistent project context that survives individual LLM conversations and model sessions.
- Built-in progress documentation that keeps development history and project knowledge alongside the code.
- Declaratively defined, project-specific prompts and development workflows.
- Domain-oriented navigation that lets the developer work by development concern rather than manually hunting through files.
- Repeatable prompt recipes that make successful LLM interactions reproducible.
- Version-controlled `.clanker` project configuration that turns the project's LLM workflow into part of the repository itself.
- Context curation that separates the question of what the developer wants to accomplish from the mechanics of supplying the LLM with the necessary material.
- A lightweight keyboard-driven interface for rapidly selecting domains and prompts.
- A persistent interface between the developer's project and otherwise ephemeral LLM sessions.
- A mechanism for continuously refining the project's own LLM-assisted development methodology through dogfooding.
- A foundation for iterative context gathering, where future interactions can request additional project context rather than requiring everything up front.
- A foundation for detecting missing, unused, or dangling context assets.
- A foundation for formally describing the project's structure and conventions through universal project contracts.
- A foundation for packaging coherent project context into review bundles for comprehensive LLM-assisted reviews.
- A foundation for extending context management from individual projects to collections of related projects.
- A practical way to make LLM-assisted software development more persistent, repeatable, contextual, and project-specific.






- **Status & Roadmap**: Functional active prototype with a stable resolution pipeline, full keyboard interface, and core template engine. Continuous efforts are directed toward refining default asset schemas and stabilizing progress tracking mechanisms.

---

# Terminal-First Prompt Engineering Workflow
Clanker serves as a bridge between local repository state and external LLM environments, standardizing project context into clipboard-ready prompts without external API dependencies.

- **Use-Case Breakdown**:
  - **Context Aggregation**: Automatically packs repository trees, individual files, and configuration fragments using delimited tags.
  - **Dynamic Resolution**: Evaluates YAML configurations to bundle domain-specific prompt layouts with active code files.
  - **Progress Tracking**: Tracks evolving architecture across development sessions using a template-driven documentation system (`.cdoc`).

- **Architecture & Structure**:
  - `clanker.py`: Implements the presentation, execution engine (`AppEngine`), state management (`SessionService`), and template hydration pipeline (`AssemblyService`).
  - `models.py`: Defines core data classes, protocol interfaces (`FileBridgePort`, `IOBridgePort`), custom domain exception hierarchies, and domain entities (`Keyboard`, `Resolver`, `Domain`).

- **Usage & Workflow**:
  1. Launch `clank` within any project repository.
  2. Press numeric keys `1-0` to toggle active development domains.
  3. Press hotkeys (`Q`, `W`, `E`, `R`) to compile context-aware prompts directly into the system clipboard.
  4. Paste into your preferred LLM chat window.

---

# Project Access & Setup

- **Review Options**:
  - **Manual Review**: Examine `clanker.py` and `models.py` for decoupled service architecture and protocol contracts.
  - **Conversational Agent Review**: Pass the repository URL directly to an AI agent for code pattern analysis.
  - **Evaluative Review**: Pass `evalcopy.zip` to an AI model for structured architecture audits.

- **Installation & Prerequisites**:
  - **Prerequisites**: Python 3.10+ and `ruamel.yaml`.
    '''bash
    pip install ruamel.yaml
    '''
  - **Clone Repository**:
    '''bash
    git clone https://github.com/Iannen/Clanker-clanker.git
    cd Clanker-clanker
    '''
  - **Symlink Setup**:
    '''bash
    chmod +x clanker.py
    sudo ln -s "$(pwd)/clanker.py" /usr/local/bin/clank
    '''

- **Notes & Disclaimers**:
  - **LLM Performance Notes**:
    - *Gemini*: Recommended choice for consistent handling of long structured context templates.
    - *ChatGPT*: Highly functional, though occasionally sensitive to very large prompt payloads.
    - *Grok*: Operational, but bound by free-tier volume limits.
    - *Claude*: Performs accurately across initial tested configurations.
  - **General Notice**: This tool is developed with LLM assistance. Users should inspect local scripts prior to running execution symlinks in critical production environments.