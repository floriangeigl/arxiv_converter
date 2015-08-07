# arXiv converter
A tiny python2.7 script which tries to convert LaTex projects into arxiv-format. Suggestions are welcome.
## Usage:
```
python arxiv_converter.py -i main_tex_file.tex
```
### Optional parameters:
    -o foldername
        Specify output folder. Default: subfolder of inputfile called "arxiv_version"
    --remove-comments
        Flag. Do not include comments in resulting file. Default: unset
    --folder-cleanup
        Flag. Remove output folder if it exists. Default: unset

