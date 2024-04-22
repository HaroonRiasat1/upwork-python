#!/usr/bin/env python3
import subprocess
import sys
import os

python_command = sys.executable
script_to_run = "upwork_job_feed_notifier.py"

# function to invoke the main script
def cron_process():
    print("checking for new notifications...")
    subprocess.Popen([python_command, script_to_run])

logo = """
00000000    0      0    0000000   0000000   0000000000
0 0    0    0      0    0         0             0
0   0  0    0      0    0000000   0000000       0
0     00    0      0    0               0       0
00000000    00000000    0000000   0000000       0                         
                                                                              
"""
print(logo, end="\n\n")

if not os.path.exists("config.json"):
    print("Config File Not Found, Please read README.MD")
    exit()

# Run the cron_process function directly without scheduling
cron_process()
