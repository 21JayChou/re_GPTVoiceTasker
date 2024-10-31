from .utils import Utils
class Node:
    current_node_count = 0

    def __init__(self, activity_name, clickable_elements, description, screen_dumper_xml, node_id=None):
        self.activity_name = activity_name
        self.clickable_elements = clickable_elements
        self.description = description
        self.screen_dumper_xml = screen_dumper_xml
        if node_id is None:
            Node.current_node_count += 1
            self.node_id = Utils.generate_id()
        else:
            self.node_id = node_id

    def __str__(self):
        return f"nodeID:{self.node_id} ActivityName:{self.activity_name} Description:{self.description}"
