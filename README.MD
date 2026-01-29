# Automatic File Manager

A simple way to automate working with files. You can set a time delay for automatic execution of your command. For example:
    
    python fileManager.py move ./Downloads/ ./Videos -p .mp4 .MP4 .mov .MOV -r -s 60
This command will move all files with .mp4 .MP4 .mov .MOV from Downloads to the Videos directory, check the Downloads directory again and do task one more time until there is no files that match patterns in Downloads, then FileManager will be waiting for 60 seconds and check Downloads again.

if you don’t want the command works in a cycle, just don't use "-r" argument. And it will be executed for one time.


## Available commands
- **move** - move files from source directory to target directory
- **slice** - slice video files to images from the source directory to the target directory. Also, you can set flag "--remove" or "-rm" for deleting a source video file after slicing
- **delete** - delete files that match patterns from source directory
- **dedup** - find duplicates in source directory that matches a pattern. An image means a duplicate if it's hash has lower 
Hamming distance with comparing image hash than threshold value. The threshold value setups in percentage and must be in range [0, 100]. Pay attention to core_size parameter: the lower value makes details at photo less important, and the higher value makes details mach important while comparing information at images. It’s implemented only dHash comparing method for now.
- **clean-annotations** - find annotation files in directory that doesn't have corresponding files
## How to use:
clone git repository:

    git clone https://github.com/SeregaCodit/AutoFileManager.git

go to project directory:

    cd path_to_project
    
create virtual environment and activate it:
    
    python -m venv .venv
    
install requirements :
    
    pip install -r requirements.txt
    
read the --help command for learn more about available commands and arguments:
    
for check available commands

    python fileManager.py --help 

for check the command usage and available arguments

    python fileManager.py {command} --help


## What else?

For more comfortable using FileManager with multiple tasks you can create an .sh file or modify [strat_all_tasks.sh](https://github.com/SeregaCodit/AutoFileManager/blob/main/strat_all_tasks.sh) with list of your commands. And run all of them just by one simple command:

    bash path_to_file/start_all_tasks.sh

for stop executing of all commands use:

    pkill -f fileManager.py

