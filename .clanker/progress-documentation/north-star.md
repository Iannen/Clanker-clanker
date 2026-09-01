1. Implement functionality to support the management of a Github Profile Repository as a root / management project of the user.
    - I expect this would need a new resolver to 'peek' at content of other repositories (local repositories)

2. Differentiate shared and PUD specific domains by UI keys they map to
    - Currently ASDF row is not used.
    - Perhaps default domains and such can map there? So you get..
        '1234567890' -> PUD specific domains
        'QWER' -> Prompts for active domain
        'ASDF' -> Shared domains
    - Tis to be mulled

3. Clanker could validate PUDs for compliance with documentation system 
    - Find a way to declare the system 'first class' in code
    - PUDS should have progress docs per template dir, README.md in repo root
    - This is for the benefit of Github meta repo structure

4. Repository Context Contract enforcement - for the benefit of Iannen repo & llm trawlers

Clanker should define a standard Repository Context Contract for projects using it, enforcing it idempotently on repo initialization.

A conforming repository has:

A README at the repository root.
Progress documentation generated from Clanker templates:
North Star
Architecture
Project History
Backlog

Each template may have one or more corresponding documents, allowing larger projects to split their context into multiple documents. Documents should follow a naming convention that lets Clanker discover which template/category they belong to.

The contract should provide a standard baseline while allowing repositories such as Cloudproject to extend each category with additional documents.

5. Built in asset status system
    - To learn if there are dangling assets, not in use