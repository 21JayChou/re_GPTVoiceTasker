from utils.tools import Tools
from hashlib import md5
import os
from input_event import TouchEvent, LongTouchEvent, ScrollEvent, InputTextEvent, KeyEvent
from utils.logger import Logger
import json
class State(object):
    current_node_count = 0
    def __init__(self, device, package, activity, description, views, screenshot_path, state_id=None):
        self.activity = activity
        self.package = package
        self.description = description
        self.views = views
        self.generate_views_str(self.views)
        self.screenshot_path = screenshot_path
        self.device = device
        self.possible_events = []
        self.logger = Logger.get_logger(self.__class__.__name__)
        if state_id is None:
            State.current_node_count += 1
            self.state_id = Tools.generate_id()
        else:
            self.state_id = state_id
        self.state_str = self.get_state_str()
            
    def __str__(self):
        return f"nodeID:{self.state_id} ActivityName:{self.activity_name} Description:{self.description}"

    def to_dict(self):
        d = self.__dict__.copy()
        d.pop('device')
        d.pop('logger')
        return d
    
    
    def get_state_str(self):
        state_str_raw = self.get_state_str_raw()
        return md5(state_str_raw.encode('utf-8')).hexdigest()

    def get_state_str_raw(self, width = 2560, height = 1440):
        # if self.device.humanoid is not None:
        #     import json
        #     from xmlrpc.client import ServerProxy
        #     proxy = ServerProxy("http://%s/" % self.humanoid)
        #     return proxy.render_view_tree(json.dumps({
        #         "view_tree": self.view_tree,
        #         "screen_res": [width, height]
        #     }))
        # else:
        #     view_signatures = set()
        #     for view in self.views:
        #         view_signature = State.get_view_signature(view)
        #         if view_signature:
        #             view_signatures.add(view_signature)
        #     return "%s{%s}" % (self.activity, ",".join(sorted(view_signatures)))
        view_signatures = set()
        for view in self.views:
            view_signature = State.get_view_signature(view)
            if view_signature:
                view_signatures.add(view_signature)

        return "%s{%s}" % (self.activity, ",".join(sorted(view_signatures)))

    def generate_views_str(self, views):
        for view in views:
            self.get_view_str(view)

    def get_view_str(self, view):
        """
        get a string which can represent the given view
        @param view_dict: dict, an element of list DeviceState.views
        @return:
        """
        if 'view_str' in view:
            return view['view_str']
        view_signature = State.get_view_signature(view)

        view_str = f"Activity:{self.activity}\nSelf:{view_signature}"
        view_str = md5(view_str.encode('utf-8')).hexdigest()
        view['view_str'] = view_str
        return view_str


    def get_all_children(self, view):
        """
        Get temp view ids of the given view's children
        :param view_dict: dict, an element of DeviceState.views
        :return: set of int, each int is a child node id
        """
        children = self.safe_dict_get(view, 'children')
        if not children:
            return set()
        children = set(children)
        for child in children:
            children_of_child = self.get_all_children(self.views[child])
            children.union(children_of_child)
        return children
    
    def get_possible_input(self):
        """
        Get a list of possible input events for this state
        :return: list of InputEvent
        """
        if self.possible_events:
            return [] + self.possible_events
        possible_events = []
        enabled_view_ids = []
        touch_exclude_view_ids = set()
        for view_dict in self.views:
            # exclude navigation bar if exists
            if self.safe_dict_get(view_dict, 'enabled') and \
                    self.safe_dict_get(view_dict, 'resource_id', '') not in \
               ['android:id/navigationBarBackground',
                'android:id/statusBarBackground']:
                enabled_view_ids.append(view_dict['temp_id'])
        # enabled_view_ids.reverse()

        for view_id in enabled_view_ids:
            if self.safe_dict_get(self.views[view_id], 'clickable'):
                possible_events.append(TouchEvent(view=self.views[view_id]))
                touch_exclude_view_ids.add(view_id)
                touch_exclude_view_ids.union(self.get_all_children(self.views[view_id]))

        for view_id in enabled_view_ids:
            if self.safe_dict_get(self.views[view_id], 'scrollable'):
                possible_events.append(ScrollEvent(view=self.views[view_id], direction="up"))
                possible_events.append(ScrollEvent(view=self.views[view_id], direction="down"))
                possible_events.append(ScrollEvent(view=self.views[view_id], direction="left"))
                possible_events.append(ScrollEvent(view=self.views[view_id], direction="right"))

        for view_id in enabled_view_ids:
            if self.safe_dict_get(self.views[view_id], 'checkable'):
                possible_events.append(TouchEvent(view=self.views[view_id]))
                touch_exclude_view_ids.add(view_id)
                touch_exclude_view_ids.union(self.get_all_children(self.views[view_id]))

        for view_id in enabled_view_ids:
            if self.safe_dict_get(self.views[view_id], 'long_clickable'):
                possible_events.append(LongTouchEvent(view=self.views[view_id]))

        for view_id in enabled_view_ids:
            if self.safe_dict_get(self.views[view_id], 'editable'):
                possible_events.append(InputTextEvent(view=self.views[view_id], text="Hello World"))
                touch_exclude_view_ids.add(view_id)
                # TODO figure out what event can be sent to editable views
                pass

        for view_id in enabled_view_ids:
            if view_id in touch_exclude_view_ids:
                continue
            children = self.safe_dict_get(self.views[view_id], 'children')
            if children and len(children) > 0:
                continue
            possible_events.append(TouchEvent(view=self.views[view_id]))

        # For old Android navigation bars
        # possible_events.append(KeyEvent(name="MENU"))

        self.possible_events = possible_events
        return [] + possible_events
    
    def save_view_img(self, view):
        try:
            view_str = view['view_str']
            view_img_dir = os.path.join(self.device.output_dir,'views')
            if not os.path.exists(view_img_dir):
                os.makedirs(view_img_dir)
            
            view_img_path = os.path.join(view_img_dir, f'view_{view_str}.png')
            from PIL import Image
            # Load the original image:
            view_bound = view['bounds']
            original_img = Image.open(self.screenshot_path)
            # view bound should be in original image bound
            view_img = original_img.crop((min(original_img.width - 1, max(0, view_bound[0][0])),
                                          min(original_img.height - 1, max(0, view_bound[0][1])),
                                          min(original_img.width, max(0, view_bound[1][0])),
                                          min(original_img.height, max(0, view_bound[1][1]))))
            view_img.convert("RGB").save(view_img_path)
            self.logger.debug('Finish saving view image {}'.format(view_img_path))
        except Exception as e:
            self.logger.warning(e)

    def save2dir(self):
        try:
            states_dir = os.path.join(self.device.output_dir, "states")
            if not os.path.exists(states_dir):
                os.makedirs(states_dir)
            from datetime import datetime
            tag = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            state_path = os.path.join(states_dir, "screen_%s.json" % tag)
            with open(state_path, "w") as f:
                json.dump(self.to_dict(), f)
            self.logger.info("finish saving state...")
        except Exception as e:
            self.logger.warning(f'exception in saving state:{e}')
    @staticmethod
    def key_if_true(view, key):
        return key if (key in view and view[key]) else ""

    @staticmethod
    def safe_dict_get(view, key, default=None):
        value = view[key] if key in view else None
        return value if value is not None else default
    
    @staticmethod
    def get_view_center(view = {}):
        bounds = view['bounds']
        return (bounds[0][0] + bounds[1][0]) / 2, (bounds[0][1] + bounds[1][1]) / 2
    
    @staticmethod
    def get_view_signature(view_dict):
        """
        get the signature of the given view
        @param view_dict: dict, an element of list DeviceState.views
        @return:
        """
        if 'signature' in view_dict:
            return view_dict['signature']

        view_text = State.safe_dict_get(view_dict, 'text', "None")
        if view_text is None or len(view_text) > 50:
            view_text = "None"

        signature = "[class]%s[resource_id]%s[text]%s[%s,%s,%s]" % \
                    (State.safe_dict_get(view_dict, 'class', "None"),
                     State.safe_dict_get(view_dict, 'resource_id', "None"),
                     view_text,
                     State.key_if_true(view_dict, 'enabled'),
                     State.key_if_true(view_dict, 'checked'),
                     State.key_if_true(view_dict, 'selected'))
        view_dict['signature'] = signature
        return signature

    @staticmethod
    def get_view_width(view):
        return view['bounds'][1][0] - view['bounds'][0][0]
    @staticmethod
    def get_view_height(view):
        return view['bounds'][1][1] - view['bounds'][0][1]
        