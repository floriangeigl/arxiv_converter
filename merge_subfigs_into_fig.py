from __future__ import print_function
import sys
import os
import shutil
import re
import traceback
from optparse import OptionParser


simple_cmd_match = re.compile(r'\\([^\\]+?)\{(.*?)\}')

class FileIter:
    def __init__(self, filename):
        self.fn = filename
        self.f = open(self.fn, 'r')

    def get_line(self):
        for line in self.f:
            if not line.strip().startswith('%'):
                yield line
        self.f.close()


def update_refs(line, ref_to_outpref):
    for cmd, content in simple_cmd_match.findall(line):
        if cmd == 'ref' and content.startswith('fig:'):
            try:
                line = line.replace('\\ref{' + content + '}', '\\ref{' + ref_to_outpref[content] + '}')
            except:
                pass
    return line


def main():
    parser = OptionParser()
    parser.add_option("-i", action="store", type="string", dest="inputfile")
    parser.add_option("--outprefix", action="store", type="string", dest="outprefix", default='Fig')
    (options, args) = parser.parse_args()
    paper_filename = options.inputfile
    outprefix = options.outprefix
    ref_to_outpref = dict()

    project_folder = paper_filename.rsplit('/', 1)[0] + '/' if '/' in paper_filename else './'

    tmp_folder = project_folder + 'plos_one/'
    if not os.path.isdir(tmp_folder):
        os.makedirs(tmp_folder)
    output_filename = tmp_folder + paper_filename.rsplit('/', 1)[-1].replace('.tex', '_plosone.tex')
    custom_commands = ''

    f_iter = FileIter(paper_filename)
    with open(paper_filename, 'r') as f:
        for idx, line in enumerate(f):
            for cmd, content in simple_cmd_match.findall(line):
                if cmd == 'ref' and content.startswith('fig:'):
                    print('line', idx + 1, ':', cmd, content)
                    if content not in ref_to_outpref:
                        ref_to_outpref[content] = outprefix + str(len(ref_to_outpref) + 1)
                elif cmd == 'newcommand':
                    custom_commands += line
    print('Found fig refs:')
    for key, val in sorted(ref_to_outpref.iteritems(), key=lambda x: int(x[1].replace(outprefix, ''))):
        print(key, '->', val)

    with open(output_filename, 'w') as outf:
        for line in f_iter.get_line():
            line = update_refs(line, ref_to_outpref)
            strip_line = line.strip()

            if strip_line.startswith(r'\begin{figure'):
                fig_text = '\\documentclass{article}\n'
                fig_text += '\\usepackage[utf8]{inputenc}\n'
                fig_text += '\\usepackage{graphicx}\n'
                fig_text += '\\usepackage{subfig}\n'
                fig_text += '\\usepackage{bm}\n'
                fig_text += custom_commands
                fig_text += '\\begin{document}\n'
                fig_text += '\\thispagestyle{empty}\n'
                fig_text += line
                outf.write(line)
                fig_ref = None
                for line in f_iter.get_line():
                    strip_line = line.strip()
                    if strip_line.startswith(r'\caption{'):
                        line = update_refs(line, ref_to_outpref)
                        outf.write(line)
                    else:
                        fig_text += line
                    if strip_line.startswith(r'\label{'):
                        _, fig_ref = filter(lambda x: x[0] == 'label', simple_cmd_match.findall(line))[0]
                        fig_ref = ref_to_outpref[fig_ref]
                        outf.write(r'\label{' + fig_ref + '}\n')
                    if strip_line.startswith(r'\end{figure'):
                        outf.write(line)
                        print('compile fig:', fig_ref)
                        fig_tex_file = project_folder + fig_ref + '.tex'
                        fig_pdf_file = project_folder + fig_ref + '.pdf'
                        fig_text += '\\end{document}'
                        with open(fig_tex_file, 'w') as f:
                            f.write(fig_text)
                        os.system('cd ' + project_folder + ' && pdflatex ' + fig_tex_file.rsplit('/', 1)[
                            -1] + ' 2>&1 >> /dev/null')
                        os.system('pdfcrop ' + fig_pdf_file + ' ' + fig_pdf_file + ' 2>&1 >> /dev/null')
                        shutil.move(fig_pdf_file, tmp_folder + fig_pdf_file.rsplit('/', 1)[-1])
                        os.system('rm ' + fig_pdf_file.replace('.pdf', '') + '*')
                        break
            else:
                outf.write(line)

if __name__ == '__main__':
    main()

