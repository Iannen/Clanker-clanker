1. Implement functionality to support the management of a Github Profile Repository as a root / management project of the user.
    - I expect this would need a new resolver to 'peek' at content of other repositories (local repositories)

2. Differentiate shared and PUD specific domains by UI keys they map to
    - Currently ASDF row is not used.
    - Perhaps default domains and such can map there? So you get..
        '1234567890' -> PUD specific domains
        'QWER' -> Prompts for active domain
        'ASDF' -> Shared domains
    - Tis to be mulled

3. Built in asset status system
    - To learn if there are dangling assets, not in use

4. Elevate the ship script role
    - Can it do more than offer a 'save button'

5. Universal Project Contract & Validation Systems
- Repository contract
    - Purpose: enforce that PUD documentation is structurally uniform, for the benefit of user cognition and Github Metarepo handling of PUDs
    - such and so documents shall exist, in such and so dirs. Allow for PUD expansion beyond default by way of set recognition
- Runtime config validation 
    - Purpose: ensure configuration stability and extension adherence across PUD specific and shared config fragments, for the benefit of reader cognition
    - all config frags must obey a common policy
- Template asset validation 
    - Purpose: aggressively ensure stability of pud initialization assets 
    - all template assets must adhere to a policy
The contracts and policies should be declarative 'first class' members of Clanker codebase.
These become bootstrap validation phases:
    Violation ? aggregated feedback into Failure ex, inform user of path forward on app crash : bootstrap phase succeeds
    ..
    ..
