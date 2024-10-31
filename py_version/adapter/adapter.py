from input_event import BaseEvent, KeyEvent, TouchEvent, LongTouchEvent, InputTextEvent, ScrollEvent
from device import Device
from state import State
import time
    

class InstructionAdapter:
    def __init__(self, device:Device) -> None:
        self.device = device
    
    def real_operation(self,event:BaseEvent):
        if isinstance(event, TouchEvent):
            self.real_touch(event)
        if isinstance(event, LongTouchEvent):
            self.real_long_touch(event)
        if isinstance(event, InputTextEvent):
            self.real_input_text(event)
        if isinstance(event, KeyEvent):
            self.real_key_press(event)
        time.sleep(2)
        self.device.last_event = event
        self.device.last_state = self.device.current_state
        self.device.get_current_state()
        
    
    def real_touch(self, event:TouchEvent):
        (x,y) = State.get_view_center(event['view'])
        self.device.view_touch(x, y)
    
    def real_long_touch(self, event:LongTouchEvent):
        (x,y) = State.get_view_center(event['view'])
        self.device.view_long_touch(x, y)
    
    def real_input_text(self, event:InputTextEvent):
        (x,y) = State.get_view_center(event['view'])
        text = event['text']
        self.device.view_input_text(x, y, text)
    
    def real_key_press(self, event:KeyEvent):
        self.device.key_press(event['name'])
