#!/usr/bin/python3

import sys, re, json
from collections import defaultdict
import matplotlib
import matplotlib.pyplot as plt


###
### LEXER
###

class Token:
    def __init__(self, name, content = ''):
        self.token_type = name
        self.content = content

    def pr(self):
        return self.token_type + " " + self.content

def lex(characters, token_exprs):
    pos = 0
    tokens = []
    while pos < len(characters):
        match = None
        for token_expr in token_exprs:
            tag, pattern = token_expr
            regex = re.compile(pattern)
            match = regex.match(characters, pos)
            if match:
                text = match.group(0)
                if tag:
                    token = Token(tag, text)
                    tokens.append(token)
                break
        if not match:
            sys.stderr.write('Illegal character: %s\\n' % characters[pos])
            sys.exit(1)
        else:
            pos = match.end(0)
    return tokens

token_dict = []
token_dict.append((None, '#[^\n]*\n'))
token_dict.append(('LBRACKET', '{'))
token_dict.append(('RBRACKET', '}'))
token_dict.append(('SEMICOLON', ';'))
token_dict.append(('PLUSEQUAL', '\+='))
token_dict.append(('EXPORT', '\^='))
token_dict.append(('EQUAL', '='))
token_dict.append(('DIVISION', '/'))
token_dict.append(('SCOPENAME', ':[^\n]*\n'))
token_dict.append(('NAME', '[a-zA-Z][a-zA-Z0-9]*'))
token_dict.append(('VALUE', '\-?[0-9]+'))
token_dict.append((None, '\s+'))

with open(sys.argv[1], 'r') as file:
    tokens = lex(file.read(), token_dict)
    for token in tokens:
        print(token.token_type)

###
### PARSER
###

'''
So, parsing.  As I recall, you want to have a rule that fits everything.  Makes sense.
So, list of rules.  Try each one prospectively?  This seems like it could be recursively nasty.
Take a list of tokens, return success or failure.  Okay, let's do a simple version
Each rule is a list of a mix of rules and terminals.
Also a rule can have multiple productions.
So, structurally: specify dictionary of rule name to list of possible combos.  Each combo is a list of either Rule(name) or Token(name) objects.
'''

class Rule:
    def __init__(self, name):
        self.rule_type = name

    def pr(self):
        return self.rule_type


productions = {}
productions['SCOPE'] = [[Token('LBRACKET'),
                         Token('SCOPENAME'),
                         Rule('EXPRLIST'),
                         Token('RBRACKET')]]
productions['EXPRLIST'] = [[Rule('EXPR'),
                            Rule('EXPRLIST')],
                           [Rule('EXPR')]]
productions['EXPR'] = [[Rule('INCREMENT')],
                       [Rule('SET')],
                       [Rule('SCOPE')],
                       [Rule('EXPORT')]]
productions['INCREMENT'] = [[Token('NAME'),
                             Token('PLUSEQUAL'),
                             Token('VALUE')]]
productions['SET'] = [[Token('NAME'),
                       Token('EQUAL'),
                       Token('VALUE')]]
productions['EXPORT'] = [[Token('NAME'),
                          Token('EXPORT'),
                          Rule('RHS')]]
productions['RHS'] = [[Rule('LOOKUP'),
                       Token('DIVISION'),
                       Rule('LOOKUP')],
                      [Rule('LOOKUP')]]
productions['LOOKUP'] = [[Token('NAME')],
                         [Token('VALUE')]]

class Parse:
    def __init__(self, name, elements):
        self.rule_type = name
        self.elements = elements

def parse_element(token_list, index, element):
    if isinstance(element, Token):
        if element.token_type == token_list[index].token_type:
            return (True, index + 1, Parse(element.token_type, token_list[index]))
        else:
            return (False, -1, [])
    elif isinstance(element, Rule):
        return parse(token_list, index, element.rule_type)
    else:
        print("Invalid rule element", element)
        sys.exit(1)

# do greedy forward parsing
def parse(token_list, index, rule):
    print('Trying rule',rule,'at index', index)
    # try to match this rule starting from this index
    prodcount = 0
    for production in productions[rule]:
        print('Production',prodcount,'for rule',rule,'out of ',len(productions[rule]))
        prodcount += 1
        production_index = index
        success = True
        parse_result = []
        for element in production:
            (success, production_index, parsed) = parse_element(token_list, production_index, element)
            print('Result of',element.pr(),'was ',success)
            if not success: break
            parse_result.append(parsed)
        if success:
            print("Succeeded in matching rule ", rule)
            return (True, production_index, Parse(rule, tuple(parse_result)))
    return (False, -1, [])
                
