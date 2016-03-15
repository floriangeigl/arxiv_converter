import re

simple_cmd_match = re.compile(r'\\([^\\]+?)\{(.*?)\}')
graphics_cmd_match = re.compile(r'\\includegraphics\[.*?\]?\{(.*?)\}')
begin_cmd_match = re.compile(r'\\begin{([^}]+?)}(?:(?:\[([^\]]+?)\])|.*)')
newcmd_match = re.compile(r'\\.+?\{(.*?)\}\{(.*)\}')
# newcmd_match_with_var = re.compile(r'\\[^\\]+?\{(.*?)\}\{(.*?)\}')
vars_match = re.compile(r'\{(.+?)\}')


def get_vars(line):
    res = list()
    open_braces = 0
    one_var = ''
    for char in line.strip():
        if char == '}':
            open_braces -= 1
        if open_braces > 0:
            one_var += char
        elif open_braces == 0 and one_var:
            res.append(one_var)
            one_var = ''
        if char == '{':
            open_braces += 1
    return res

class FileIter:
    def __init__(self, filename):
        self.fn = filename
        self.f = open(self.fn, 'r')

    def get_line(self):
        for line in self.f:
            yield line
        self.f.close()

