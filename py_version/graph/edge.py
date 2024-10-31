
class Edge:
    def __init__(self, src, dest, action="", target="", bounds=""):
        self.src = src
        self.dest = dest
        if action == "":
            self.action = " "
        else:
            self.action = action

        if target == "":
            self.target = " "
        else:
            self.target = target

        if bounds == "":
            self.bounds = " "
        else:
            self.bounds = bounds

    def __str__(self):
        return f"Edge: {self.src.nodeID} -> {self.dest.nodeID}, action='{self.action}', target='{self.target}', bounds='{self.bounds}\n"