parse_final = parse(tokens, 0, 'SCOPE')

def print_parse(parse_tree, prefix):
    print(prefix + parse_tree.rule_type)
    for element in parse_tree.elements:
        print_parse(element, prefix + "  ")

#print_parse(parse_final[2], "")

data_store = defaultdict(lambda: defaultdict(float))

def handle_scope(x, s):
    outer_parent = s['PARENT_SCOPE']
    s['PARENT_SCOPE'] = s['SCOPE']
    s['SCOPE'] = x[1].elements.content
    interpret(x[2], s)
    s['SCOPE'] = s['PARENT_SCOPE']
    s['PARENT_SCOPE'] = outer_parent

def handle_increment(x, s):
    data_store[s['SCOPE']][x[0].elements.content] += float(x[2].elements.content)

def handle_set(x, s):
    data_store[s['SCOPE']][x[0].elements.content] = float(x[2].elements.content)

def handle_export(x, s):
    name = x[0].elements.content
    print(x[2].rule_type)
    value = interpret(x[2], s)
    data_store[s['PARENT_SCOPE']][name] += value
    data_store[s['SCOPE']][name] -= value

def handle_exprlist(x, s):
    interpret(x[0], s)
    if (len(x) == 2):
        interpret(x[1], s)

def handle_expr(x, s):
    interpret(x[0], s)

def handle_lookup(x, s):
    if x[0].elements.token_type == 'NAME':
        return data_store[s['SCOPE']][x[0].elements.content]
    elif x[0].elements.token_type == 'VALUE':
        return float(x[0].elements.content)
    else:
        print('Invalid lookup token type', x[0].elements.token_type)
        sys.exit(1)
    
def handle_rhs(x, s):
    if len(x) == 1:
        return interpret(x[0], s)
    elif len(x) == 3:
        numerator = interpret(x[0], s)
        denominator = interpret(x[2], s)
        return numerator / denominator
    else:
        print('Invalid number of arguments in handle rhs')
        sys.exit(1)

def null_handler(x, s):
    pass

parse_handler = defaultdict(lambda: null_handler)
parse_handler['EXPRLIST'] = handle_exprlist
parse_handler['EXPR'] = handle_expr
parse_handler['EXPORT'] = handle_export
parse_handler['INCREMENT'] = handle_increment
parse_handler['SCOPE'] = handle_scope
parse_handler['LOOKUP'] = handle_lookup
parse_handler['RHS'] = handle_rhs


def initial_handle_scope(x, s):
    outer_parent = s['PARENT_SCOPE']
    s['PARENT_SCOPE'] = s['SCOPE']
    s['SCOPE'] = x[1].elements.content
    initial_interpret(x[2], s)
    s['SCOPE'] = s['PARENT_SCOPE']
    s['PARENT_SCOPE'] = outer_parent
    
def initial_handle_exprlist(x, s):
    initial_interpret(x[0], s)
    if (len(x) == 2):
        initial_interpret(x[1], s)

def initial_handle_expr(x, s):
    initial_interpret(x[0], s)

initial_parse_handler = defaultdict(lambda: null_handler)
initial_parse_handler['EXPRLIST'] = initial_handle_exprlist
initial_parse_handler['SET'] = handle_set
initial_parse_handler['SCOPE'] = initial_handle_scope
initial_parse_handler['EXPR'] = initial_handle_expr


###
### INTERPRETER
###

def initial_interpret(parse_tree, state):
    if isinstance(parse_tree, Parse):
        return initial_parse_handler[parse_tree.rule_type](parse_tree.elements, state)

def interpret(parse_tree, state):
    if isinstance(parse_tree, Parse):
        # TODO: can use defaultdict.  Syntax: defaultdict(default)
        return parse_handler[parse_tree.rule_type](parse_tree.elements, state)

base_state = {'PARENT_SCOPE': None, 'SCOPE': None}

scoped_values = defaultdict(lambda: [])
initial_interpret(parse_final[2], base_state)
print(data_store)
for i in range(0, int(sys.argv[2])):
    interpret(parse_final[2], base_state)
    for scope in data_store:
        for value in data_store[scope]:
            full_name = "%s:%s" % (scope, value)
            scoped_values[full_name].append(data_store[scope][value])
print(data_store)
print(scoped_values)

x = range(0, int(sys.argv[2]))
for value in scoped_values:
    plt.plot(x, scoped_values[value], label = value)
    
plt.legend(loc='upper left')
plt.xlabel('iteration')
plt.show()
