#!/usr/bin/python3

import sys, copy
from collections import defaultdict
from parser import Parse

class Scope:
    def __init__(self, stack):
        self.stack = stack

    def push(self, scope):
        self.stack.append(scope)

    def pop(self):
        return self.stack.pop()

    def create_parent(self): 
        parent_scope = Scope(list(self.stack))
        parent_scope.stack.pop()
        return parent_scope
   
    def parent_scope(self):
        return self.stack[-2]

    def scope(self):
        return self.stack[-1]

def handle_scope(x, s, d, od, ph):
    s.push(x[1].elements.content)
    interpret(x[2], s, d, od, ph)
    s.pop()

def handle_increment(x, s, d, od, ph):
    d[s.scope()][x[0].elements.content] += float(x[2].elements.content)

def handle_set(x, s, d, od, ph):
    d[s.scope()][x[0].elements.content] = float(x[2].elements.content)

def handle_export(x, s, d, od, ph):
    name = x[0].elements.content
    value = interpret(x[2], s, d, od, ph)
    d[s.parent_scope()][name] += value
    d[s.scope()][name] -= value

def handle_import(x, s, d, od, ph):
    name = x[0].elements.content
    value = interpret(x[2], s.create_parent(), d, od, ph)
    d[s.parent_scope()][name] -= value
    d[s.scope()][name] += value

def handle_exprlist(x, s, d, od, ph):
    interpret(x[0], s, d, od, ph)
    if (len(x) == 2):
        interpret(x[1], s, d, od, ph)

def handle_expr(x, s, d, od, ph):
    interpret(x[0], s, d, od, ph)

def handle_group(x, s, d, od, ph):
    return interpret(x[1], s, d, od, ph)

def handle_lookup(x, s, d, od, ph):
    if x[0].rule_type == 'GROUP':
        return interpret(x[0], s, d, od, ph)
    elif x[0].elements.token_type == 'NAME':
        return d[s.scope()][x[0].elements.content]
    elif x[0].elements.token_type == 'VALUE':
        return float(x[0].elements.content)
    else:
        print('Invalid lookup token type', x[0].elements.token_type)
        sys.exit(1)

arithmetic_op = {}
arithmetic_op['+'] = lambda l, r: l + r
arithmetic_op['-'] = lambda l, r: l - r
arithmetic_op['*'] = lambda l, r: l * r
arithmetic_op['/'] = lambda l, r: l / r

def handle_rhs(x, s, d, od, ph):
    if len(x) == 1:
        return interpret(x[0], s, od, od, ph)
    elif len(x) == 3:
        left = interpret(x[0], s, od, od, ph)
        right = interpret(x[2], s, od, od, ph)
        return arithmetic_op[x[1].elements.content](left, right)
    else:
        print('Invalid number of arguments in handle rhs')
        sys.exit(1)

def null_handler(x, s, d, od, ph):
    pass

parse_handler = defaultdict(lambda: null_handler)
parse_handler['EXPRLIST'] = handle_exprlist
parse_handler['EXPR'] = handle_expr
parse_handler['EXPORT'] = handle_export
parse_handler['IMPORT'] = handle_import
parse_handler['INCREMENT'] = handle_increment
parse_handler['SCOPE'] = handle_scope
parse_handler['LOOKUP'] = handle_lookup
parse_handler['RHS'] = handle_rhs
parse_handler['GROUP'] = handle_group

initial_parse_handler = defaultdict(lambda: null_handler)
initial_parse_handler['EXPRLIST'] = handle_exprlist
initial_parse_handler['SET'] = handle_set
initial_parse_handler['SCOPE'] = handle_scope
initial_parse_handler['EXPR'] = handle_expr


###
### INTERPRETER
###

def interpret(parse_tree, state, d, od, ph):
    if isinstance(parse_tree, Parse):
        return ph[parse_tree.rule_type](parse_tree.elements, state, d, od, ph)

def interpret_live(parse_tree, data_store):
    base_state = Scope([None, None])
    old_data_store = copy.deepcopy(data_store)
    interpret(parse_tree, base_state, data_store,
              old_data_store, parse_handler)

def interpret_initial(parse_tree, data_store):
    base_state = Scope([None, None])
    old_data_store = copy.deepcopy(data_store)
    interpret(parse_tree, base_state, data_store,
              old_data_store, initial_parse_handler)
