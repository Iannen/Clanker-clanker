## The Fractal Context Pattern

A codebase architecture that uses consumer-driven contracts to slice LLM context by structure instead of search

Purpose: divvy up a codebase in self contained LLM contexts, information complete in some sense.

Each node and *all* its connected nodes, represent such a context.

There are two types of nodes:
    - package nodes, containing implementations
    - contract nodes, to connect the package nodes

---

Here is a repo showing packages and contract nodes. There are no llm contexts in this diagram.


```mermaid
graph LR
    Root["Root Package"]
    ItfA["Contract"]
    PackageA["Package A"]
    ItfA1["Contract"]
    ChildA1["Child Package A1"]
    ItfA2["Contract"]
    ChildA2["Child Package A2"]

    ItfB["Contract"]
    PackageB["Package B"]
    ItfB1["Contract"]
    ChildB1["Child Package B1"]
    ItfB2["Contract"]
    ChildB2["Child Package B2"]

    %% Flow Branch A
    Root --> ItfA
    ItfA --> PackageA
    PackageA --> ItfA1
    ItfA1 --> ChildA1
    PackageA --> ItfA2
    ItfA2 --> ChildA2

    %% Flow Branch B
    Root --> ItfB
    ItfB --> PackageB
    PackageB --> ItfB1
    ItfB1 --> ChildB1
    PackageB --> ItfB2
    ItfB2 --> ChildB2

    %% Styling for visual differentiation in VS Code preview
    style ItfA stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
    style ItfB stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
    style ItfA1 stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
    style ItfA2 stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
    style ItfB1 stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
    style ItfB2 stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
```

---

Here we show the same repo, this time with the ctx of the root node. 

```mermaid
graph LR
    Root["Root Package"]
    ItfA["Contract"]
    PackageA["Package A"]
    ItfA1["Contract"]
    ChildA1["Child Package A1"]
    ItfA2["Contract"]
    ChildA2["Child Package A2"]

    ItfB["Contract"]
    PackageB["Package B"]
    ItfB1["Contract"]
    ChildB1["Child Package B1"]
    ItfB2["Contract"]
    ChildB2["Child Package B2"]

    %% Flow Branch A
    Root --> ItfA
    ItfA --> PackageA
    PackageA --> ItfA1
    ItfA1 --> ChildA1
    PackageA --> ItfA2
    ItfA2 --> ChildA2

    %% Flow Branch B
    Root --> ItfB
    ItfB --> PackageB
    PackageB --> ItfB1
    ItfB1 --> ChildB1
    PackageB --> ItfB2
    ItfB2 --> ChildB2

    %% Root Context Boundary (Zoom Level 0)
    subgraph RootContext["Root Package Context Slice"]
        Root
        ItfA
        ItfB
    end

    %% Styling for boundary and contracts
    style RootContext fill:#00b4d8,fill-opacity:0.08,stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 4 4
    style ItfA stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
    style ItfB stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
    style ItfA1 stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
    style ItfA2 stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
    style ItfB1 stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
    style ItfB2 stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
```

---

Package B:

```mermaid
graph LR
    Root["Root Package"]
    ItfA["Contract"]
    PackageA["Package A"]
    ItfA1["Contract"]
    ChildA1["Child Package A1"]
    ItfA2["Contract"]
    ChildA2["Child Package A2"]

    ItfB["Contract"]
    PackageB["Package B"]
    ItfB1["Contract"]
    ChildB1["Child Package B1"]
    ItfB2["Contract"]
    ChildB2["Child Package B2"]

    %% Flow Branch A
    Root --> ItfA
    ItfA --> PackageA
    PackageA --> ItfA1
    ItfA1 --> ChildA1
    PackageA --> ItfA2
    ItfA2 --> ChildA2

    %% Flow Branch B
    Root --> ItfB
    ItfB --> PackageB
    PackageB --> ItfB1
    ItfB1 --> ChildB1
    PackageB --> ItfB2
    ItfB2 --> ChildB2

    %% Package B Context Boundary
    subgraph PackageBContext["Package B Context Slice"]
        ItfB
        PackageB
        ItfB1
        ItfB2
    end

    %% Styling for boundary and contracts
    style PackageBContext fill:#ffb703,fill-opacity:0.08,stroke:#ffb703,stroke-width:2px,stroke-dasharray: 4 4
    style ItfA stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
    style ItfB stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
    style ItfA1 stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
    style ItfA2 stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
    style ItfB1 stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
    style ItfB2 stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
```

---
Child package A2:

