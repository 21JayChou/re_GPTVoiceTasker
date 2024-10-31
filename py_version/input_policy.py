import sys
import json
import random
import time
from device import Device
from abc import abstractmethod
from input_event import KeyEvent, InputTextEvent, ScrollEvent
from graph.utg import UTG
from utils.logger import Logger

# Max number of restarts
MAX_NUM_RESTARTS = 5
# Max number of steps outside the app
MAX_NUM_STEPS_OUTSIDE = 5
MAX_NUM_STEPS_OUTSIDE_KILL = 10
# Max number of replay tries
MAX_REPLY_TRIES = 5

# Some input event flags
EVENT_FLAG_STARTED = "+started"
EVENT_FLAG_START_APP = "+start_app"
EVENT_FLAG_STOP_APP = "+stop_app"
EVENT_FLAG_EXPLORE = "+explore"
EVENT_FLAG_NAVIGATE = "+navigate"
EVENT_FLAG_TOUCH = "+touch"

# Policy taxanomy
POLICY_NAIVE_DFS = "dfs_naive"
POLICY_GREEDY_DFS = "dfs_greedy"
POLICY_NAIVE_BFS = "bfs_naive"
POLICY_GREEDY_BFS = "bfs_greedy"
POLICY_REPLAY = "replay"
POLICY_MANUAL = "manual"
POLICY_MONKEY = "monkey"
POLICY_NONE = "none"
POLICY_MEMORY_GUIDED = "memory_guided"  # implemented in input_policy2
POLICY_LLM_GUIDED = "llm_guided"  # implemented in input_policy3



class InputInterruptedException(Exception):
    pass


class InputPolicy(object):
    """
    This class is responsible for generating events to stimulate more app behaviour
    It should call AppEventManager.send_event method continuously
    """

    def __init__(self, device:Device):
        self.logger = Logger.get_logger(self.__class__.__name__)
        self.device = device
        self.action_count = 0

    # def start(self, input_manager):
    #     """
    #     start producing events
    #     :param input_manager: instance of InputManager
    #     """
    #     self.action_count = 0
    #     while input_manager.enabled and self.action_count < input_manager.event_count:
    #         try:
    #             # # make sure the first event is go to HOME screen
    #             # # the second event is to start the app
    #             # if self.action_count == 0 and self.master is None:
    #             #     event = KeyEvent(name="HOME")
    #             # elif self.action_count == 1 and self.master is None:
    #             #     event = IntentEvent(self.app.get_start_intent())
    #             if self.action_count == 0 and self.master is None:
    #                 event = KillAppEvent(app=self.app)
    #             else:
    #                 event = self.generate_event()
    #             input_manager.add_event(event)
    #         except KeyboardInterrupt:
    #             break
    #         except InputInterruptedException as e:
    #             self.logger.warning("stop sending events: %s" % e)
    #             break
    #         # except RuntimeError as e:
    #         #     self.logger.warning(e.message)
    #         #     break
    #         except Exception as e:
    #             self.logger.warning("exception during sending events: %s" % e)
    #             import traceback
    #             traceback.print_exc()
    #             continue
    #         self.action_count += 1

    @abstractmethod
    def generate_event(self):
        """
        generate an event
        @return:
        """
        pass

class DfsSearchPolicy(InputPolicy):
    def __init__(self, device:Device, max_depth, utg:UTG):
        super(DfsSearchPolicy, self).__init__(device)
        self.max_depth = max_depth
        self.event_stack = []
        self.utg = utg

    def generate_event(self):
        if self.device.current_state is None:
            time.sleep(5)
            return KeyEvent(name="BACK")

        current_state = self.device.current_state
        self.logger.info("Current state: %s" % current_state.state_str)
        possible_events = self.device.current_state.get_possible_input()
        self.logger.debug(f'number of possible events: {len(possible_events)}')
        if len(possible_events) == 0:
            return KeyEvent(name="BACK")
        random.shuffle(possible_events)
        for event in possible_events:
            if not self.utg.is_event_explored(event, current_state) and not isinstance(event, InputTextEvent) and not isinstance(event, ScrollEvent):
                return event
            return KeyEvent(name="BACK")



