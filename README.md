# kleinanzeigen.de notifier

A Python script that monitors the appearance of new ads in a specified section on www.kleinanzeigen.de.

### Description
A simple script with minimal parameters. To use it, you need to create a .env file with the following variables:
URL - the link to the section of the website you want to monitor.
EXCLUSIONS - keywords in the ad titles, the presence of which will cause the ad to be ignored.
New ads are checked for every 20-40 seconds by default. The script is adapted for use on macOS and utilizes its Notification Center to display notifications (you will need to allow notifications in the Notification Center). You will also need to install [terminal-notifier](https://github.com/julienXX/terminal-notifier).
The script can be run either through an IDE or via the terminal. To run it via the terminal:
- Ensure the first line of the script is #!/usr/bin/python3
- Change the extension of the file to .command (i.e. If the file you want to make executable is called Test.py, change it to Test.command)
- In Terminal make the Python script file executable by running chmod +x Test.command (obviously the Test.command will be whatever your file is from Step 2 above).
By following the above steps, you should be able to double-click your Python script within macOS. It will open a terminal window and run the script.

### Requirements
Python 3.9+
terminal-notifier

### Public availability and terms of usage

NOTE: I did not plan to make this script publicly available, as it was originally written for personal use. Nevertheless, I thought it might be useful to someone else.

WARNING: Use this script at your own risk since usage may violate the terms of kleinanzeigen.de. Sending requests to kleinanzeigen.de too frequently may lead to your blocking on the platform.

Copyright (C) Leon Adler



