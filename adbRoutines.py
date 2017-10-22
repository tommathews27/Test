#!/usr/bin/env python
# coding=utf-8

"""12/03/2014: Initial coding of adb modules commonly used
03/12/2015: Minor changes to make return values consistent and remove unnecessary 'async'
            argument to cmdAdb
06/22/2015: Addition of few more functions
07/09/2015: Added global debug option to suppress printing debug messages, and also better error handling
07/22/2015: Added docstrings to all functions and cleaned up the responses of all the functions to return a standard
            output
"""

import subprocess
import os
import re
import time

__firstInput = 'sharon'

__author__ = "Janifer Patterson-Noble & Tom Mathews"
__modDate__ = "04/18/2016"
__description__ = "Common adb routines which are have been utilized in multiple test cases"

class (object):
  __name = 'firstChange'
  
  
  
class ADB(object):
    __adb_path = None
    __error = None
    __getADBPath = None
    __failed = False
    __passed = True

    def __init__(self):
        self.device = None
        self.debug = False
        self.__getADBPath = os.popen("/usr/bin/which adb")
        self.resetPath()
        self.asyncHdl = None
        self.osVersion = ""
        self.screen_state = {"5": "Display Power", "4": "mScreenOn"}
        self.screen_state_off_response = {"5": "state=OFF", "4": "false"}
        self.lock_screen_state = {"5": "StatusBar", "4": "Keyguard"}

    def adbRoot(self):
        """
            Root and Remount the device

            Returns: (bool)
                True or False based on success or failure of the function
        """
        # Rooting the device
        print 'Rooting the Device'
        for _ in range(3):
            result = self.cmdAdb('root')
            if type(result) is list:
                if not result:
                    result = ['restarting adbd as root']
                if ('restarting adbd as root' in result[0]) or ('already running as root' in result[0]):
                    self.cmdAdb('wait-for-device')
                    print('Device is rooted')
                    result = self.cmdAdb('remount')
                    if type(result) is list:
                        if not result:
                            time.sleep(5)
                            result = self.cmdAdb('remount')
                    if 'remount succeeded' in result[0]:
                        self.cmdAdb('wait-for-device')
                        print('Device is remounted')
                        return True
                elif 'adbd cannot run as root in production builds' in result[0]:
                    print('Production devices cannot be rooted')
                    return False
                else:
                    print('Root & Remount failed, trying again')
                    time.sleep(2)
            else:
                continue
        return False

    def checkDeviceConn(self):
        """
            Check device adb connection state

            Returns: (bool)
                True or False based on whether the adb to device connection is active or not
        """
        ret = self.cmdAdb("get-state")
        ret = ret[0].strip()
        print("Device state reported as: %s" % ret)
        if (ret == "device"):
            if self.device is None:
                self.device = self.getDevices()[0]
            return True
        else:
            return False

    def checkFocusWindow(self):
        """
            Get current focus window on the device

            Returns:
                ret (str): String with the current focus on the device
        """
        ret = self.cmdAdb("shell dumpsys window windows | grep -E 'mCurrentFocus'")[0].strip()
        return ret

    def checkLockScreenState(self):
        """
            Check screen state of the device

            Returns: (bool)
                True or False based on whether the screen is ON or OFF
        """
        self.getOSVersion()
        ret = self.checkFocusWindow()
        if self.lock_screen_state[self.osVersion[0]].upper() in ret.upper():
            return True
        else:
            return False

    def checkScreenState(self):
        """
            Check screen state of the device

            Returns: (bool)
                True or False based on whether the screen is ON or OFF
        """
        self.getOSVersion()
        ret = self.cmdAdb("shell dumpsys power | grep '%s'" % self.screen_state[self.osVersion[0]])[0].strip()
        if self.screen_state_off_response[self.osVersion[0]] not in ret:
            return True
        else:
            return False

    def cmdAdb(self, command, fd=None, async=False):
        """
            Function to run any adb commands

            Args:
                command (str): Command to be executed
                fd (file handle): File handle to store result while running in aysnc mode
                async (bool): Boolean to specify to run the command asynchronously or not

            Returns:
                result (list - str): Output of the command. When the command is run asynchronously the output is
                'Async'
        """
        if self.device is None:
            command = '%s %s' % (self.__adb_path, command)
        else:
            command = '%s -s %s %s' % (self.__adb_path, self.device, command)
        if self.debug is True:
            print 'Submitting: %s' % command
        try:
            if async is not None and fd is not None:
                if self.debug is True:
                    print "Running adb command asynchronously..."
                self.asyncHdl = subprocess.Popen(command.split(), stdout=fd, stderr=subprocess.STDOUT, )
                result = ["Async"]
            else:
                result = os.popen(command, 'r').readlines()
        except Exception, self.__error:
            print "Issue with the command: %s  \n Due to this Error: %s " % (command, self.__error.message)
            result = False
        return result

    def cmdKeyevent(self, keycode):
        """
            Input a keyevent to the device

            Args:
                keyevent (str): Key code to be input to the device using keyevent
        """
        # adb command input keyevent
        self.cmdAdb('shell input keyevent ' + str(keycode))
        return None

    def cmdText(self, text):
        """
            Input a text to the device

            Args:
                text (str): Text to be input to the device
        """
        self.cmdAdb('shell input text ' + str(text))
        return None

    def devReboot(self):
        """
            Reboot the device

        """
        # adb command for device reboot
        self.cmdAdb('reboot')
        return None

    def disableLowBatterySystemDialogs(self):
        """
            Disable Low Battery & System Dialogs
        """
        # adb command for device reboot
        self.cmdAdb('shell touch /data/system/disable_mtp_dialog.txt')

        print('Disable low power charging dialog')
        self.cmdAdb('shell settings put system low_charger_dialog 0')
        time.sleep(10)

        print("Disable all pop-up dialogs")
        self.cmdAdb('shell setprop persist.sys.disable_anrcd 1')
        time.sleep(10)

        return None

    def disable_oobe(self):
        """
            Disables OOBE

            Returns: (bool)
                True  -- OOBE disabled
                False -- Otherwise
        """
        print("Disable OOBE")
        self.cmdAdb('shell settings put secure user_setup_complete 1')
        self.cmdAdb('shell settings put secure oobe_completed 1')
        self.cmdAdb('shell settings put global device_provisioned 1')
        time.sleep(1)
        self.cmdAdb('shell pm disable com.amazon.kindle.otter.oobe')
        self.cmdAdb('shell pm disable com.amazon.tv.oobe')
        result_focus = self.search_dumpsys('mCurrentFocus=.*', 'window')
        if 'oobe' not in result_focus.lower():
            return True
        else:
            return False

    def exist_on_device(self, path):
        """
            Input a text to the device

            Args:
                path (str): File or directory path to be checked

            Returns: (bool)
                True or False based on whether the file or directory exists on the device
        """
        # Check whether a file/directory exist on device
        status = self.cmdAdb('shell ls ' + path)
        if 'No such file' in status:
            return False
        else:
            return True

    def filePull(self, remotepath, localpath):
        """
            Pull file(s) from the device

            Args:
                localpath (str): Path on local station to pull the file from device to

            Returns: (bool)
                True or False based on whether the file or directory exists on the device
        """
        if int(self.cmdAdb('version')[0].strip().split('.')[-1:][0]) > 31:
            cmd = 'pull -p '
        else:
            cmd = 'pull '
        self.cmdAdb(cmd + remotepath + ' ' + localpath)
        return None

    def filePush(self, localpath, remotepath):
        """
            Pull file(s) from the device

            Args:
                localpath (str): Path on local station to pull the file from device to

            Returns: (bool)
                True or False based on whether the file or directory exists on the device
        """
        if int(self.cmdAdb('version')[0].strip().split('.')[-1:][0]) > 31:
            cmd = 'push -p '
        else:
            cmd = 'push '
        self.cmdAdb(cmd + localpath + ' ' + remotepath)
        return None

    def findPids(self, process):
        """
            Pull file(s) from the device

            Args:
                process (str): Process name

            Returns:
                PIDs (list - str): List of all the process under the same process name
        """
        command = "shell ps | grep %s | awk {'print $2'}" % process
        PIDs = self.cmdAdb(command)
        return PIDs

    def forceClose(self, package):
        """
            Force close a particular package on the device

            Args:
                package (str): Package name [e.g. com.amazon.avod]
        """
        self.cmdAdb('shell am force-stop %s' % package)
        return None

    def getBatteryLevel(self):
        """
            Get battery level from device

            Returns: (str)
                Percentage battery level
        """
        return self.cmdAdb('shell dumpsys battery | grep level')[0].strip().split(' ')[1]

    def getBuildVersion(self):
        """
            Get build version from device

            Returns: (str)
                Incremental build version
        """
        return self.cmdAdb('shell getprop ro.build.version.incremental')[0].strip()

    def getDevices(self):
        """
            Get DSNs of all the connected devices

            Returns:
             devices (list - str): List of DSNs of all the devices that are connected.
        """
        lines = self.cmdAdb("devices")
        devices = []
        for line in lines[1:(len(lines) - 1)]:
            line = line.split('\t')[0].strip()
            devices.append(line)
        return devices

    def getDevName(self):
        """
            Get device name

            Returns: (str)
                Device name
        """
        return self.cmdAdb('shell getprop ro.product.name')[0].strip()

    def getDeviceState(self):
        """
            Get device state

            Returns:
                ret (str): State of the device
        """
        ret = self.cmdAdb("get-state")[0].strip()
        return ret

    def getOSVersion(self):
        """
            Get device name

            Returns: (str)
                OS Version on the device '5' or '4'
        """
        self.osVersion = self.cmdAdb('shell getprop ro.build.version.release')[0].strip()
        return self.osVersion

    def gotoHomescreen(self):
        """
            Input keycode to go to homescreen
        """
        return self.cmdKeyevent('3')

    def getPath(self):
        """
            Get adb path

            Returns: (str)
                adb path
        """
        return self.__adb_path

    def hasBootComp(self):
        """
            Check for boot complete

            Returns: (bool)
                True or False based on whether or not the boot of the device has completed or not
        """
        ret = self.cmdAdb("shell getprop sys.boot_completed")[0].strip()
        return ret == '1'

    def isDeviceOn(self):
        """
            Check for boot complete

            Returns: (bool)
                True or False based on whether display power is on or not
        """
        ret = self.checkScreenState()
        return ret

    def launchActivity(self, activity, opt=None):
        """
            Launch an activity on the device

            Args:
                activity (str): Activity to be launched
            Returns:
                ret (list - str): Message and Warnings from the adb command
        """
        ret = self.cmdAdb('shell am start %s' % activity)
        return ret

    def launchPackage(self, package, opt=None):
        """
            Launch a package on the device

            Args:
                package (str): Package to be launched
            Returns:
                ret (list - str): Message and Warnings from the adb command
        """
        ret = self.cmdAdb('shell pm start %s' % package)
        return ret

    def launchService(self, service, opt=None):
        """
            Launch a service on the device

            Args:
                service (str): Package to be launched
            Returns:
                ret (list - str): Message and Warnings from the adb command
        """
        ret = self.cmdAdb('shell am startservice %s' % service)
        return ret

    def removeScreenWarnings(self):
        """
            Removes screen warnings from the device
        """
        self.cmdKeyevent('4')
        return None

    def resetPath(self):
        """
            Reset adb path
        """
        if self.__getADBPath is not None:
            for ePath in self.__getADBPath.readlines():
                if os.path.exists(ePath.strip()):
                    self.__adb_path = ePath.strip()
                    break
        else:
            self.__adb_path = os.environ.get('ADBPATH')

    def search_dumpsys(self, keyword, cmd=''):
        """
            Search dumpsys for a keyword

            Args:
                keyword (str): keyword to look for in dumpsys

            Kwargs:
                cmd (str): Dumpsys argument (battery, window, power)

            Returns: (str)
                Line that contains keyword
        """
        result = self.cmdAdb('shell dumpsys %s' % cmd)
        if len(result) > 0:
            for line in result:
                match = re.search(keyword, line)
                if match:
                    return match.group(0)

    def stayAwake(self, state=True):
        """
            Keep the device awake

            Args:
                state (bool): True to enable and False to disable [Default - True]
        """
        if state:
            self.cmdAdb('shell svc power stayon true')
        elif not state:
            self.cmdAdb('shell svc power stayon false')
        return None

    def suspendDevice(self):
        """
            Suspend the device
        """
        ret = self.checkScreenState()
        if ret:
            self.cmdKeyevent('26')
        return None

    def takeScreenshot(self, fname='screen.png'):
        """
            Take screenshot of the device

            Args:
                fname (str): Name for the screenshot image file [Default: 'screen.png']
        """
        print 'Taking Screenshot'
        self.cmdAdb('shell screencap -p /sdcard/' + fname)
        print ('Screenshot saved in /sdcard/ as ' + fname)
        return None

    def unlockDevice(self):
        """
            Unlock the device if it is locked
        """
        self.wakeDevice()
        print('Screen is ON')
        if self.checkLockScreenState():
            self.cmdKeyevent('82')
        print('Screen is unlocked')
        return None

    def waitBootComplete(self):
        """
            Wait till the device comes up on adb and completes boot
        """
        # Waiting for the device to show up on ADB
        print ('Waiting for the Device to come on ADB')
        while True:
            dev_state = self.getDeviceState()
            if dev_state == 'device':
                break
        # Waiting for the device to complete boot
        print ('Waiting for BootComplete')
        while True:
            dev_state = self.hasBootComp()
            if dev_state:
                break
        print 'Device Boot Complete'
        return None

    def wakeDevice(self):
        """
            Wake the device if it is in suspend state
        """
        if not self.isDeviceOn():
            self.cmdKeyevent('26')
        return None
