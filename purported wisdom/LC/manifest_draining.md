# the idea, very crudely explained

suppose a manifest of files, that represents all the files of a repo

src/core/engine.py : 214 lines
src/core/models/entities.py : 89 lines
src/core/models/exceptions.py : 47 lines
src/services/ingestion/pipeline.py : 176 lines
src/services/ingestion/validators.py : 63 lines
src/services/render/shaper.py : 102 lines
src/adapters/fs_bridge.py : 81 lines
src/adapters/io_bridge.py : 54 lines
tests/unit/test_pipeline.py : 138 lines
config/domains/default.yaml : 29 lines

Then we say there are contexts of these, which are just subsets that may or may not overlap. its desireable that the contexts make sense stand-alone

--- 

the set of ctx starts out empty on iteration 1

ctx = [

]

manifest = <all the files>

then we say 'do your best to extract a meaningful subset (its probably good if we supply criteria and constraints - the HIL factor)'

---

we get 

ctx = [
    <3 files>
]

manifest = <all the files - 3 files>

then we say <do it again>

--- 

we get 

ctx = [
    <3 files>
    <2 files>
]

manifest = <all the files - 3 files - 2 files + 1 file > cuz there was overlap between the extracted sets - we are allowed to use previously extracted files

then we keep doing this, and we will have arrived at some organization
