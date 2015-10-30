from __future__ import print_function
import os
import shutil
import tex_utils
from optparse import OptionParser


def find_files(base_dir, file_ending):
    if not base_dir.endswith('/'):
        base_dir += '/'
    res = [base_dir + i for i in os.listdir(base_dir)]
    return sorted(filter(lambda x: x.endswith(file_ending), res))


def update_refs(line, ref_to_outpref):
    for cmd, content in tex_utils.simple_cmd_match.findall(line):
        if cmd == 'ref' and content.startswith('fig:'):
            try:
                line = line.replace('\\ref{' + content + '}', '\\ref{' + ref_to_outpref[content] + '}')
            except:
                pass
    return line


def main():
    # parse args
    parser = OptionParser()
    parser.add_option("-i", action="store", type="string", dest="inputfile")
    parser.add_option("--figureprefix", action="store", type="string", dest="figureprefix", default='Fig')
    (options, args) = parser.parse_args()
    paper_filename = options.inputfile
    figureprefix = options.figureprefix
    ref_to_outpref = dict()
    ref_to_caption = dict()
    tmp_filename = '/tmp/merge_subfigs_tmp.tex'

    files_to_copy = ['PLOS-submission-eps-converted-to.pdf', 'PLOS-submission.eps']

    # create output folder
    project_folder = paper_filename.rsplit('/', 1)[0] + '/' if '/' in paper_filename else './'
    tmp_folder = project_folder + 'PLOS_submission/'
    if not os.path.isdir(tmp_folder):
        os.makedirs(tmp_folder)
    output_filename = tmp_folder + paper_filename.rsplit('/', 1)[-1]

    # go over input file and find ref to figures
    # also collect all newcommands to be later able to add them to the figure tex files.
    # (just in case those commands are just in the figure)
    custom_commands = ''
    with open(paper_filename, 'r') as f:
        with open(output_filename, 'w') as outf:
            for idx, line in enumerate(f):
                for cmd, content in tex_utils.simple_cmd_match.findall(line):
                    if cmd == 'ref' and content.startswith('fig:'):
                        print('line', idx + 1, ':', cmd, content)
                        if content not in ref_to_outpref:
                            ref_to_outpref[content] = figureprefix + str(len(ref_to_outpref) + 1)
                    elif cmd == 'newcommand':
                        custom_commands += line
                    elif cmd == 'input':
                        content = paper_filename.rsplit('/', 1)[0] + '/' + content
                        if not os.path.isfile(content):
                            content += '.tex'
                        if os.path.isfile(content):
                            line = '% ' + '*' * 80 + '\n'
                            line += '% imported content of external file: ' + content.rsplit('/', 1)[-1] + '\n'
                            with open(content, 'r') as input_file:
                                for l in input_file:
                                    line += l
                            line += '% ' + '*' * 80 + '\n'
                outf.write(line)
    print('*' * 80)
    print('Found fig refs:')
    for key, val in sorted(ref_to_outpref.iteritems(), key=lambda x: int(x[1].replace(figureprefix, ''))):
        print('\t', key, '->', val)
    print('*' * 80)

    # merge subfigures into one figure
    # -> extract content of figure commands (no caption) and compile them to one file.
    f_iter = tex_utils.FileIter(output_filename)
    with open(tmp_filename, 'w') as outf:
        for line in f_iter.get_line():
            line = update_refs(line, ref_to_outpref)
            strip_line = line.strip()

            # found begin of figure
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
                fig_ref = None
                outf_text = line
                for line in f_iter.get_line():
                    strip_line = line.strip()

                    # write caption to plos one latex document
                    if strip_line.startswith(r'\caption{'):
                        line = update_refs(line, ref_to_outpref)
                        outf_text += line

                    # write the rest to the figure tex file
                    else:
                        fig_text += line

                    # fix label to match new figure reference
                    if strip_line.startswith(r'\label{'):
                        _, fig_ref = filter(lambda x: x[0] == 'label', tex_utils.simple_cmd_match.findall(line))[0]
                        fig_ref = ref_to_outpref[fig_ref]
                        outf_text += '\t\\label{' + fig_ref + '}\n'

                    # end of figure found.
                    # -> compile figure content to a single pdf (filename starting with figureprefix) and crop it.
                    # -> insert caption with new ref into the plos one latex document.
                    #    (including a commented includegraphics cmd)
                    if strip_line.startswith(r'\end{figure'):
                        outf_text += line
                        outf_text = outf_text.replace('\\caption', '%\\includegraphics[width=.99\columnwidth]{' + fig_ref + '}'
                                                                                                                '\n\t\\caption')
                        ref_to_caption[fig_ref] = outf_text
                        print('compile figure:', fig_ref)
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
            # no figure content -> just write unmodified line to plos one latex document.
            else:
                outf.write(line)
    shutil.move(tmp_filename, output_filename)

    # copy additional files like files (e.g., style files like .sty,...) to output folder
    print('copy (maybe) needed additional files to tmp folder')
    additional_files = find_files(project_folder, ('.sty', '.cls', '.bib', '.bst'))
    for af in additional_files:
        shutil.copy(af, tmp_folder + af.rsplit('/', 1)[-1])

    # copy further needed files to output folder (e.g., plos one logo)
    for f in files_to_copy:
        try:
            shutil.copy(project_folder + f, tmp_folder + f)
        except:
            pass

    # figures captions should be placed after the paragraph they were first referenced in the plos one latex document.
    # -> go over plos one file, find reference to figures and insert their captions after the paragraph.
    print('place figure captions')
    outpref_to_ref = {val: key for key, val in ref_to_outpref.iteritems()}
    inserted_figures = set()
    with open(output_filename, 'r') as f:
        with open(tmp_filename, 'w') as fo:
            figures_after_break = list()
            for line in f:
                fo.write(line)
                for cmd, content in tex_utils.simple_cmd_match.findall(line):
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

    # compile the paper and bibtex. insert content of .bbl into the plos one latex document.
    #   (replacing the \bibliography command)
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

    # finally compile the plos one latex document.
    os.system('cd ' + tmp_folder + ' && pdflatex ' + output_filename.rsplit('/', 1)[-1])


if __name__ == '__main__':
    main()

