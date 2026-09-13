from dataclasses import dataclass

@dataclass
class KbSpec:
    shared_domain_keys: str
    pud_domain_keys: str
    prompt_keys: str