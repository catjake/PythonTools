#!/usr/bin/env python
import sys
import os

# Configure your favorite diff program here.
DIFF = "/usr/bin/gvimdiff"

# Subversion provides the paths we need as the last two parameters.
LEFT  = sys.argv[-2]
RIGHT = sys.argv[-1]
print "LEFT: {0}, RIGHT: {1}".format(LEFT,RIGHT)
# Call the diff command (change the following line to make sense for
# your diff program).
# cmd = [DIFF, '--left', LEFT, '--right', RIGHT]
cmd = [DIFF, "--nofork", LEFT, RIGHT]
os.execv(cmd[0], cmd)

# Return an errorcode of 0 if no differences were detected, 1 if some were.
# Any other errorcode will be treated as fatal.