```mermaid
graph LR
    Root["Root Package"]
    ItfA["Contract"]
    PackageA["Package A"]
    ItfA1["Contract"]
    ChildA1["Child Package A1"]
    ItfA2["Contract"]
    ChildA2["Child Package A2"]

    ItfB["Contract"]
    PackageB["Package B"]
    ItfB1["Contract"]
    ChildB1["Child Package B1"]
    ItfB2["Contract"]
    ChildB2["Child Package B2"]

    %% Flow Branch A
    Root --> ItfA
    ItfA --> PackageA
    PackageA --> ItfA1
    ItfA1 --> ChildA1
    PackageA --> ItfA2
    ItfA2 --> ChildA2

    %% Flow Branch B
    Root --> ItfB
    ItfB --> PackageB
    PackageB --> ItfB1
    ItfB1 --> ChildB1
    PackageB --> ItfB2
    ItfB2 --> ChildB2

    %% Child Package A2 Context Boundary
    subgraph ChildA2Context["Child Package A2 Context Slice"]
        ItfA2
        ChildA2
    end

    %% Styling for boundary and contracts
    style ChildA2Context fill:#7209b7,fill-opacity:0.08,stroke:#7209b7,stroke-width:2px,stroke-dasharray: 4 4
    style ItfA stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
    style ItfB stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
    style ItfA1 stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
    style ItfA2 stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
    style ItfB1 stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
    style ItfB2 stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
```

---
And anotherone:

```mermaid
graph LR
    Root["Root Package"]
    ItfA["Contract"]
    PackageA["Package A"]
    ItfA1["Contract"]
    ChildA1["Child Package A1"]
    ItfA2["Contract"]
    ChildA2["Child Package A2"]

    ItfB["Contract"]
    PackageB["Package B"]
    ItfB1["Contract"]
    ChildB1["Child Package B1"]
    ItfB2["Contract"]
    ChildB2["Child Package B2"]

    %% Flow Branch A
    Root --> ItfA
    ItfA --> PackageA
    PackageA --> ItfA1
    ItfA1 --> ChildA1
    PackageA --> ItfA2
    ItfA2 --> ChildA2

    %% Flow Branch B
    Root --> ItfB
    ItfB --> PackageB
    PackageB --> ItfB1
    ItfB1 --> ChildB1
    PackageB --> ItfB2
    ItfB2 --> ChildB2

    %% Contract Context Boundary (Targeting Contract ItfB1)
    subgraph ContractB1Context["Contract Context Slice: ItfB1"]
        PackageB
        ItfB1
        ChildB1
    end

    %% Styling for boundary and contracts
    style ContractB1Context fill:#43aa8b,fill-opacity:0.08,stroke:#43aa8b,stroke-width:2px,stroke-dasharray: 4 4
    style ItfA stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
    style ItfB stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
    style ItfA1 stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
    style ItfA2 stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
    style ItfB1 stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
    style ItfB2 stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
```

---
and anotherone

```mermaid
graph LR
    Root["Root Package"]
    ItfA["Contract"]
    PackageA["Package A"]
    ItfA1["Contract"]
    ChildA1["Child Package A1"]
    ItfA2["Contract"]
    ChildA2["Child Package A2"]

    ItfB["Contract"]
    PackageB["Package B"]
    ItfB1["Contract"]
    ChildB1["Child Package B1"]
    ItfB2["Contract"]
    ChildB2["Child Package B2"]

    %% Flow Branch A
    Root --> ItfA
    ItfA --> PackageA
    PackageA --> ItfA1
    ItfA1 --> ChildA1
    PackageA --> ItfA2
    ItfA2 --> ChildA2

    %% Flow Branch B
    Root --> ItfB
    ItfB --> PackageB
    PackageB --> ItfB1
    ItfB1 --> ChildB1
    PackageB --> ItfB2
    ItfB2 --> ChildB2

    %% Contract Context Boundary (Targeting Contract ItfA)
    subgraph ContractAContext["Contract Context Slice: ItfA"]
        Root
        ItfA
        PackageA
    end

    %% Styling for boundary and contracts
    style ContractAContext fill:#f94144,fill-opacity:0.08,stroke:#f94144,stroke-width:2px,stroke-dasharray: 4 4
    style ItfA stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
    style ItfB stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
    style ItfA1 stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
    style ItfA2 stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
    style ItfB1 stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
    style ItfB2 stroke:#00b4d8,stroke-width:2px,stroke-dasharray: 5 5
```


### Notes
- chew on this. it seems clever, but is it?
- does it make implementing features easier or harder?