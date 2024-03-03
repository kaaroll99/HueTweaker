#!/bin/bash
git fetch 
git pull 
echo "Do you want to continue? (y/n)" 
read -r continue_run 
if [ "$continue_run" = "y" ]; then 
    python3 main_sb.py 
else
    echo "Cancelled"
fi
