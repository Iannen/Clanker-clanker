I. Long term goals
    [ ] can we do without any external deps like ruamel & pydantic, lessening the install burden?
    [ ] prettify the UI template, for fun and profit.

II. Medium term goals
    [ ] the user should not have to start & stop the app for config updates to become online
    [ ] there should b default history doc as well as bl doc, for otherprojects.
    [ ] config dev and debloat domains need a more comprehensive suite of prompts & assets.
    [ ] Handle filename collisions in multi-doc resolution (e.g. nested files with identical names)
        - Plan:
            1. Evaluate path-based or namespaced resolution strategies instead of relying purely on basenames.
            2. Update AssemblyService._resolve to handle duplicate filenames deterministically without silent overwrites.

III. Immediate goals

IV. Idea bucket:

V. Non-critical bugs 
- arrow keys interpreted as esc