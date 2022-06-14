from curses.ascii import NUL
import json
from turtle import st
import numpy as np
import sys

from .Node import Node

import ipal_iids.settings as settings
from ids.ids import MetaIDS


# not finished but a start. Calculates q_min and q_max for one process value
class Task_3_2(MetaIDS):
    _name = "Task_3_2"
    _description = "Probabilistic Suffix Trees"
    _requires = ["train.ipal", "live.ipal"]
    _pst_default_settings = {"N": 3, "Threshold": 0.5, "alert_unknown": False}
    _conn_tree_map = {}  # Maps each conn_id to a Tree
    _conn_window_map = {}
    _last_n = []

    def __init__(self, name=None):
        super().__init__(name=name)
        self._add_default_settings(self._pst_default_settings)

    def train(self, ipal=None, state=None):
        with self._open_file(ipal) as f:
            for line in f.readlines():
                msg = json.loads(line)

                conn_id = self._parse_conn_id(msg)

                # If the connection is new, initialize tree and window:
                if conn_id not in self._conn_window_map:
                    self._conn_window_map[conn_id] = []
                    self._conn_tree_map[conn_id] = Node("")

                # Append new message to window buffer:
                self._conn_window_map[conn_id].append(msg)

                # If the window is not full, we continue with next message:
                if len(self._conn_window_map[conn_id]) < self.settings["N"]:
                    continue
                else:
                    self._conn_tree_map[conn_id].count_sequence(
                        self._conn_window_map[conn_id]
                    )
                    self._conn_window_map[conn_id].pop(0)

    def new_ipal_msg(self, msg):

        # Populate initial window with N messages
        self._last_n.append(msg["type"])
        if len(self._last_n) > self.settings["N"]:
            self._last_n.pop(0)
        if len(self._last_n) < self.settings["N"]:
            return False, None

        # Determine connection identifier
        conn_id = self._parse_conn_id(msg)

        # Evaluate likelihood of sequence
        iter_node = self._conn_tree_map[conn_id]
        likelihood = 0
        for i in range(len(self._last_n)):
            if self._last_n[i] in iter_node.type_child_map:
                iter_node = iter_node.type_child_map[self._last_n[i]]
            else:
                return True, {"Likelihood": likelihood}

        likelihood = (
            iter_node.visit_counter / self._conn_tree_map[conn_id].visit_counter
        )

        return likelihood < self.settings["Threshold"], {"Likelihood": likelihood}

    def save_trained_model(self):
        if self.settings["model-file"] is None:
            return False

        conn_dict_map = {}
        for (peer1, peer2) in self._conn_tree_map:
            conn_dict_map[peer1 + "|" + peer2] = self._conn_tree_map[
                (peer1, peer2)
            ].to_dict()

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
            self._conn_tree_map[conn_id] = Node.from_dict(conn_dict_map[key])

        return True

    def visualize_model(self):
        import networkx as nx
        import matplotlib.pyplot as plt
        from networkx.drawing.nx_pydot import graphviz_layout

        forest = nx.DiGraph()
        for conn_id in self._conn_tree_map:
            self._conn_tree_map[conn_id].add_edges(forest)

        fig, ax = plt.subplots(1)

        int_forest = nx.convert_node_labels_to_integers(
            forest, label_attribute="node_label"
        )
        int_pos = graphviz_layout(int_forest, prog="twopi", root="")
        str_pos = {int_forest.nodes[n]["node_label"]: p for n, p in int_pos.items()}
        nx.draw(forest, pos=str_pos, ax=ax)
        # Draw edge labels:
        edge_labels = nx.get_edge_attributes(forest, "msg_type")
        nx.draw_networkx_edge_labels(forest, pos=str_pos, edge_labels=edge_labels)
        # Draw node labels:
        node_labels = nx.get_node_attributes(forest, "counter")
        nx.draw_networkx_labels(forest, labels=node_labels, pos=str_pos)

        return plt, fig

    def _parse_conn_id(self, msg):
        src_addr = msg["src"].split(":")[0]
        dest_addr = msg["dest"].split(":")[0]
        if src_addr < dest_addr:
            conn_id = (src_addr, dest_addr)
        else:
            conn_id = (dest_addr, src_addr)

        return conn_id
