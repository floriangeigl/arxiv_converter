from __future__ import print_function
import sys
import os
import shutil
import tex_utils
import traceback
from optparse import OptionParser


def add_content_of_file(input_filename, output_file, output_folder, file_mapping, remove_comments=True):
    if not os.path.isfile(input_filename):
        input_filename += '.tex'
    with open(input_filename, 'r') as f:
        for line in f:
            if not line.strip().startswith('%'):
                if '%' in line and remove_comments:
                    cleaned_line = list()
                    for part in line.split('%'):
                        cleaned_line.append(part)
                        if not part.endswith('\\'):
                            break
                    line = '%'.join(cleaned_line)
                    if not line.endswith('\n'):
                        line += '\n'

                if r'\input{' in line:
                    for cmd, import_filename in tex_utils.simple_cmd_match.findall(line):
                        if cmd == 'input':
                            if not remove_comments:
                                output_file.write('%' + '=' * 80 + '\n')
                                output_file.write('%imported external file: ' + import_filename + '\n')
                            print('import external file content:', import_filename)
                            add_content_of_file(import_filename, output_file, output_folder, file_mapping,
                                                remove_comments=remove_comments)
                            if not remove_comments:
                                output_file.write('%end external file: ' + import_filename + '\n')
                                output_file.write('%' + '=' * 80 + '\n')
                            print('import external file content:', import_filename, '[DONE]')
                elif r'\includegraphics' in line:
                    for used_plot_filename in tex_utils.graphics_cmd_match.findall(line):
                        possible_filenames = [used_plot_filename + i for i in ['', '.pdf', '.png', '.eps']]
                        print('plot filename:', end=' ')
                        try:
                            plot_filename = list(filter(os.path.isfile, possible_filenames))[0]
                            print(plot_filename, '->', end=' ')
                        except IndexError:
                            print(used_plot_filename, '[FILE NOT FOUND]')
                            continue
                        dest_filename = output_folder + os.path.basename(plot_filename)
                        dest_ext = '.' + dest_filename.rsplit('.', 1)[0]
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
                        output_file.write(
                            line.replace(used_plot_filename, os.path.basename(dest_filename).replace(dest_ext, '')))
                        print('[OK]')
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
    with open(output_filename, 'w') as outfile:
        add_content_of_file(paper_filename, outfile, output_folder, file_mapping, remove_comments=remove_comments)
    for fn in os.listdir(os.path.abspath(os.path.dirname(paper_filename))):
        if fn.endswith(('.sty', '.cls')):
            print('copy', fn, 'to', output_folder)
            shutil.copy(fn, output_folder)


if __name__ == '__main__':
    main()