class UtgGreedySearchPolicy(InputPolicy):
    """
    DFS/BFS (according to search_method) strategy to explore UFG (new)
    """

    def __init__(self, device,search_method):
        super().__init__(device=device)
        self.logger = Logger.get_logger(self.__class__.__name__)
        self.search_method = search_method
        self.utg = UTG(device)
        if self.device.humanoid is not None:
            self.humanoid_view_trees = []
            self.humanoid_events = []

        self.preferred_buttons = ["yes", "ok", "activate", "detail", "more", "access",
                                  "allow", "check", "agree", "try", "go", "next"]
    
    def generate_event(self):
        if self.device.current_state is None:
            import time
            time.sleep(5)
            return KeyEvent(name="BACK")
        
        if self.device.humanoid is not None:
            self.humanoid_view_trees = self.humanoid_view_trees + [self.device.current_state.views]
            if len(self.humanoid_view_trees) > 4:
                self.humanoid_view_trees = self.humanoid_view_trees[1:]
        
        event = self.generate_event_based_on_graph()
        if self.device.humanoid is not None:
            self.humanoid_events = self.humanoid_events + [event]
        if len(self.humanoid_events) > 3:
            self.humanoid_events = self.humanoid_events[1:]
        
        self.logger.info('starting event:%s'%event.to_dict())
        return event


    def generate_event_based_on_graph(self):
        """
        generate an event based on current UTG
        @return: InputEvent
        """
        current_state = self.current_state
        self.logger.info("Current state: %s" % current_state.state_str)
        # if current_state.state_str in self.__missed_states:
        #     self.__missed_states.remove(current_state.state_str)

        # if current_state.get_app_activity_depth(self.app) < 0:
        #     # If the app is not in the activity stack
        #     start_app_intent = self.app.get_start_intent()

        #     # It seems the app stucks at some state, has been
        #     # 1) force stopped (START, STOP)
        #     #    just start the app again by increasing self.__num_restarts
        #     # 2) started at least once and cannot be started (START)
        #     #    pass to let viewclient deal with this case
        #     # 3) nothing
        #     #    a normal start. clear self.__num_restarts.

        #     if self.__event_trace.endswith(EVENT_FLAG_START_APP + EVENT_FLAG_STOP_APP) \
        #             or self.__event_trace.endswith(EVENT_FLAG_START_APP):
        #         self.__num_restarts += 1
        #         self.logger.info("The app had been restarted %d times.", self.__num_restarts)
        #     else:
        #         self.__num_restarts = 0

        #     # pass (START) through
        #     if not self.__event_trace.endswith(EVENT_FLAG_START_APP):
        #         if self.__num_restarts > MAX_NUM_RESTARTS:
        #             # If the app had been restarted too many times, enter random mode
        #             msg = "The app had been restarted too many times. Entering random mode."
        #             self.logger.info(msg)
        #             self.__random_explore = True
        #         else:
        #             # Start the app
        #             self.__event_trace += EVENT_FLAG_START_APP
        #             self.logger.info("Trying to start the app...")
        #             return IntentEvent(intent=start_app_intent)

        # elif current_state.get_app_activity_depth(self.app) > 0:
        #     # If the app is in activity stack but is not in foreground
        #     self.__num_steps_outside += 1

        #     if self.__num_steps_outside > MAX_NUM_STEPS_OUTSIDE:
        #         # If the app has not been in foreground for too long, try to go back
        #         if self.__num_steps_outside > MAX_NUM_STEPS_OUTSIDE_KILL:
        #             stop_app_intent = self.app.get_stop_intent()
        #             go_back_event = IntentEvent(stop_app_intent)
        #         else:
        #             go_back_event = KeyEvent(name="BACK")
        #         self.__event_trace += EVENT_FLAG_NAVIGATE
        #         self.logger.info("Going back to the app...")
        #         return go_back_event
        # else:
        #     # If the app is in foreground
        #     self.__num_steps_outside = 0

        # Get all possible input events
        possible_events = self.device.current_state.get_possible_input()

        if self.search_method == POLICY_GREEDY_DFS:
            possible_events.append(KeyEvent(name="BACK"))
        elif self.search_method == POLICY_GREEDY_BFS:
            possible_events.insert(0, KeyEvent(name="BACK"))

        # get humanoid result, use the result to sort possible events
        # including back events
        if self.device.humanoid is not None:
            possible_events = self.__sort_inputs_by_humanoid(possible_events)

        # If there is an unexplored event, try the event first
        for input_event in possible_events:
            if not self.utg.is_event_explored(event=input_event, state=current_state):
                self.logger.info("Trying an unexplored event.")
                return input_event
        
        # TODO: stop building

    def __sort_inputs_by_humanoid(self, possible_events):
        
        from xmlrpc.client import ServerProxy
        proxy = ServerProxy("http://%s/" % self.device.humanoid)
        request_json = {
            "history_view_trees": self.humanoid_view_trees,
            "history_events": [x.__dict__ for x in self.humanoid_events],
            "possible_events": [x.__dict__ for x in possible_events],
            "screen_res": [self.device.display_info["width"],
                           self.device.display_info["height"]]
        }
        result = json.loads(proxy.predict(json.dumps(request_json)))
        new_idx = result["indices"]
        text = result["text"]
        new_events = []

        # get rid of infinite recursive by randomizing first event
        if not self.utg.is_state_reached(self.current_state):
            new_first = random.randint(0, len(new_idx) - 1)
            new_idx[0], new_idx[new_first] = new_idx[new_first], new_idx[0]

        for idx in new_idx:
            if isinstance(possible_events[idx], InputTextEvent):
                possible_events[idx].text = text
            new_events.append(possible_events[idx])
        return new_events
    
    def update_graph(self):
        self.utg.add_transition(self.device.last_event, self.device.last_state, self.device.current_state)