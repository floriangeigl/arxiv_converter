from __future__ import print_function
import sys
import os
import shutil
import tex_utils
import traceback
from optparse import OptionParser
from collections import Counter, defaultdict


def replace_figure(orig_plot_fn, out_folder, file_mapping):
    possible_filenames = [orig_plot_fn + i for i in ['', '.pdf', '.png', '.eps']]
    print('plot filename:', end=' ')
    try:
        plot_filename = list(filter(os.path.isfile, possible_filenames))[0]
        print(plot_filename, '->', end=' ')
    except IndexError:
        print(orig_plot_fn, '[FILE NOT FOUND]')
        return None, None
    dest_filename = out_folder + os.path.basename(plot_filename)
    dest_ext = '.' + dest_filename.rsplit('.', 1)[1]
    try:
        dest_filename = file_mapping[plot_filename]
    except KeyError:
        tmp_filename = dest_filename
        counter = 0
        while os.path.isfile(dest_filename):
            counter += 1
            tmp_filename = dest_filename.replace(dest_ext, '') + str(counter).rjust(3,
                                                                                    '0') + dest_ext
        dest_filename = tmp_filename
        file_mapping[plot_filename] = dest_filename
    print('/'.join(dest_filename.rsplit('/', 2)[-2:]), end=' ')
    shutil.copy(plot_filename, dest_filename)
    print('[OK]')
    return plot_filename, os.path.basename(dest_filename).replace(dest_ext, '')


def add_content_of_file(input_filename, output_file, output_folder, file_mapping, var_mapping, complex_cmds,
                        remove_comments=True):
    if not os.path.isfile(input_filename):
        input_filename += '.tex'
    f = tex_utils.FileIter(input_filename)
    for line in f.get_line():
        if r'\newcommand{' not in line and r'\renewcommand{' not in line:
            for var_name, var_val in sorted(var_mapping.iteritems(), key=lambda x: len(x[0]), reverse=True):
                if var_name not in complex_cmds:
                    line = line.replace(var_name, var_val)
        if not line.strip().startswith('%'):
            if '%' in line and remove_comments:
                cleaned_line = list()
                for part in line.split('%'):
                    cleaned_line.append(part)
                    if not part.endswith('\\'):
                        break
                line = '%'.join(cleaned_line)
                line += '%'
                if not line.endswith('\n'):
                    line += '\n'

            line_simple_cmd = tex_utils.simple_cmd_match.findall(line.strip())
            # print(line.strip(), '\n\t->', line_simple_cmd)

            if r'\input{' in line:
                for cmd, import_filename in tex_utils.simple_cmd_match.findall(line):
                    if cmd == 'input':
                        if not remove_comments:
                            output_file.write('%' + '=' * 80 + '\n')
                            output_file.write('%imported external file: ' + import_filename + '\n')
                        print('import external file content:', import_filename)
                        add_content_of_file(import_filename, output_file, output_folder, file_mapping, var_mapping,
                                            complex_cmds, remove_comments=remove_comments)
                        if not remove_comments:
                            output_file.write('%end external file: ' + import_filename + '\n')
                            output_file.write('%' + '=' * 80 + '\n')
                        print('import external file content:', import_filename, '[DONE]')
            elif r'\includegraphics' in line:
                for orig_plot_fn in tex_utils.graphics_cmd_match.findall(line):
                    orig_fn, dest_fn = replace_figure(orig_plot_fn, output_folder, file_mapping)
                    if orig_fn is not None:
                        line = line.replace(orig_plot_fn, dest_fn)
                output_file.write(line)
            elif r'\bibliography{' in line:
                compiled_bibtex_file = input_filename.replace('.tex', '.bbl')
                if not os.path.isfile(compiled_bibtex_file):
                    article_file = input_filename.replace('.tex', '')
                    if not os.path.isfile(input_filename.replace('.tex', '.aux')):
                        print('try compile paper:', end=' ')
                        sys.stdout.flush()
                        if os.system('pdflatex ' + article_file) == 0:
                            print('[OK]')

                        else:
                            print('[FAILED]')
                    print('try compile paper:', end=' ')
                    sys.stdout.flush()
                    if os.system('bibtex ' + article_file) == 0:
                        print('[OK]')
                    else:
                        print('[FAILED]')
                try:
                    if not remove_comments:
                        output_file.write('%' + '=' * 80 + '\n')
                        output_file.write('% bibtex content\n')
                    with open(compiled_bibtex_file, 'r') as bib_f:
                        for bib_line in bib_f:
                            if not bib_line.strip().startswith('%') or not remove_comments:
                                output_file.write(bib_line)
                    if not remove_comments:
                        output_file.write('\n% end bibtex\n')
                        output_file.write('%' + '=' * 80 + '\n')
                except:
                    print(traceback.format_exc())
            elif r'\newcommand{' in line or r'\renewcommand{' in line:
                #print('newcmd line:', line)
                # \newcommand{\varname}{var_val}
                braces_counter = defaultdict(int, Counter(line))
                braces = braces_counter['{'] - braces_counter['}']
                output_file.write(line)
                if braces == 0:
                    for var_name, var_val in tex_utils.newcmd_match.findall(line):
                        var_mapping[var_name] = var_val
                        # print('map var:',var_name, var_val)
                else:
                    tmp_cmd = [line.strip()]
                    cmd_name = line_simple_cmd[0][1]
                    for line in f.get_line():
                        if '%' in line:
                            line = line.split('%', 1)[0] + '%\n'
                            if line.strip() == '%':
                                continue
                        if r'\newcommand{' not in line and r'\renewcommand{' not in line:
                            for var_name, var_val in var_mapping.iteritems():
                                if var_name not in complex_cmds:
                                    line = line.replace(var_name, var_val)
                        output_file.write(line)
                        tmp_cmd += [line.strip()]
                        braces_counter = defaultdict(int, Counter(line))
                        braces += braces_counter['{'] - braces_counter['}']
                        #print('-'*80)
                        #print('line:', line)
                        #print('open braces:', braces)

                        if braces <= 0:
                            break
                    if any(map(lambda x: r'\includegraphics' in x, tmp_cmd)):
                        tmp_cmd = '\n'.join(tmp_cmd[1:-1])
                        #print('new cmd:', cmd_name)
                        #print(tmp_cmd)
                        complex_cmds[cmd_name] = tmp_cmd
            elif len(line_simple_cmd) > 0:
                cmd = "\\" + line_simple_cmd[0][0]
                #print('\tcmd', cmd)
                #print(complex_cmds.keys())
                if cmd in complex_cmds:
                    vars = tex_utils.get_vars(line)
                    cmd = complex_cmds[cmd]
                    #print('ORIG CMD:', cmd)
                    #print('vars:', vars)
                    for idx, var in enumerate(vars):
                        cmd = cmd.replace('#' + str(idx + 1), var)
                    #print('WRITE cmd:', cmd)
                    #print('-'*80)
                    for cmd_line in cmd.split('\n'):
                        for orig_plot_fn in tex_utils.graphics_cmd_match.findall(cmd_line):
                            orig_fn, dest_fn = replace_figure(orig_plot_fn, output_folder, file_mapping)
                            if orig_fn is not None:
                                cmd_line = cmd_line.replace(orig_plot_fn, dest_fn)
                        output_file.write(cmd_line + '\n')
                        #print(cmd_line)
                    #print('-'*80)
                else:
                    output_file.write(line)
            else:
                output_file.write(line)
        elif not remove_comments:
            output_file.write(line)


