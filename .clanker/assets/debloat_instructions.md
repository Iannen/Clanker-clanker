
# Objective
Refactor and optimize `clanker.py` to minimize token overhead, reclaim vertical space, and eliminate technical debt while strictly maintaining 100% behavioral parity and API compatibility.

# known enemies
1. redundant declaration:
'''ex.1 - wrong
def action(self, arg):
    member = arg.member
    return member * 2
'''
'''ex.1 - correct
def action(self, arg):
    return arg.member * 2
'''
2. inline comments, like '# ... '
3. dead code
4. opportunities for consolidation
# operational instruction
    - perform a silent analysis, and then return

1. list of candidates for review. format:
    - known enemies 1 candidates
        1. ...
        2. 
    - known enemies 2 ...

the list represents a recommendation from you to me, for how I might win back some tokens in my codebase.