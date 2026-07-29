active_num_btn: '1'
rows:
  domain_row:
    primary: '1234567890'
    secondary: '!"#¤%&/()='
  prompt_row:
    primary: qwer
    secondary: QWER
  action_row:
    primary: asdf
    secondary: ASDF
domains:
- name: Main script
  plan:
  prompts:
  - name: config-dev
    symbol_set:
      indent: '  '
      arrow_indent: =>
      open_tag: <{tag} {attr}>
      open_tag_no_attr: <{tag}>
      closed_tag: </{tag}>
      self_closing_tag: <{tag} {attr} />
      self_closing_no_attr: <{tag} />
    prompt_fragments:
    - id: general_rules
      type: document
      path: .clanker/assets/general-rules.md
      resolver:
    - id: config_development
      type: document
      path: .clanker/assets/config_development_instructions.md
      resolver:
    - id: script_file_only
      type: file_set
      path:
      resolver:
        sorter: path_asc
        inclusion_roots:
        - clanker.py
        exclusion_roots: []
  - name: script-dev
    symbol_set:
      indent: '  '
      arrow_indent: =>
      open_tag: <{tag} {attr}>
      open_tag_no_attr: <{tag}>
      closed_tag: </{tag}>
      self_closing_tag: <{tag} {attr} />
      self_closing_no_attr: <{tag} />
    prompt_fragments:
    - id: general_rules
      type: document
      path: .clanker/assets/general-rules.md
      resolver:
    - id: script_dev
      type: document
      path: .clanker/assets/script_dev_instructions.md
      resolver:
    - id: script_file_only
      type: file_set
      path:
      resolver:
        sorter: path_asc
        inclusion_roots:
        - clanker.py
        exclusion_roots: []
  - name: debloat
    symbol_set:
      indent: '  '
      arrow_indent: =>
      open_tag: <{tag} {attr}>
      open_tag_no_attr: <{tag}>
      closed_tag: </{tag}>
      self_closing_tag: <{tag} {attr} />
      self_closing_no_attr: <{tag} />
    prompt_fragments:
    - id: general_rules
      type: document
      path: .clanker/assets/general-rules.md
      resolver:
    - id: debloat
      type: document
      path: .clanker/assets/debloat_instructions.md
      resolver:
    - id: script_file_only
      type: file_set
      path:
      resolver:
        sorter: path_asc
        inclusion_roots:
        - clanker.py
        exclusion_roots: []
