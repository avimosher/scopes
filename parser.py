#!/usr/bin/python3

import sys
from lexer import Token

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
                       [Rule('EXPORT')],
                       [Rule('IMPORT')]]
productions['INCREMENT'] = [[Token('NAME'),
                             Token('PLUSEQUAL'),
                             Token('VALUE')]]
productions['SET'] = [[Token('NAME'),
                       Token('EQUAL'),
                       Token('VALUE')]]
productions['EXPORT'] = [[Token('NAME'),
                          Token('EXPORT'),
                          Rule('RHS')]]
productions['IMPORT'] = [[Token('NAME'),
                          Token('IMPORT'),
                          Rule('RHS')]]
productions['RHS'] = [[Rule('LOOKUP'),
                       Token('ARITHMETIC'),
                       Rule('LOOKUP')],
                      [Rule('LOOKUP')]]
productions['LOOKUP'] = [[Token('NAME')],
                         [Token('VALUE')],
                         [Rule('GROUP')],
                         [Rule('RHS')]]
productions['GROUP'] = [[Token('LPAREN'),
                         Rule('RHS'),
                         Token('RPAREN')]]

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

def print_parse(parse_tree, prefix):
    if isinstance(parse_tree.elements, Token):
        print(prefix + parse_tree.rule_type)
        return
    print(prefix + parse_tree.rule_type)
    for element in parse_tree.elements:
        print_parse(element, prefix + "  ")
