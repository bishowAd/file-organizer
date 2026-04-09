Smart File Organizer
A Python script that instantly sorts messy folders into clean, categorized subfolders.
What It Does
Scans a folder and moves files into subfolders based on type: Images, Documents, Code, Videos, Audio, Spreadsheets, Presentations, Archives, Executables, Data, eBooks, Fonts, and 3D/CAD. Anything unrecognized goes into "Other."
Usage
bash# Organize your Downloads folder
python organize_files.py

# Organize a specific folder
python organize_files.py --folder desktop
python organize_files.py --path "D:/MyFolder"

# Preview changes without moving anything
python organize_files.py --dry-run

# Include files in subfolders
python organize_files.py --recursive

# Reverse the last run
python organize_files.py --undo
Features

Dry run mode to preview before committing
Undo support with a saved log to reverse all changes
Duplicate handling by appending _1, _2, etc.
Recursive mode to organize nested folders
Skips system files like desktop.ini and thumbs.db
No dependencies — runs on pure Python

Supported Folder Shortcuts
downloads | desktop | documents | pictures | music | videos
Requirements
Python 3.6+
