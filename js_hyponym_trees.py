# -*- coding: utf-8 -*-

import sys, os, re
from uuid import uuid4
from tree import Tree
from hyponym_generator import HyponymGenerator



CURRENT_DIR = os.path.dirname(__file__)

##### Default Settings
DATA_DIR = 'data'
COUNTS_FILE = 'word-totals.txt'
WHITE_LIST = 'whitelist.csv'
DEFAULT_LIMIT = 50000
DEFAULT_DEPTH = 5
DEFAULT_SYNSETS = 3


##### JSON Dependent variables
JS_DIR = 'tree_js'


class JsonTree(Tree):
	
	
	def write_json(self,parent): #Recursively writes the tree
		child_format = []
		queue = self[parent].fpointer
		if len(queue) > 0: #if the parent has children
			print str(queue)
			for child in queue:
				child_format.append(self.write_json(child))  # recursively add the children and their children
			children = str(child_format)
			json_format = """{{"id": "{1}", "text" : "{0}", "icon" : "string", "state" : {{ "opened" : true, "disabled"  : false, "selected" : false}}, "children" : {2}, "li_attr" : [], "a_atrr" : [] }}""".format(parent, str(uuid4().hex), children)
		else:
			json_format = """{{"id": "{1}", "text" : "{0}", "icon" : "string", "state" : {{ "opened" : true, "disabled"  : false, "selected" : false}}, "children" : [], "li_attr" : [], "a_atrr" : [] }}""".format(parent, str(uuid4().hex))
		return json_format

	
	def write(self, child, parent): #An overriden version for json to write the entire tree
		json_tree = self.write_json(parent=child)
		json_format = """var TreeData = {{"id": "{1}", "text" : "{0}", "icon" : "string", "state" : {{ "opened" : true, "disabled"  : false, "selected" : false}}, "children" : [{2}], "li_attr" : [], "a_atrr" : [] }};""".format(parent, str(uuid4().hex), json_tree)
		json_format = re.sub("(}\\')", '}', json_format)
		json_format = re.sub("(\\'{)", '{', json_format)
		json_format = json_format.replace('\\', "")
		json_format = json_format.replace("'", "")
		return json_format




class JSGenerator(HyponymGenerator):
	
	whitewords = []
	
	def __init__(self):
		self.frequency_limit = DEFAULT_LIMIT
		self.depth_limit = DEFAULT_DEPTH
		self.synset_limit = DEFAULT_SYNSETS

		#Add only relevant word frequencies
		data_dir = os.path.join(CURRENT_DIR, DATA_DIR)
		unigram_file = os.path.join(data_dir, COUNTS_FILE)
		with open(unigram_file, "r") as unigrams:
			unigrams = unigrams.readlines()
			for unigram in unigrams:
				word, frequency = unigram.split('\t')
				frequency = int(frequency)
				if frequency >= self.frequency_limit:
					self.unigram_frequencies[word] = frequency
			del unigrams
		
		#Add a whitelist of categories already in use
		white_file = os.path.join(data_dir, WHITE_LIST)
		with open(white_file, "r") as whitelist:
			whiteline = whitelist.readlines()
			for line in whiteline:
				wwords = line.split(',')
				for wword in wwords:
					self.whitewords.append(wword.strip().lower())
	
	
	def set_tree(self): #Overriden function for json version
		self.tree = JsonTree()
		
	
	def final_menu(self, word): #Overriden function for json version
			jinput = raw_input("Please input the parent's name for this tree\n")
			tree_json = self.tree.write(child=word, parent=jinput)
			j_filename = word
			jjinput = raw_input("Please input the file name for this file or nothing for the default {0}.js".format(word))
			if jjinput != '':
				j_filename = word
			js_path = os.path.join(CURRENT_DIR, JS_DIR)
			file_path = os.path.join(js_path, '{0}.js'.format(j_filename))
			output_file = open(file_path, 'wb')
			output_file.write(tree_json)
			

if __name__ == '__main__':
	hg = JSGenerator()
	hg.run_menus()
