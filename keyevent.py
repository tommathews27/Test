#!/usr/bin/env python

import sys
import argparse
import adbRoutines



def helper():
    """Helper for usage 
    """
    print "KeyEvent"
    print "Usage : " + sys.argv[0] + "[-h|--help] [-k|--keyevent <KeyEvent>] [-d|--device <DSN>]"
    print "\tKeyEvent can be found in : http://developer.android.com/reference/android/view/KeyEvent.html"
    print "\t DSN is the device SN as output by adb \"devices\" cmd"
    sys.exit(2)


def runner(arg):
    adb.device = arg.device
    keycode = arg.keycode
    if keycode is None:
        print ("Keycode not entered")
        helper()
    cmd = 'shell input keyevent ' + keycode
    if not adb.device is None:
        adb.cmdAdb(cmd)
    else:
        devices = adb.getDevices()
        if len(devices) == 0:
            print ("No device found")
            helper()
        elif len(devices) > 1:
            print ("More than one device connected")
            helper()
        else:
            adb.device = (devices[0])
            adb.cmdAdb(cmd)


if __name__ == '__main__':
    adb = adbRoutines.ADB()
    parser = argparse.ArgumentParser(description="Reboot Device(s)",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d', '--device', type=str, help='DSN is the device Serial Number as output '
                                                         'by \"adb devices\" cmd')
    parser.add_argument('-k', '--keycode', type=str,
                        help='KeyEvent can be found in : '
                             'http://developer.android.com/reference/android/view/KeyEvent.html')
    args = parser.parse_args()
    runner(args)