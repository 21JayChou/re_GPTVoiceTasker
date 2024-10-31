# This is the interface for adb
import subprocess
import re
import time
import os
from utils.logger import Logger
try:
    from shlex import quote # Python 3
except ImportError:
    from pipes import quote # Python 2


class ADBException(Exception):
    """
    Exception in ADB connection
    """
    pass


class ADB:
    """
    interface of ADB
    send adb commands via this, see:
    http://developer.android.com/tools/help/adb.html
    """
    UP = 0
    DOWN = 1
    DOWN_AND_UP = 2

    def __init__(self, device=None):
        """
        initiate a ADB connection from serial no
        the serial no should be in output of `adb devices`
        :param device: instance of Device
        :return:
        """
        self.logger = Logger.get_logger(self.__class__.__name__)
        self.device = device

        self.cmd_prefix = ['adb']

    def run_cmd(self, extra_args):
        """
        run an adb command and return the output
        :return: output of adb command
        @param extra_args: arguments to run in adb
        """
        # if isinstance(extra_args, str):
        #     extra_args = extra_args.split()
        # if not isinstance(extra_args, list):
        #     msg = "invalid arguments: %s\nshould be list or str, %s given" % (extra_args, type(extra_args))
        #     self.logger.warning(msg)
        #     raise ADBException(msg)

        args = self.cmd_prefix + extra_args
        command = ''
        for arg in args:
            command += arg + ' '
        self.logger.info(f'command:{command}')
        r = subprocess.check_output(command).strip()
        if not isinstance(r, str):
            r = r.decode()
        return r

    def shell(self, extra_args):
        """
        run an `adb shell` command
        @param extra_args:
        @return: output of adb shell command
        """
        # if isinstance(extra_args, str):
        #     extra_args = extra_args.split()
        # if not isinstance(extra_args, list):
        #     msg = "invalid arguments: %s\nshould be list or str, %s given" % (extra_args, type(extra_args))
        #     self.logger.warning(msg)
        #     raise ADBException(msg)

        shell_extra_args = ['shell'] + [ quote(arg) for arg in extra_args ]
        shell_extra_args = ['shell'] + [extra_args]
        return self.run_cmd(shell_extra_args)


    # The following methods are originally from androidviewclient project.
    # https://github.com/dtmilano/AndroidViewClient.
    def get_display_info(self):
        """
        Gets C{mDefaultViewport} and then C{deviceWidth} and C{deviceHeight} values from dumpsys.
        This is a method to obtain display dimensions and density
        """
        display_info = {}
        logical_display_re = re.compile(".*DisplayViewport{valid=true, .*orientation=(?P<orientation>\d+),"
                                        " .*deviceWidth=(?P<width>\d+), deviceHeight=(?P<height>\d+).*")
        dumpsys_display_result = self.shell("dumpsys display")
        if dumpsys_display_result is not None:
            for line in dumpsys_display_result.splitlines():
                m = logical_display_re.search(line, 0)
                if m:
                    for prop in ['width', 'height', 'orientation']:
                        display_info[prop] = int(m.group(prop))

        if 'width' not in display_info or 'height' not in display_info:
            physical_display_re = re.compile('Physical size: (?P<width>\d+)x(?P<height>\d+)')
            m = physical_display_re.search(self.shell('wm size'))
            if m:
                for prop in ['width', 'height']:
                    display_info[prop] = int(m.group(prop))

        if 'width' not in display_info or 'height' not in display_info:
            # This could also be mSystem or mOverscanScreen
            display_re = re.compile('\s*mUnrestrictedScreen=\((?P<x>\d+),(?P<y>\d+)\) (?P<width>\d+)x(?P<height>\d+)')
            # This is known to work on older versions (i.e. API 10) where mrestrictedScreen is not available
            display_width_height_re = re.compile('\s*DisplayWidth=(?P<width>\d+) *DisplayHeight=(?P<height>\d+)')
            for line in self.shell('dumpsys window').splitlines():
                m = display_re.search(line, 0)
                if not m:
                    m = display_width_height_re.search(line, 0)
                if m:
                    for prop in ['width', 'height']:
                        display_info[prop] = int(m.group(prop))

        if 'orientation' not in display_info:
            surface_orientation_re = re.compile("SurfaceOrientation:\s+(\d+)")
            output = self.shell("dumpsys input")
            m = surface_orientation_re.search(output)
            if m:
                display_info['orientation'] = int(m.group(1))

        # density = None
        # float_re = re.compile(r"[-+]?\d*\.\d+|\d+")
        # d = self.get_property('ro.sf.lcd_density')
        # if float_re.match(d):
        #     density = float(d)
        # else:
        #     d = self.get_property('qemu.sf.lcd_density')
        #     if float_re.match(d):
        #         density = float(d)
        #     else:
        #         physical_density_re = re.compile('Physical density: (?P<density>[\d.]+)', re.MULTILINE)
        #         m = physical_density_re.search(self.shell('wm density'))
        #         if m:
        #             density = float(m.group('density'))
        # if density is not None:
        #     display_info['density'] = density

        display_info_keys = {'width', 'height', 'orientation', 'density'}
        if not display_info_keys.issuperset(display_info):
            self.logger.warning("getDisplayInfo failed to get: %s" % display_info_keys)

        return display_info


    def get_installed_apps(self):
        """
        Get the package names and apk paths of installed apps on the device
        :return: a dict, each key is a package name of an app and each value is the file path to the apk
        """
        app_lines = self.shell("pm list packages -f").splitlines()
        app_line_re = re.compile("package:(?P<apk_path>.+)=(?P<package>[^=]+)")
        package_to_path = {}
        for app_line in app_lines:
            m = app_line_re.match(app_line)
            if m:
                package_to_path[m.group('package')] = m.group('apk_path')
        return package_to_path

    def get_display_density(self):
        display_info = self.get_display_info()
        if 'density' in display_info:
            return display_info['density']
        else:
            return -1.0

    def __transform_point_by_orientation(self, xy, orientation_orig, orientation_dest):
        (x, y) = xy
        if orientation_orig != orientation_dest:
            if orientation_dest == 1:
                _x = x
                x = self.get_display_info()['width'] - y
                y = _x
            elif orientation_dest == 3:
                _x = x
                x = y
                y = self.get_display_info()['height'] - _x
        return x, y

    def get_orientation(self):
        display_info = self.get_display_info()
        if 'orientation' in display_info:
            return display_info['orientation']
        else:
            return -1

    def unlock(self):
        """
        Unlock the screen of the device
        """
        self.shell("input keyevent MENU")
        self.shell("input keyevent BACK")

    def key_press(self, key_code):
        """
        Press a key
        """
        self.shell("input keyevent %s" % key_code)

    def touch(self, x, y, orientation=-1, event_type=DOWN_AND_UP):
        if orientation == -1:
            orientation = self.get_orientation()
        self.shell("input tap %d %d" %
                   self.__transform_point_by_orientation((x, y), orientation, self.get_orientation()))

    def long_touch(self, x, y, duration=2000, orientation=-1):
        """
        Long touches at (x, y)
        """
        self.drag((x, y), (x, y), duration, orientation)

    def drag(self, start_xy, end_xy, duration, orientation=-1):
        """
        Sends drag event n PX (actually it's using C{input swipe} command.
        @param start_xy: starting point in pixel
        @param end_xy: ending point in pixel
        @param duration: duration of the event in ms
        @param orientation: the orientation (-1: undefined)
        """
        (x0, y0) = start_xy
        (x1, y1) = end_xy
        if orientation == -1:
            orientation = self.get_orientation()
        (x0, y0) = self.__transform_point_by_orientation((x0, y0), orientation, self.get_orientation())
        (x1, y1) = self.__transform_point_by_orientation((x1, y1), orientation, self.get_orientation())

        self.shell("input swipe %d %d %d %d" % (x0, y0, x1, y1))
        # else:
        #     self.shell("input touchscreen swipe %d %d %d %d %d" % (x0, y0, x1, y1, duration))

    def input_text(self, x, y, text, orientation=-1):
        if isinstance(text, str):
            escaped = text.replace("%s", "\\%s")
            encoded = escaped.replace(" ", "%s")
        else:
            encoded = str(text)
        # TODO find out which characters can be dangerous, and handle non-English characters
        self.touch(x, y, orientation)
        self.shell("input text %s" % encoded)
        
    def get_package_activity(self):
        res = self.shell("dumpsys window | grep mCurrentFocus")
        pattern = re.compile('mCurrentFocus=Window\{.*? u0 (\S+/\S+)}')
        packagename, activity = re.findall(pattern, res)[0].split('/')
        activity = activity.replace(packagename, '')
        return packagename, activity 
    
    def get_xml(self, packagename, activity):
        self.shell('uiautomator dump /sdcard/domtree.xml')
        xml_dir = f'.\\data\\{packagename}\\xmls'
        if not os.path.exists(xml_dir):
            os.makedirs(xml_dir)
        xml_path = os.path.join(xml_dir, f'{activity}.xml')
        os.system(f"adb pull /sdcard/domtree.xml {xml_path}")
        return xml_path
        