import random
import xml.etree.ElementTree as ET
from adapter.adb import ADB
class Tools:
    view_groups = ["android.support.v7.widget.LinearLayoutCompat","android.widget.HorizontalScrollView","android.widget.GridView","androidx.drawerlayout.widget.DrawerLayout","android.widget.RelativeLayout","androidx.recyclerview.widget.RecyclerView","com.google.android.material.card.MaterialCardView","android.view.ViewGroup","android.widget.FrameLayout","android.widget.LinearLayout","android.support.v7.widget.RecyclerView"]
    @staticmethod
    def generate_id():
        return random.randint(100,999)

    @staticmethod
    def no_children_clickable(root: ET.Element):
        for child in root:
            if child.attrib["clickable"] == "true":
                return False
            if not Tools.no_children_clickable(child):
                return False
        return True
    @staticmethod
    def converge_text(root: ET.Element, texts:set, content_descs:set):

        if root.attrib['text'] != "":
            texts.add(root.attrib['text'])
        if root.attrib['content-desc'] != "":
            content_descs.add(root.attrib['content-desc'])

        for child in root:
            Tools.converge_text(child, texts, content_descs)

    @staticmethod
    def view_tree2list(root:ET.Element, view_list, width, height):
        view_dict = {}
        bounds = root.attrib["bounds"][1:-1].split("][")
        x1, y1 = map(int, bounds[0].split(","))
        x2, y2 = map(int, bounds[1].split(","))
        view_dict['bounds'] = [[x1, y1], [x2, y2]]
        is_out_of_screen = not(x1 >= 0 and x2 <= width and y1 >=0 and y2 <= height)
        is_container = root.attrib['class'] is not None and root.attrib['class'] in Tools.view_groups
        
        if len(root) == 0 and is_container:
            return
        
        if root.attrib['clickable'] == 'true' and not is_out_of_screen and (not is_container or is_container and Tools.no_children_clickable(root)):
            view_width = (x2 - x1)
            view_height = (y2 - y1)
            view_dict['size'] = '%d*%d' % (view_width, view_height)
            if is_container:
                texts = set()
                content_descs = set()
                Tools.converge_text(root, texts, content_descs)
                view_dict['text'] = ''
                view_dict['content-desc'] = ''
                for text in texts:
                    view_dict['text'] += text + ','

                for desc in content_descs:
                    view_dict['content-desc'] += desc + ','


            if root.attrib['class'] is not None and root.attrib['class'] != '':
                view_dict['class'] = root.attrib['class']

            if root.attrib['package'] is not None and root.attrib['package'] != '':
                view_dict['package'] = root.attrib['package']
        
            if root.attrib['clickable'] == 'true':
                view_dict['clickable'] = 'true'

            if root.attrib['long-clickable'] is not None and root.attrib['long-clickable'] != 'false':
                view_dict['long-clickable'] = root.attrib['long-clickable']

            if root.attrib['resource-id'] is not None and root.attrib['resource-id'] != '':
                view_dict['resource-id'] = root.attrib['resource-id']

            if root.attrib['scrollable'] is not None and root.attrib['scrollable'] != 'false':
                view_dict['scrollable'] = root.attrib['scrollable']

            if root.attrib['checkable'] is not None and root.attrib['checkable'] != 'false':
                view_dict['checkable'] = root.attrib['checkable']
                view_dict['checked'] = root.attrib['checked']

            if root.attrib['focusable'] is not None and root.attrib['focusable'] != 'false':
                view_dict['focusable'] = root.attrib['focusable']
                view_dict['focused'] = root.attrib['focused']

            if root.attrib['scrollable'] is not None and root.attrib['scrollable'] != 'false':
                view_dict['scrollable'] = root.attrib['scrollable']

            if root.attrib['scrollable'] is not None and root.attrib['scrollable'] !='false':
                view_dict['scrollable'] = root.attrib['scrollable']

            if 'editable' in root.keys() and root.attrib['editable'] != 'false':
                view_dict['editable'] = root.attrib['editable']

            if 'enabled' in root.keys() and root.attrib['enabled'] != 'false':
                view_dict['enabled'] = root.attrib['enabled']

            if 'parent' in root.keys():
                view_dict['parent'] = root.attrib['parent']
            else:
                view_dict['parent'] = -1
            view_dict['text'] = root.attrib['text']
            view_dict['content-desc'] = root.attrib['content-desc']

        tree_id = len(view_list)
        view_dict['temp_id'] = tree_id
        view_list.append(view_dict)
        children_ids = []
        for child in root:
            child.attrib['parent'] = tree_id
            Tools.view_tree2list(child, view_list, width, height)
            if 'temp_id' in child.attrib.keys():
                children_ids.append(view_dict['temp_id'])
        view_dict['children'] = children_ids



        

        
            
        
        