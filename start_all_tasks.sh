#!/bin/bash
# simple running multiple commands

FILE_MANAGER_PATH={path_to_filemanager}
# activate venv
source .venv/bin/activate

echo "File Manager running ...."

# Task 1
python  $FILE_MANAGER_PATH {command} {positional_arguments} {named_arguments} &
echo "Task 1 {task description} started with PID $!"

# Task 2
python $FILE_MANAGER_PATH {command} {positional_arguments} {named_arguments} &
echo "Task 2 {task description} started with PID $!"

echo "All tasks was running. Use 'pkill -f fileManager.py' for stop"

## Optional: wait for all processes ending
#wait