def main():
    parser = OptionParser()
    parser.add_option("-i", action="store", type="string", dest="inputfile")
    parser.add_option("-o", action="store", type="string", dest="outputfolder", default='')
    parser.add_option("--remove-comments", action="store_true", dest="rm_comments", default=True)
    parser.add_option("--folder-cleanup", action="store_true", dest="folder_cleanup", default=False)
    (options, args) = parser.parse_args()
    paper_filename = options.inputfile
    output_folder = options.outputfolder
    if not output_folder:
        output_filename = os.path.dirname(os.path.abspath(paper_filename)) + '/arxiv_version/' + paper_filename
        output_folder = os.path.dirname(output_filename) + '/'
    else:
        if not output_folder.endswith('/'):
            output_folder += '/'
        output_filename = output_folder + paper_filename
    remove_comments = options.rm_comments
    print('convert:', paper_filename)
    print('outputfolder:', output_folder)
    if os.path.isdir(output_folder) and options.folder_cleanup:
        shutil.rmtree(output_folder)
        os.makedirs(output_folder)
    else:
        os.makedirs(output_folder)
    file_mapping = dict()
    var_mapping = dict()
    complex_cmds = dict()
    with open(output_filename, 'w') as outfile:
        add_content_of_file(paper_filename, outfile, output_folder, file_mapping, var_mapping, complex_cmds, remove_comments=remove_comments)
    for fn in os.listdir(os.path.abspath(os.path.dirname(paper_filename))):
        if fn.endswith(('.sty', '.cls')):
            print('copy', fn, 'to', output_folder)
            shutil.copy(fn, output_folder)


if __name__ == '__main__':
    main()
