# -*- coding: utf-8 -*-

import sys, os, re
from uuid import uuid4
from tree import Tree
from hyponym_generator import HyponymGenerator

##### Default Settings
COUNTS_DIR = '/media/New Volume/Datastore/Natural Language/'
WHITE_LIST = 'whitelist.csv'
DEFAULT_LIMIT = 50000
DEFAULT_DEPTH = 5
DEFAULT_SYNSETS = 3


##### JSON Dependent variables
JS_DIR = ''


class JsonTree(Tree):
	
	
	def write_json(self,parent):
		child_format = []
		queue = self[parent].fpointer
		if len(queue) > 0:
			print str(queue)
			for child in queue:
				child_format.append(self.write_json(child))  # recursive call
			children = str(child_format)
			json_format = """{{"id": "{1}", "text" : "{0}", "icon" : "string", "state" : {{ "opened" : true, "disabled"  : false, "selected" : false}}, "children" : {2}, "li_attr" : [], "a_atrr" : [] }}""".format(parent, str(uuid4().hex), children)
		else:
			json_format = """{{"id": "{1}", "text" : "{0}", "icon" : "string", "state" : {{ "opened" : true, "disabled"  : false, "selected" : false}}, "children" : [], "li_attr" : [], "a_atrr" : [] }}""".format(parent, str(uuid4().hex))
		return json_format

	
	def write(self, child, parent):
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
		unigram_file = os.path.join(COUNTS_DIR, 'Google {0}-grams/{0}-gram total.txt'.format(1))
		with open(unigram_file, "r") as unigrams:
			unigrams = unigrams.readlines()
			for unigram in unigrams:
				unigram, frequency = unigram.split('\t')
				frequency = int(frequency)
				if frequency >= self.frequency_limit:
					self.unigram_frequencies[unigram] = frequency
			del unigrams
		
		with open(WHITE_LIST, "r") as whitelist:
			whiteline = whitelist.readlines()
			for line in whiteline:
				wwords = line.split(',')
				for wword in wwords:
					self.whitewords.append(wword.strip().lower())
			
	def set_tree(self):
		self.tree = JsonTree()
		
	
	def final_menu(self, word): ##################################################################################################ABSTRACT AWAY
			jinput = raw_input("Please input the parent's name (from db) for this tree\n")
			tree_json = self.tree.write(child=word, parent=jinput)
			j_filename = word
			jjinput = raw_input("Please input the file name for this file or nothing for the default {0}.js".format(word))
			if jjinput != '':
				j_filename = word
			file_path = os.path.join(JS_DIR, '{0}.js'.format(j_filename))
			output_file = open(file_path, 'wb')
			output_file.write(tree_json)
			

if __name__ == '__main__':
	hg = JSGenerator()
	hg.run_menus()
