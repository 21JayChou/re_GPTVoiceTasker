import json
import os
import random
import time
from abc import abstractmethod

import utils

POSSIBLE_KEYS = [
    "BACK",
    "MENU",
    "HOME"
]



KEY_KeyEvent = "key"
KEY_ManualEvent = "manual"
KEY_ExitEvent = "exit"
KEY_TouchEvent = "touch"
KEY_LongTouchEvent = "long_touch"
KEY_SelectEvent = "select"
KEY_UnselectEvent = "unselect"
KEY_SwipeEvent = "swipe"
KEY_ScrollEvent = "scroll"
KEY_SetTextEvent = "set_text"
KEY_IntentEvent = "intent"
KEY_SpawnEvent = "spawn"
KEY_KillAppEvent = "kill_app"


class InvalidEventException(Exception):
    pass

class BaseEvent:
    def __init__(self) -> None:
        self.event_type = None
    
    def to_dict(self):
        return self.__dict__
    
    def to_json(self):
        return json.dumps(self.to_dict())
    
    @abstractmethod
    def send(self, device):
        pass

    
    @staticmethod
    def from_dict(event_dict):
        if not isinstance(event_dict, dict):
            return None
        if 'event_type' not in event_dict:
            return None
        event_type = event_dict['event_type']
        if event_type == KEY_KeyEvent:
            return KeyEvent(event_dict=event_dict)
        elif event_type == KEY_TouchEvent:
            return TouchEvent(event_dict=event_dict)
        elif event_type == KEY_LongTouchEvent:
            return LongTouchEvent(event_dict=event_dict)
        elif event_type == KEY_ScrollEvent:
            return ScrollEvent(event_dict=event_dict)
        # elif event_type == KEY_SelectEvent or event_type == KEY_UnselectEvent:
        #     return SelectEvent(event_dict=event_dict)
        # elif event_type == KEY_SwipeEvent:
        #     return SwipeEvent(event_dict=event_dict)
        # elif event_type == KEY_SetTextEvent:
        #     return SetTextEvent(event_dict=event_dict)
        # elif event_type == KEY_IntentEvent:
        #     return IntentEvent(event_dict=event_dict)
        # elif event_type == KEY_ExitEvent:
        #     return ExitEvent(event_dict=event_dict)
        # elif event_type == KEY_SpawnEvent:
        #     return SpawnEvent(event_dict=event_dict)
    

class KeyEvent(BaseEvent):
    def __init__(self, name = None, event_dict = None) -> None:
        super().__init__()
        self.event_type = KEY_KeyEvent
        self.name = name
        if event_dict is not None:
            self.__dict__.update(event_dict)
    def to_dict(self):
        return self.__dict__
    
    def send(self, device):
        device.key_press(self.name)
        time.sleep(5)
    
    def get_event_str(self, state):
        return f'{self.__class__.__name__}(state={state.state_str}, name={self.name})'

    
    
class UIEvent(BaseEvent):
    """
    This class describes a UI event of app, such as touch, click, etc
    """
    def __init__(self):
        super().__init__()

    def send(self, device):
        raise NotImplementedError

    @staticmethod
    def get_xy(x, y, view):
        if x and y:
            return x, y
        if view:
            from state import State
            return State.get_view_center(view=view)
        return x, y

    @staticmethod
    def view_str(state, view):
        view_class = view['class'].split('.')[-1]
        view_text = view['text'].replace('\n', '\\n') if 'text' in view and view['text'] else ''
        view_text = view_text[:10] if len(view_text) > 10 else view_text
        view_short_sig = f'{state.activity}/{view_class}-{view_text}'
        return f"state={state.state_str}, view={view['view_str']}({view_short_sig})"
    
class TouchEvent(UIEvent):
    """
    a touch on screen
    """

    def __init__(self, x=None, y=None, view=None, event_dict=None):
        super().__init__()
        self.event_type = KEY_TouchEvent
        self.x = x
        self.y = y
        self.view = view
        if event_dict is not None:
            self.__dict__.update(event_dict)


    def send(self, device):
        x, y = UIEvent.get_xy(x=self.x, y=self.y, view=self.view)
        device.current_state.save_view_img(self.view)
        device.view_touch(x=x, y=y)
        time.sleep(5)
        return True

    def get_event_str(self, state):
        if self.view is not None:
            return f"{self.__class__.__name__}({UIEvent.view_str(state, self.view)})"
        elif self.x is not None and self.y is not None:
            return "%s(state=%s, x=%s, y=%s)" % (self.__class__.__name__, state.state_str, self.x, self.y)
        else:
            msg = "Invalid %s!" % self.__class__.__name__
            raise InvalidEventException(msg)

    def get_views(self):
        return [self.view] if self.view else []
    
