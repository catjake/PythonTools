#!/usr/bin/env python
import eva_uic,sys

def go():
    my_app = eva_uic.EvaApplication()
    my_app.go()
    my_app._destroy_command()
if __name__=='__main__':
    go()
    sys.exit()
