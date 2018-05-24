#!/usr/bin/python3

###
### LEXER
###

import re, sys

class Token:
    def __init__(self, name, content = ''):
        self.token_type = name
        self.content = content

    def pr(self):
        return self.token_type + " " + self.content

def lex(characters):
    pos = 0
    tokens = []
    while pos < len(characters):
        match = None
        for token_expr in token_dict:
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
token_dict.append(('LPAREN', '\('))
token_dict.append(('RPAREN', '\)'))
token_dict.append(('SEMICOLON', ';'))
token_dict.append(('PLUSEQUAL', '\+='))
token_dict.append(('EXPORT', '\^='))
token_dict.append(('IMPORT', 'v='))
token_dict.append(('EQUAL', '='))
token_dict.append(('ARITHMETIC', '[/\*\+\-]'))
token_dict.append(('SCOPENAME', ':[^\n]*\n'))
token_dict.append(('NAME', '[a-zA-Z][a-zA-Z0-9]*'))
token_dict.append(('VALUE', '\-?[0-9]+'))
token_dict.append((None, '\s+'))
