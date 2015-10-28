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

def find_files(base_dir, file_ending):
    res = list()
    for root, dirs, files in os.walk(base_dir):
        if not root.endswith('/'):
            root += '/'
        res.extend([root + i for i in filter(lambda x: x.endswith(file_ending), files)])
    return sorted(res)


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
    parser.add_option("--figureprefix", action="store", type="string", dest="figureprefix", default='Fig')
    (options, args) = parser.parse_args()
    paper_filename = options.inputfile
    figureprefix = options.figureprefix
    ref_to_outpref = dict()
    ref_to_caption = dict()

    needed_files = ['PLOS-submission-eps-converted-to.pdf', 'PLOS-submission.eps']

    project_folder = paper_filename.rsplit('/', 1)[0] + '/' if '/' in paper_filename else './'

    tmp_folder = project_folder + 'PLOS_submission/'
    if not os.path.isdir(tmp_folder):
        os.makedirs(tmp_folder)
    output_filename = tmp_folder + paper_filename.rsplit('/', 1)[-1]
    custom_commands = ''

    f_iter = FileIter(paper_filename)
    with open(paper_filename, 'r') as f:
        for idx, line in enumerate(f):
            for cmd, content in simple_cmd_match.findall(line):
                if cmd == 'ref' and content.startswith('fig:'):
                    print('line', idx + 1, ':', cmd, content)
                    if content not in ref_to_outpref:
                        ref_to_outpref[content] = figureprefix + str(len(ref_to_outpref) + 1)
                elif cmd == 'newcommand':
                    custom_commands += line
    print('Found fig refs:')
    for key, val in sorted(ref_to_outpref.iteritems(), key=lambda x: int(x[1].replace(figureprefix, ''))):
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
                # outf.write(line)
                fig_ref = None
                outf_text = line
                for line in f_iter.get_line():
                    strip_line = line.strip()
                    if strip_line.startswith(r'\caption{'):
                        line = update_refs(line, ref_to_outpref)
                        outf_text += line
                    else:
                        fig_text += line
                    if strip_line.startswith(r'\label{'):
                        _, fig_ref = filter(lambda x: x[0] == 'label', simple_cmd_match.findall(line))[0]
                        fig_ref = ref_to_outpref[fig_ref]
                        outf_text += '\t\\label{' + fig_ref + '}\n'
                    if strip_line.startswith(r'\end{figure'):
                        outf_text += line
                        outf_text = outf_text.replace('\\caption', '%\\includegraphics[width=.99\columnwidth]{' + fig_ref + '}'
                                                                                                                '\n\t\\caption')
                        # outf.write(outf_text)
                        ref_to_caption[fig_ref] = outf_text
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
    print('copy (maybe) needed additional files to tmp folder')
    additional_files = find_files(project_folder, ('.sty', '.cls', '.bib', '.bst'))
    for af in additional_files:
        if not af.startswith(tmp_folder):
            shutil.copy(af, tmp_folder + af.rsplit('/', 1)[-1])

    for f in needed_files:
        try:
            shutil.copy(project_folder + f, tmp_folder + f)
        except:
            pass

    print('place figure captions')
    ref_to_outpref
    outpref_to_ref = {val: key for key, val in ref_to_outpref.iteritems()}
    tmp_filename = '/tmp/merge_subfigs_tmp.tex'
    inserted_figures = set()
    with open(output_filename, 'r') as f:
        with open(tmp_filename, 'w') as fo:
            figures_after_break = list()
            for line in f:
                fo.write(line)
                for cmd, content in simple_cmd_match.findall(line):
                    if cmd == 'ref' and content.startswith(figureprefix):
                        figures_after_break.append(content)
                if line.strip() == '' and figures_after_break:
                    for fig in figures_after_break:
                        if fig not in inserted_figures:
                            fo.write('% ' + (' begin ' + fig + ' ').center(80, '*') + '\n')
                            try:
                                fo.write(ref_to_caption[fig])
                            except KeyError:
                                print('WARNING: Figure to ref ', fig, 'not found!')
                                fo.write('% ' + fig + ' ( ' + outpref_to_ref[
                                    fig] + ' ) not found! Maybe unresolved ref in input file?\n')
                            fo.write('% ' + (' end ' + fig + ' ').center(80, '*') + '\n')
                            fo.write('\n')
                            inserted_figures.add(fig)
                    figures_after_break = list()

    shutil.move(tmp_filename, output_filename)

    print('compile paper:', output_filename)
    os.system('cd ' + tmp_folder + ' && pdflatex ' + output_filename.rsplit('/', 1)[-1])
    os.system('cd ' + tmp_folder + ' && bibtex ' + output_filename.rsplit('/', 1)[-1].replace('.tex', ''))
    tmp_filename = '/tmp/merge_subfigs_tmp.tex'
    last_line_empty = False
    with open(output_filename, 'r') as f:
        with open(tmp_filename, 'w') as fo:
            for line in f:
                strip_line = line.strip()
                if strip_line.startswith('\\bibliography{'):
                    with open(output_filename.replace('.tex', '.bbl'), 'r') as bf:
                        for b_line in bf:
                            fo.write(b_line)
                elif strip_line == '':
                    if not last_line_empty:
                        last_line_empty = True
                        fo.write(line)
                    continue
                else:
                    fo.write(line)
                last_line_empty = False
    shutil.move(tmp_filename, output_filename)
    os.system('cd ' + tmp_folder + ' && pdflatex ' + output_filename.rsplit('/', 1)[-1])


if __name__ == '__main__':
    main()

