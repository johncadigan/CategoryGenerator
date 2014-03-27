import os

CURRENT_DIR = os.path.dirname(__file__)

###Default Settings
DATA_DIR = 'data'
COUNTS_FILE = 'word-totals.txt'
WHITE_LIST = 'whitelist.csv'
DEFAULT_LIMIT = 50000
DEFAULT_DEPTH = 5
DEFAULT_SYNSETS = 3

##### DB Dependent variables
MYSQL_URL = 'mysql://user:password@host/database?charset=utf8'
from sqlalchemy import *
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, aliased
from tree import Tree
from hyponym_generator import HyponymGenerator
from model import *


class DBTree(Tree):
	
	
	def write(self, child, parent): #Overriden function for db version
		Session = sessionmaker(bind=create_engine(MYSQL_URL))
		DBSession = Session()
		parent_category = DBSession.query(Category).filter(Category.name==parent).first()
		child_category = Category(name=child)
		child_category.parent = parent_category
		DBSession.add(child_category)
		DBSession.commit()
		queue = self[child].fpointer
		if self[child].expanded:
			for element in queue:
				self.write(element, child_category.name)  # recursive call
				


class DBGenerator(HyponymGenerator):
	
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
			
	
	def set_tree(self): #Overriden function for db version
		self.tree = DBTree()
	
	
	def final_menu(self, word): #Overriden function for db version
		Session = sessionmaker(bind=create_engine(MYSQL_URL))
		DBSession = Session()
		ppinput = "1"
		while ppinput == "1":
			pinput = raw_input("Please input the potential name of a grandparent in db to find parents\n")
			parent = DBSession.query(Category).filter(Category.name == pinput).first()
			descendants = DBSession.query(Category.name).filter(Category.left > parent.left).filter(Category.right < parent.right).all()
			print "{0} \n \t {1}".format(parent.name, str(descendants))
			ppinput = raw_input("Please input the name for tree's parent. Input 1 to look at other parts of database tree\n")
			if ppinput != "1":
				self.tree.write(child=word, parent=ppinput)

if __name__ == '__main__':
	hg = DBGenerator()
	hg.run_menus()
