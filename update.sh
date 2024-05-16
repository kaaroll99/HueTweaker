#!/bin/bash
git fetch
git pull
echo "Do you want to continue? (y/n)"
read -r continue_run
if [ "$continue_run" = "y" ]; then
    while [ true ]; do
        echo "Starting Bot ..."
        python3 main_sb.py
        echo "Bot crashed ... Restarting in 5 seconds..."
        sleep 5
    done
else
    echo "Cancelled"
fi





