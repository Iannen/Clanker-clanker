I. Ideas, complaints and non-critical bugs:

- Visual upgrade to UI template
- the user should not have to start & stop the app for config updates to become online
- can we do without any external deps like ruamel & pydantic, lessening the install burden?
- arrow keys interpreted as esc

II. Items to refine & QC:

1. Look for ways to improve upon recently implemented ports & adapters architecture
    - offload non-business logic to adapters, leave behind clean code
    - the code should not use members of the adapters not offered by their ports, as this appears as 'magic' unless the reader also has access to the adapter impls

III. Slated for implementation:

V. Critical bugs
