#!/usr/bin/env python

import os
from Tkinter import *
import tkFont
import util

# floating_menu
# first attempt at creating class for generating mouse driven events, i.e. M3 brings up a menu of options such as copy, cut
# and paste.  Want a boiler plate to start with, then allow for insertion of custom events as required for the 
# particular app.

class FloatingMenu(Frame): 
    Version = '0.1'

    def __init__(self, master=None):
        Frame.__init__(self, master) 
        self.grid(sticky=N+S+W+E)
        self.rowconfigure(0, weight=1)

    def _create_menu_bar(self, root):
        # create menubar
        self.menubar = Menu(self)
    
    def _add_to_menu_bar(self, CommandLabel, Command):
        self.menubar.add_command(label=CommandLabel, command=Command)
