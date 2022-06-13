from curses.ascii import NUL
import json
from turtle import st
import numpy as np

import ipal_iids.settings as settings
from ids.ids import MetaIDS


N = 10


#not finished but a start. Calculates q_min and q_max for one process value
class Task_3_2(MetaIDS):
    _name = "Task_3_2"
    _description = "Probabilistic Suffix Trees"
    _requires = ["train.ipal", "live.ipal"]
    _conn_tree_map = {} # Maps each conn_id to a Tree
    _conn_window_map = {}


    def train(self, ipal=None, state=None):
        with self._open_file(ipal) as f:
            for line in f.readlines():
                msg = json.loads(line)

                # Determine connection identifier:
                src_addr = msg["src"].split(":")[0]
                dest_addr = msg["dest"].split(":")[0]
                if src_addr < dest_addr:
                    conn_id = (src_addr, dest_addr)
                else:
                    conn_id = (dest_addr, src_addr)

                # If the connection is new, initialize tree and window:
                if not conn_id in self._conn_window_map:
                    self._conn_window_map[conn_id] = []
                    self._conn_tree_map[conn_id] = Tree()

                # Append new message to window buffer:
                self._conn_window_map[conn_id].append(msg)

                # If the window is not full, we continue with next message:
                if len(self._conn_window_map[conn_id]) < N:
                    continue

                else:
                    self._conn_tree_map[conn_id].count_sequence(self._conn_window_map[conn_id])
                    self._conn_window_map[conn_id].pop(0)


    def new_state_msg(self, msg):
        pass


    def save_trained_model(self):
        if self.settings["model-file"] is None:
            return False

        conn_dict_map = {}
        for (peer1, peer2) in self._conn_tree_map:
            conn_dict_map[peer1 + "|" + peer2] = self._conn_tree_map[(peer1, peer2)].to_dict()

        model = {
            "_name": self._name,
            "settings": self.settings,
            "prob_suffix_trees": conn_dict_map,
        }

        with self._open_file(self._resolve_model_file_path(), mode="wt") as f:
            f.write(json.dumps(model, indent=4) + "\n")

        return True

    def load_trained_model(self):
        if self.settings["model-file"] is None:
            return False

        try:  # Open model file
            with self._open_file(self._resolve_model_file_path(), mode="rt") as f:
                model = json.load(f)
        except FileNotFoundError:
            settings.logger.info(
                "Model file {} not found.".format(str(self._resolve_model_file_path()))
            )
            return False

        # Load model
        assert self._name == model["_name"]
        self.settings = model["settings"]

        conn_dict_map = model["prob_suffix_trees"]
        for key in conn_dict_map:
            conn_id = (key.split("|")[0], key.split("|")[1])
            self._conn_tree_map[conn_id] = Tree.from_dict(conn_dict_map[key])

        return True


    def visualize_model(self):
        import networkx as nx
        import matplotlib.pyplot as plt

        forest = nx.DiGraph()
        next_node_id = 0
        for conn_id in self._conn_tree_map:
            # Find highest node ID in graph:
            for n in forest:
                if n > next_node_id:
                    next_node_id = n + 1
            # Add edges for new Tree:
            (edges, id) = self._conn_tree_map[conn_id].edges(next_node_id)
            forest.add_edges_from(edges)

        fig, ax = plt.subplots(1)

        nx.draw_networkx(forest, arrows=True, ax=ax)

        return plt, fig


class Tree:

    def __init__(self):
        self.visit_counter = 0
        self.type_child_map = {}


    def count_sequence(self, sequence):
        """Move along the nodes given by the sequence of message types and update the counter for each visited node."""
        self.visit_counter += 1
        if len(sequence) == 0:
            return

        next_msg_type = sequence[0]["type"]

        if not next_msg_type in self.type_child_map:
            self.type_child_map[next_msg_type] = Tree()
        self.type_child_map[next_msg_type].count_sequence(sequence[1:])

    def edges(self, next_id):
        """Returns all edges of this subtree."""
        own_id = next_id
        next_id += 1
        res = []
        for key in self.type_child_map.keys():
            res.append((own_id, next_id))
            (sub_tree_edges, id) = self.type_child_map[key].edges(next_id)
            res.extend(sub_tree_edges)
            next_id = id

        return (res, next_id)


    def to_dict(self):
        res = {}
        res["counter"] = self.visit_counter
        res["childs"] = {}
        for key in self.type_child_map:
            res["childs"][key] = self.type_child_map[key].to_dict()

        return res

    @staticmethod
    def from_dict(src):
        res = Tree()
        res.visit_counter = src["counter"]
        for msg_type in src["childs"]:
            res.type_child_map[msg_type] = Tree.from_dict(src["childs"][msg_type])

        return res
