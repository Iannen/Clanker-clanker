1. Implement functionality to support the management of a Github Profile Repository as a root / management project of the user.
    - I expect this would need a new resolver to 'peek' at content of other repositories (local repositories)

2. Differentiate shared and PUD specific domains by UI keys they map to
    - Currently ASDF row is not used.
    - Perhaps default domains and such can map there? So you get..
        '1234567890' -> PUD specific domains
        'QWER' -> Prompts for active domain
        'ASDF' -> Shared domains
    - Tis to be mulled