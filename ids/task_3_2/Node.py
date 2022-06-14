class Node:
    def __init__(self, prefix):
        self.prefix = prefix
        self.visit_counter = 0
        self.type_child_map = {}

    def count_sequence(self, sequence):
        """Move along the nodes given by the sequence of message types and update the counter for each visited node."""
        self.visit_counter += 1
        if len(sequence) == 0:
            return

        next_msg_type = sequence[0]["type"]

        if next_msg_type not in self.type_child_map:
            self.type_child_map[next_msg_type] = Node(self.prefix + "|" + next_msg_type)
        self.type_child_map[next_msg_type].count_sequence(sequence[1:])

    def add_edges(self, tree):
        """Adds all edges of this subtree to the given Graph."""
        import networkx as nx

        for key in self.type_child_map.keys():
            tree.add_edge(self.prefix, self.type_child_map[key].prefix, msg_type=key)
            self.type_child_map[key].add_edges(tree)

        nx.set_node_attributes(
            tree, values={self.prefix: self.visit_counter}, name="counter"
        )

    def to_dict(self):
        res = {}
        res["counter"] = self.visit_counter
        res["prefix"] = self.prefix
        res["childs"] = {}
        for key in self.type_child_map:
            res["childs"][key] = self.type_child_map[key].to_dict()

        return res

    @staticmethod
    def from_dict(src):
        res = Node(src["prefix"])
        res.visit_counter = src["counter"]
        for msg_type in src["childs"]:
            res.type_child_map[msg_type] = Node.from_dict(src["childs"][msg_type])

        return res
