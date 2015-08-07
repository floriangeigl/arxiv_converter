# arXiv converter
A tiny python2.7 script which tries to convert LaTex projects into arXiv-format. Suggestions are welcome. 

## Tasks:
* The script creates an output folder,
* parses the input file and generates a new one in the output folder where it:
    * inserts the content of all imports (e.g., \import{foo}),
    * copies all graphics (e.g., \includegraphics{graphic}) source files into the same folder (enumerate them if two or more have the same name) and replaces the filename in the LaTex file with the new one.
    * Finally, it inserts the content of the .bbl file as bibliography (if the .bbl does not exist, it tries to compile it)

## Usage:
```
python arxiv_converter.py -i main_tex_file.tex
```
### Optional parameters:
    -o foldername
        Specify output folder. Default: subfolder of input file called "arxiv_version"
    --remove-comments
        Flag. Do not include comments. Default: unset
    --folder-cleanup
        Flag. Remove output folder if it exists. Default: unset

