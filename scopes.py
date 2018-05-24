#!/usr/bin/python3

import sys, json
from collections import defaultdict
import matplotlib
import matplotlib.pyplot as plt
import lexer, parser, interpreter

# lex

with open(sys.argv[1], 'r') as file:
    tokens = lexer.lex(file.read())
    for token in tokens:
        print(token.token_type)

# parse

parse_final = parser.parse(tokens, 0, 'SCOPE')
parser.print_parse(parse_final[2], "")

# interpret

data_store = defaultdict(lambda: defaultdict(float))

scoped_values = defaultdict(lambda: [])
interpreter.interpret_initial(parse_final[2], data_store)
for i in range(0, int(sys.argv[2])):
    interpreter.interpret_live(parse_final[2], data_store)
    for scope in data_store:
        for value in data_store[scope]:
            full_name = "%s:%s" % (scope, value)
            scoped_values[full_name].append(data_store[scope][value])

x = range(0, int(sys.argv[2]))
for value in scoped_values:
    plt.plot(x, scoped_values[value], label = value)
    
plt.legend(loc='upper left')
plt.xlabel('iteration')
plt.show()
