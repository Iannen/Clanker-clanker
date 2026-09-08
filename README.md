# Clanker clanker; 
## AIO HIL Solo Dev tool
Clanker is a homegrown TUI application which attempts to adress the various challenges facing the vibecoding solo develpoer, as experienced by its author.  


### Complaints and grievances of the vibecoding solo developer

Here follows a thematic representation of such.

#### Frustration aligned large language models

<blockquote>
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
</blockquote>

#### Fear-inducing git operations

<blockquote>
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
</blockquote>

#### The perils of freedom

<blockquote>
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
</blockquote>

#### Unsustainable context management practices

<blockquote>
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
</blockquote>

#### Distractions from the workflow loop

<blockquote>
<details>
<summary>asd</summary>

  ![SaaS Shaming Signup UI](presentation/saas_shaming.png)

</details>
</blockquote>

### Clanker features

Clanker attempts to adress such ills by way of its, per llm feedback, 'opinionated' feature set;

#### YAML-configured compilation pipeline (extract model thing in preceding section)

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

#### Built in collection of progress documentation, for a semistructured IDE internal documentation process

<details>
<summary> pls divvy me up </summary>

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

</details>

#### A workflow loop

<details>
<summary> loop </summary>

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

</details>

- A lightweight keyboard-driven interface for rapidly selecting domains and prompts.
- project specific assets, fallback to global assets 
- llm as consultant and workhorse
- vendor independence through browser interface boundary
- simple af UI.

### Status & Roadmap

I find Clanker to be a functional WIP application, producing for me...
- Challenges to tackle
- The means to do so
  
  
Ongoing efforts target configuration ingestion, as this is thought to unlock
- proper yaml validation
  - asset existence / compliance
  - proper user feedback, perhaps autofix options where possible
- decoupling of data and model
  - structure the conversion of data into app model classes
  - ease implementation of new features

## The breakdown

Here follows an technical breakdown of Clanker, per the authors
  - ..understanding of matters technical and architectural
  - ..recollection of the particulars
  - ..ability to convert the above to a easily digestible breakdown

I wish myself luck. But first, lets kick the can on that one and let ourselves be distracted an offering of usage examples:

### Clanker use examples


I think we can link out to actual docs showing the llm convos, extra points if we have commit ids and stuff.
At the same time, it should be understandable if the user can't be bothered with clicking links. I respect such a position

#### Clankerization of a project

#### A backlog planning session

#### Implementation of an item

#### Draining to project history

#### The ship

### Under the hood

#### strategy based stuff

Clanker was unifile
  - let the llm see the whole thing - correct context 
  - easy to drop off in the browser - ease of prompting

It held out for a while, but eventually..
- certain members became config / assets
- other members became python files of their own

In an attempt to retain the advantages of the unifile, a 'wheat and chaff' (or shit and cinnamon) split emerged:
- Let certain file contain high signal business logic and similar, to expose the workings of the app in an information dense manner.
- And other files contain the boilerplate, the low level transformations etc

In conversations with llm's, this was identified as the *Ports and Adapters* architecture:
- namedrop some guys
- explain in own words what that is about
- explain benefit it provides in selecting assets to form a proper prompt context for an llm

Then explain the members of the codebase on those terms.

#### Clanker Components

The components, their responsibilities
- AppEngine class
  - Delegates work to a service layer
    - first bootstrap / config ingestion to get RuntimeContext
    - then while loop
      - get key input
      - effectute
      - display msg
  - hotel manager (prompts as button inhabitants)

- dual purpose render pipeline
  - used for the UI renders
  - and prompt compilation

- ex system to implement failfast death by exit 1 policy
  - an early invention
  - to play around
  - an attempt at discouringing defensive coding (app death is fine and encouraged)

- config ingestion system
  - main function is to provide the RTC, else no Clanker
  - secondary to collect diagnostic info about issues with configs and the assets they reference
    - style preferences (no littering)
    - non-existent assets
    - things of that nature

#### explanation of .clanker contents 

- the configs
  - system config 
  - shared config
  - pud config

- prompt assets

- templates

### apologetic 'yeah i know man' section? ugh

Not apologetic but honest and reflective. Conclusive of the above

### easy 'howto' section, kinda

is this required? I'm not so sure. it feels kinda repetitive at this point  

1. Launch `clank` within any project repository.
2. Press numeric keys `1-0` to toggle active development domains.
3. Press hotkeys (`Q`, `W`, `E`, `R`) to compile context-aware prompts directly into the system clipboard.
4. Paste into your preferred LLM chat window.

## Final thoughs

some text here

### LLM Vendor breakdown

some text here, saying this is subjective off-the-cuff stuff.
free tier freeloaders perspective, if you will

#### Google 

The daily driver

Pros:
  - Flash -> great
  - Flash-lite -> less great, but highly serviceable
  - usage limits -> great

Cons:
  - 32k character input limit
  - fear-inducing security filters
  - some backend failures on display

#### ChatGPT

Sees little use for work. Used for 'rate my project' filedumps.
The OG - much respect.

Pros: 
  - bigger ctx, no idea of particulars
  - usage limits dont feel constrained
  - accepting of urls and zip files
Cons:
  - Feels dumber, more sycophantic
  - Has a brittle feel to it

#### Grok

Pros:
  - mature tone, feels great
  - takes filedumps, like ChatGPT

Cons:
  - Very restrictive on the free tier, so not serviceable 

#### Claude

Barely tried it - it felt very slow and engineered.

### The intended review options

a. Feel free to browse source code and such things.

b. Drop the below prompt into an llm, and then converse with it at your leisure
```plaintext
a yet to be supplied prompt
```

c. Drop the non-existant 'clanker-evalcopy.zip' off with your favourite llm, and then converse
  - removes the .git dir 
  - leaving only the pertinent stuff behind

### Installation & Prerequisites

You need python on your system. 
<howto box>
Per my understanding, python does not come with baked-in yaml parsing capabilites, so you will unfortunately have to install ruamel.yaml dependency via pip
<howto box>

Then, clone the repository to your preferred location
<howto box>

Symlink it
<howto box. what about windows users? mac?>

### Parting words of wisdom and other disclaimers 

<blank>


### blockquote

<blockquote>
</blockquote>

<blockquote>
<details>
<summary> blockquotes at least color it </summary>

```python
def hello():
    print("Hello, World!")
    return True
```

<details>
<summary> blockquotes at least color it </summary>
![SaaS Shaming Signup UI](presentation/saas_shaming.png)
</details>

</details>
<details>
<summary> blockquotes at least color it </summary>

![SaaS Shaming Signup UI](presentation/saas_shaming.png)

</details>
</blockquote>
