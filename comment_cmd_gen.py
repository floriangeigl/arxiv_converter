from __future__ import print_function
import sys

# create easy to use comment tags for latex documents
# usage: python comment_cmd_gen.py name1 name2 name3
# copy output into your latex document
name_tags = sorted(sys.argv[1:])
print('% comment cmds')
for name_tag in name_tags:
    print('\\newcounter{' + name_tag + 'counter}')
    print('\\DeclareRobustCommand{\\' + name_tag + '}[1]{\\textbf{/* #1 (' + name_tag + ') */}'
        '\\stepcounter{' + name_tag + 'counter}'
        '\\typeout{LaTeX Warning: ' + name_tag + ' comment \\the' + name_tag + 'counter}}')
print('% comment toggle. change to \\iftrue to hide comments\n\\iffalse')
for name_tag in name_tags:
    print('\t\\renewcommand{\\' + name_tag + '}[1]{}')
print('\\fi')
