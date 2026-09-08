# Clanker clanker; 
## AIO HIL Solo Dev tool
Clanker is a homegrown TUI application which attempts to adress the various challenges facing the vibecoding solo develpoer, as experienced by its author.  


### Complaints and grievances of the vibecoding solo developer

Here follows a thematic representation of such.

#### Frustration aligned large language models

<details>
<summary>Repeated in-line commentary</summary>

  ```python
  def hello():
      print("Hello, World!")
      return True
  ```

</details>

<details>
<summary>Error masking fallbacks</summary>

  ```python
  def hello():
      print("Hello, World!")
      return True
  ```

</details>
  

#### Fear-inducing git operations

<details>
<summary>After an on-Github 'quickfix' </summary>

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

</details>

#### The perils of freedom

<details>
<summary>Difficulties of planning</summary>

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

</details>

#### Unsustainable context management practices

<details>
<summary>One file to rule them all, and in technical debt bind them</summary>

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

</details>

#### Distractions from the workflow loop

<details>
<summary>asd</summary>

  ![SaaS Shaming Signup UI](presentation/saas_shaming.png)

</details>
    

### Clanker features

Clanker attempts to adress such ills by way of its, per llm feedback, 'opinionated' feature set;

#### YAML-configured compilation pipeline

<details>
<summary> Model of project domains with prompts, to organize content </summary>

  ```python
  def hello():
      print("Hello, World!")
      print("Lets do a mermaid")
      return True
  ```

</details>

<details>
<summary>a yaml config</summary>

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

</details>

<details>
<summary> the ugly but functional truth 1 </summary>

  ![UI on program start ](presentation/saas_shaming.png)

</details>

<details>
<summary> the ugly but functional truth 2 </summary>

  ![UI after domain selection ](presentation/saas_shaming.png)

</details>

<details>
<summary> the ugly but functional truth 3 </summary>

  ![UI after prompt selection](presentation/saas_shaming.png)

</details>


#### pushdown marker

<details>
<summary> templatosaurus rex </summary>

  ```python
  def hello():
      print("Hello, World!")
      return True
  ```

</details>

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
- *Built in collection of progress documentation, for a semistructured IDE internal documentation process*
  ```plantext
    .clanker/progress-documentation/
  ├── architecture.cdoc
  ├── backlog.cdoc
  ├── north-star.cdoc
  └── project-history.cdoc

  ---.clanker/progress-documentation/architecture.cdoc---
  // For gentlemen proficient in such matters

  ---.clanker/progress-documentation/backlog.cdoc---
  // The most used document
  I. Ideas, complaints and non-critical bugs:
  II. Items to refine & QC:
  III. Slated for implementation:
  IV. Recently implemented:
  V. Critical bugs

  === .clanker/progress-documentation/north-star.cdoc ===
  // A dropbox of sorts
  === .clanker/progress-documentation/project-history.cdoc ===
  // a ledger of completed backlog items, compressed & formatted by Clanker
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

- A lightweight keyboard-driven interface for rapidly selecting domains and prompts.
- project specific assets, fallback to global assets 
- llm as consultant and workhorse
- vendor independence through browser interface boundary
- simple af UI.

### Status & Roadmap

- functional WIP application, primarily used on itself.
- Ongoing efforts target configuration ingestion to promote yaml validation and ease the implementation of new features.

---

## the middle section
### some usage examples, possible link out for ez

### an 'architecture' part
#### strategy based stuff
- P/A attempt, primarily for benefit of high signal core when prompting
#### componet based description of src code
- then something to describe src code as components:
    - while loop engine
    - dual purpose render pipeline
    - ex system to implement failfast death by exit 1 policy
    - config ingestion system, RuntimeConfig assembly

#### explanation of .clanker contents 

### apologetic 'yeah i know man' section? ugh


### easy 'howto' section, kinda
  1. Launch `clank` within any project repository.
  2. Press numeric keys `1-0` to toggle active development domains.
  3. Press hotkeys (`Q`, `W`, `E`, `R`) to compile context-aware prompts directly into the system clipboard.
  4. Paste into your preferred LLM chat window.

## The outro

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
  - **Subjective LLM Performance Notes**:
    - *Gemini*: The daily driver. 
    - *ChatGPT*: Feels flaky and sycophantic, but more accepting of filedumps
    - *Grok*: Not viable with free tier restrictions, but has a great feel to it.
    - *Claude*: Barely tried it - it felt very slow.
  