class LongTouchEvent(UIEvent):
    """
    a long touch on screen
    """

    def __init__(self, x=None, y=None, view=None, duration=1000, event_dict=None):
        super().__init__()
        self.event_type = KEY_LongTouchEvent
        self.x = x
        self.y = y
        self.view = view
        self.duration = duration
        if event_dict is not None:
            self.__dict__.update(event_dict)


    def send(self, device):
        x, y = UIEvent.get_xy(x=self.x, y=self.y, view=self.view)
        device.current_state.save_view_img(self.view)
        device.view_long_touch(x=x, y=y, duration=self.duration)
        time.sleep(5)
        return True

    def get_event_str(self, state):
        if self.view is not None:
            return f"{self.__class__.__name__}({UIEvent.view_str(state, self.view)})"
        elif self.x is not None and self.y is not None:
            return "%s(state=%s, x=%s, y=%s)" % (self.__class__.__name__, state.state_str, self.x, self.y)
        else:
            msg = "Invalid %s!" % self.__class__.__name__
            raise InvalidEventException(msg)

    def get_views(self):
        return [self.view] if self.view else []
    
class ScrollEvent(UIEvent):
    """
    swipe gesture
    """

    def __init__(self, x=None, y=None, view=None, direction="down", event_dict=None):
        super().__init__()
        self.event_type = KEY_ScrollEvent
        self.x = x
        self.y = y
        self.view = view
        self.direction = direction

        if event_dict is not None:
            self.__dict__.update(event_dict)



    def send(self, device):
        if self.view is not None:
            from .state import State
            width = State.get_view_width(view=self.view)
            height = State.get_view_height(view=self.view)
        else:
            width = device.width
            height = device.height

        x, y = UIEvent.get_xy(x=self.x, y=self.y, view=self.view)
        if not x or not y:
            # If no view and no coordinate specified, use the screen center coordinate
            x = width / 2
            y = height / 2

        start_x, start_y = x, y
        end_x, end_y = x, y
        duration = 500

        if self.direction == "UP":
            start_y -= height * 2 / 5
            end_y += height * 2 / 5
        elif self.direction == "DOWN":
            start_y += height * 2 / 5
            end_y -= height * 2 / 5
        elif self.direction == "LEFT":
            start_x -= width * 2 / 5
            end_x += width * 2 / 5
        elif self.direction == "RIGHT":
            start_x += width * 2 / 5
            end_x -= width * 2 / 5
        device.current_state.save_view_img(self.view)
        device.view_drag((start_x, start_y), (end_x, end_y), duration)
        time.sleep(5)
        return True

    def get_event_str(self, state):
        if self.view is not None:
            return \
                f"{self.__class__.__name__}({UIEvent.view_str(state, self.view)}, direction={self.direction})"
        elif self.x is not None and self.y is not None:
            return "%s(state=%s, x=%s, y=%s, direction=%s)" %\
                   (self.__class__.__name__, state.state_str, self.x, self.y, self.direction)
        else:
            return "%s(state=%s, direction=%s)" % \
                   (self.__class__.__name__, state.state_str, self.direction)

    def get_views(self):
        return [self.view] if self.view else []
    
class InputTextEvent(UIEvent):
    """
    input text to target UI
    """
    def __init__(self, x=None, y=None, view=None, text=None, event_dict=None):
        super().__init__()
        self.event_type = KEY_SetTextEvent
        self.x = x
        self.y = y
        self.view = view
        self.text = text
        if event_dict is not None:
            self.__dict__.update(event_dict)

    def send(self, device):
        x, y = UIEvent.get_xy(x=self.x, y=self.y, view=self.view)
        touch_event = TouchEvent(x=x, y=y)
        device.current_state.save_view_img(self.view)
        touch_event.send(device)
        time.sleep(2)
        device.view_set_text(self.text)
        time.sleep(5)
        return True

    def get_event_str(self, state):
        if self.view is not None:
            return f"{self.__class__.__name__}({UIEvent.view_str(state, self.view)}, text={self.text})"
        elif self.x is not None and self.y is not None:
            return "%s(state=%s, x=%s, y=%s, text=%s)" %\
                   (self.__class__.__name__, state.state_str, self.x, self.y, self.text)
        else:
            msg = "Invalid %s!" % self.__class__.__name__
            raise InvalidEventException(msg)

    def get_views(self):
        return [self.view] if self.view else []
