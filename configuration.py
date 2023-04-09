import ast
import fileinput
import os
import re
import sys
from abc import abstractmethod, ABC
from enum import Enum


class File:
    """
    Parent class that would represent all the files that
    are going to be generated in this project.
    """

    def __init__(self, name=None):
        """
        Initializes all parent class variables that are going to be used
        later on.

        :param name: Name for the file.
        """
        if name is None:
            name = "bot_config"
        self.name = name if not name.endswith(".txt") else name.replace(".txt", "")
        self.path = os.path.join(os.getcwd(), "{0}.txt".format(self.name))
        self.prepare_file()

    def prepare_file(self):
        """
        Prepares the files.

        This depends on the :func:`~configuration.File.file_exists_method` and
        :func:`~configuration.File.file_not_exists_method` that are going to be
        implemented on extending classes.
        """
        if os.path.exists(self.path):
            self.file_exists_method()
        else:
            self.file_not_exists_method()

    @abstractmethod
    def file_exists_method(self):
        """
        This function should be implemented in the extending class since
        :func:`~configuration.File.prepare_files` will call this function
        when the file exists.
        """
        pass

    @abstractmethod
    def file_not_exists_method(self):
        """
        This function should be implemented in the extending class since
        :func:`~configuration.File.prepare_files` will call this function
        when the file does exists.
        """
        pass


class ConfigNode(Enum):
    """
    Enumeration that contains data for all the configuration options

    This contains a tuple. index[0] is the key of the configuration
    and index[2] is the default value of the key when the fil is generated.
    """
    API_KEY = ("API_KEY", "replace this with your eleven labs API key")
    VOICE = ("Voice", "")
    INPUT = ("Input", "")
    OUTPUT = ("Output", "")
    T_MODE = ("T_Mode", "0")

    def get_key(self):
        return self.value[0]

    def get_value(self):
        return self.value[1]


class ConfigFile(File, ABC):
    """
    This class represents the configuration for the bot. Instead of reading the file
    every time we need information from the config file, we just use this class instead.
    """

    def __init__(self, name=None):
        """
        Construct that initializes the super class File and initialize the configuration
        nodes that are parsed from the config file.

        :param: name: name of the file
        """
        super().__init__(name)
        self.nodes = {}
        self.parse_config()

    def parse_config(self):
        """
        Initializes the nodes dictionary.

        This does this by opening the config file with read only permission.
        It then loops through all the lines in the config file and extract
        the key to check if it's one of the keys defined in ConfigNode. If
        it is a key defined in ConfigNode, we then extract the value of that
        key in the file and insert it in the dictionary.
        """
        f = open(self.path, 'r')
        for line in f:
            key = self.__get_key_from_line(line)
            if key != -1 and self.__key_in_nodes(key):
                self.nodes[key] = self.__get_val_from_line(line)
        f.close()

    def get(self, node):
        """
        Get a value of a node

        :param: node: ConfigNode that you want the value of.
        :return: The value of the ConfigNode in the config.
        """
        return self.nodes[node.value[0]].replace("\n", "")

    def get_list_node(self, node):
        """
        Get a node with a value of a list.

        :param node: ConfigNode with a value of list.
        :return: Returns a list if the value of a node looks like a list,
        return empty list otherwise.
        """
        return self._collection_literal_eval(node, '\\[.*?\\]', [])

    def get_tuple_node(self, node):
        """
        Get a node with a tuple value.

        :param node: ConfigNode with a tuple value.
        :return: Returns a tuple if the value of a node looks like a tuple,
        return empty list otherwise.
        """
        return self._collection_literal_eval(node, '\\(.*?\\)', ())

    def get_dict_node(self, node):
        """
        Get a node with a dict value.

        :param node: ConfigNode with a dict value.
        :return: Returns a dict if the value of a node looks like a dict,
        return empty dict otherwise.
        """
        return self._collection_literal_eval(node, '\\{.*?\\}', {})

    def _collection_literal_eval(self, node, regex, fallback):
        """
        Evaluates the value of a node with given arguments

        :param node: The node path.
        :param regex: The regex pattern for the value.
        :param fallback: Default return value if there's no match with regex.
        :return: Returns the evaluated value.
        """
        val = self.nodes[node.get_key()]
        if not re.match(regex, val):
            return fallback
        return ast.literal_eval(val)

    def set(self, node, value):
        """
        Sets a value of node.

        This also changes the file and updates the dictionary in this class.

        :param node: ConfigNode that you want to change the value of
        :param value: The value that you want for the node param.
        """
        for line in fileinput.input(self.path, inplace=True):
            key = self.__get_key_from_line(line)
            if key != -1 and key == node.get_key():
                line = "{} = {}\n".format(key, value)
                self.nodes[key] = value
            sys.stdout.write(line)
        self.reload()

    def reload(self):
        """
        Reloads the config file if the file is updated when the bot is running.
        """
        self.nodes = {}
        self.parse_config()

    def file_exists_method(self):
        """
        Implemented method from the parent class.

        If config file exists, this method just checks if all the defined
        nodes in ConfigNode actually exists in that config file.

        If not, then just write that missing ConfigNode with default value.
        """
        f = open(self.path, 'r+')
        for node in ConfigNode:
            if not self.__node_in_file(f, node):
                f.write("{} = {}\n".format(node.get_key(), node.get_value()))
        f.close()

    def file_not_exists_method(self):
        """
        Implemented method from parent class.

        If config file doesn't exist, just write a new file with all
        default values.
        """
        f = open(self.path, 'w+')
        for node in ConfigNode:
            f.write("{} = {}\n".format(node.get_key(), node.get_value()))
        f.close()

    # Private static Methods
    @staticmethod
    def __get_key_from_line(line):
        """
        Static method to get the key from a line of string.

        Since a config line looks like 'config_key = config_value', just split it with
        split("="), get index 0, and strip it.

        :param line: The line of config that you want to extract the key from.
        :return: The extracted key from the line, and -1 if the line does not have a '='
        """
        if '=' not in line:
            return -1
        return line.split("=")[0].strip()

    @staticmethod
    def __get_val_from_line(line):
        """
        Static method to get the value of a line of string.

        Since a config line looks like 'config_key = config_value', just split it with
        split("="), get index 1, and to preserve the value, strip with lstrip() to remove
        leading space after the '='.

        :param line:
        :return: Return the value of the line, -1 if line doesn't have '='.
        """
        if '=' not in line:
            return -1
        return line.split('=')[1].lstrip()

    @staticmethod
    def __node_in_file(f, node):
        """
        Static method to check if one of the nodes defined in ConfigNode
        could be found in the config file.

        :param f: The config file.
        :param node: Which node do you want to check.
        :return: Returns true if the param node is in the config file, false otherwise.
        """
        for line in f:
            if line.startswith(node.get_key()):
                return True
        return False

    @staticmethod
    def __key_in_nodes(key):
        """
        Static method to check if the key in a config file is defined in ConfigNode.

        :param key: A key that could be found in the config file.
        :return: Returns true if the key is defined in ConfigNode, false otherwise.
        """
        for node in ConfigNode:
            if key == node.get_key():
                return True
        return False
