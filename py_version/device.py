from adapter.adb import ADB
from state import State
import xml.etree.ElementTree as ET
from utils.chat import Chat
from prompt import Prompt
from utils.tools import Tools
import os
from utils.logger import Logger
import json

class Device:
    def __init__(self, current_state:State = None) -> None:
        self.adb = ADB(self)
        display_info = self.adb.get_display_info()
        self.width = display_info['width']
        self.height = display_info['height']
        self.package, self.activity = self.get_package_activity()
        self.output_dir = f'.\\data\\{self.package}'
        self.last_event = None
        self.last_state = None
        self.current_state = None
        self.logger = Logger.get_logger(self.__class__.__name__)
        self.get_current_state()
    def view_touch(self, x, y):
        self.adb.touch(x, y)

    def view_long_touch(self, x, y, duration=2000):
        """
        Long touches at (x, y)
        @param duration: duration in ms
        This workaround was suggested by U{HaMi<http://stackoverflow.com/users/2571957/hami>}
        """
        self.adb.long_touch(x, y, duration)

    def view_drag(self, start_xy, end_xy, duration):
        """
        Sends drag event n PX (actually it's using C{input swipe} command.
        """
        self.adb.drag(start_xy, end_xy, duration)

    def view_input_text(self, x, y, text):
        
        self.adb.input_text(x, y, text)

    def key_press(self, key_code):
        self.adb.key_press(key_code)
        
    def get_xml(self):
        return self.adb.get_xml(self.package, self.activity)
        
    def get_package_activity(self):
        return self.adb.get_package_activity()
    
    def get_screen_description(self, package, current_screen_xml, activity):
        prompt = Prompt.screen_summarise(package, current_screen_xml, activity)
        return Chat.chat_with_llm(prompt)
    
    def get_views(self, xml_path)->list:
        root = ET.parse(xml_path).getroot()
        view_list = []
        for child in root:
            Tools.view_tree2list(child, view_list, self.width, self.height)
        return view_list
    
    def get_screenshot(self):
        from datetime import datetime
        tag = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        screenshot_dir = os.path.join(self.output_dir, "screenshots")
        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir)

        local_img_path = os.path.join(screenshot_dir, "screen_%s.png" % tag)
        remote_img_path = "/sdcard/screenshot.png"
        self.adb.shell(f"screencap -p {remote_img_path}")
        self.adb.run_cmd([f'pull {remote_img_path} {local_img_path}'])
        self.adb.shell("rm %s" % remote_img_path)

        return local_img_path
        
    def get_current_state(self):
        self.logger.info("getting current device state...")
        current_state = None
        try:
            xml_path = self.get_xml()
            views = self.get_views(xml_path)
            package, activity = self.get_package_activity()
            screen_description = self.get_screen_description(package, str(views), activity)
            screenshot_path = self.get_screenshot()
            self.logger.info("finish getting current device state...")
            current_state = State(self,package, activity, screen_description, views, screenshot_path)
        except Exception as e:
            self.logger.warning("exception in get_current_state: %s" % e)
            import traceback
            traceback.print_exc()
        if not current_state:
            self.logger.error("Failed to get current state!")

        self.last_state = self.current_state
        self.current_state = current_state

