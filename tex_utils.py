import re

simple_cmd_match = re.compile(r'\\([^\\]+?)\{(.*?)\}')
graphics_cmd_match = re.compile(r'\\includegraphics\[.*?\]?\{(.*?)\}')
begin_cmd_match = re.compile(r'\\begin{([^}]+?)}(?:(?:\[([^\]]+?)\])|.*)')


class FileIter:
    def __init__(self, filename):
        self.fn = filename
        self.f = open(self.fn, 'r')

    def get_line(self):
        for line in self.f:
            yield line
        self.f.close()

