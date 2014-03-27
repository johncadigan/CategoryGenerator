
from nltk.corpus import wordnet as wn
import sys, os

CURRENT_DIR = os.path.dirname(__file__)

##### Default Settings
DATA_DIR = 'data'
COUNTS_FILE = 'word-totals.txt'
WHITE_LIST = 'whitelist.csv'
DEFAULT_LIMIT = 50000
DEFAULT_DEPTH = 5
DEFAULT_SYNSETS = 3

class HyponymGenerator():
	
	unigram_frequencies = {}
	frequency_limit = 0
	depth_limit = 0
	synset_limit = 0
	generated_tree = []
	pruned_tree = {}
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
					
		
	def settings(self): #prints settings
		print "Current Settings \t Frequency limit {0} \t Depth limit {1} \t Synset limit {2}".format(self.frequency_limit, self.depth_limit, self.synset_limit)
	
	def change_settings(self):
		rawinput = raw_input("Please input frequency limit, depth limit and synset limit separated by one space each")
		flimit, dlimit, slimit = rawinput.split(' ')
		self.frequency_limit = int(flimit)
		self.depth_limit = int(dlimit)
		self.synset_limit = int(slimit)
		
		#Add only relevant word frequencies
		unigram_file = os.path.join(COUNTS_DIR, 'Google {0}-grams/{0}-gram total.txt'.format(1))
		self.unigram_frequencies = {}
		with open(unigram_file, "r") as unigrams:
			unigrams = unigrams.readlines()
			for unigram in unigrams:
				unigram, frequency = unigram.split('\t')
				frequency = int(frequency)
				if frequency >= self.frequency_limit:
					self.unigram_frequencies[unigram] = frequency
			del unigrams
	
	def find_frequency(self, ngram):
		if len(ngram.split(' ')) == 1:  ##Unigrams
			if self.unigram_frequencies.has_key(ngram):
				return self.unigram_frequencies[ngram]
			else: 
				return 0 ## Unigrams below limit = 0
		else:
			return self.frequency_limit + 1 ## Pass all others

	def get_subtree(self, dpth, prev_synset, word, pos):
		dpth += 1
		if self.find_frequency(word) >= self.frequency_limit:
			if dpth > self.depth_limit:
				return [word]
			possible_synsets = wn.synsets(word, pos=pos)
			if prev_synset:
				sorted_synsets = sorted(possible_synsets, key= lambda ns: prev_synset.lch_similarity(ns))
				sorted_synsets.reverse()
				if len(sorted_synsets) > self.synset_limit:
					top_possible_synsets = sorted_synsets[0:self.synset_limit]
				else:
					top_possible_synsets = sorted_synsets
			else:
				top_possible_synsets = possible_synsets
			for synset in top_possible_synsets:
				possible_hyponyms = [x.name for x in synset.closure(lambda s:s.hyponyms())] 
				if len(possible_hyponyms) > 0:
					hyponym_branches = []
					hyponym_set = []
					for hyponym in possible_hyponyms:
						hyponym_lemma, pos, num = hyponym.split('.')
						hyponym_lemma = hyponym_lemma.replace('_', ' ')
						hyponym_set.append((hyponym_lemma, pos))
					hyponym_set = list(set(hyponym_set))
					sub_tree = []
					for hyponym_lemma, pos in hyponym_set:
						next_results =  self.get_subtree(dpth, synset, hyponym_lemma, pos)
						if next_results != None:
							sub_tree.append([word, next_results])
					return sub_tree
				else:
					return [word]
	
	def print_branches(self, key, dpth):
		print "\t"*(dpth-1)+ "==={0}===".format(self.format_word(key))
		if self.pruned_tree.has_key(key):
			children = []
			child_parents = []
			for child in list(set(self.pruned_tree[key])):
				if self.pruned_tree.has_key(child):
					child_parents.append(child)
				child = self.format_word(child)
				children.append(child)
			print '\t*'*dpth + '->' + str(children)
			for branch in child_parents:
				self.print_branches(branch, dpth+1)
			
	def print_branch(self, key, dpth):
		print "\t"*(dpth-1)+ "==={0}===".format(key)
		if self.pruned_tree.has_key(key):
			children = []
			child_parents = []
			for child in list(set(self.pruned_tree[key])):
				if self.pruned_tree.has_key(child):
					child_parents.append(child)
				child = self.format_word(child)
				children.append(child)
			print '\t*'*dpth + '->' + str(children)


	def print_tree(self, root):
		depth = 0
		self.print_branches(root, 1)
				

	def prune_category_tree(self, dic, lvl, branches): #Turns the lists into a dictionary which is turned into a tree object
		lvl += 1
		dic.setdefault(lvl, []) #Stores words at each level of the tree
		if branches == None:
			return {'': ''}
		for x in branches:
			parent = x[0]
			dic.setdefault(parent, []) #Stores the children of a parent
			if type(x[1:][0]) == list:
				#If second part is a list
				if(len(x[1:][0])) > 0: # if the parent has children
					if type(x[1:][0][0]) == str: #if there are no grandchildren (a list would indicate grandchildren)
						dic[parent].append(x[1:][0][0])
						dic[lvl].append(x[1:][0][0])
					else: #if there are grandchildren
						dic[parent].append(x[1:][0][0][0]) # Adds child
						dic.update(self.prune_category_tree(dic, lvl, x[1:][0])) #runs recursively to add grandchildren
		return dic
			
	
	def add_child(self,parent, child): #Adds a child to a parent
		self.tree.create_node(child, child, parent = parent)
	
	def add_family(self, parent, children): #Adds children to parent
		for child in children:
			self.add_child(parent,child)
	
	def add_entire_family(self, parent): #Adds entire family
		if self.pruned_tree.has_key(parent):
			queue = self.pruned_tree[parent]
			for element in queue:
				self.add_child(parent, element)  
				self.add_entire_family(element)# recursive call
	
	def set_tree(self): #Overriden function
		pass
	
	def final_menu(self): #Overriden function
		pass
	
	def check_whitelist(self, word):
		if self.whitewords.count(word) > 0:
			word += '@'
		return word
	
	
	def format_word(self, word):
		if self.pruned_tree.has_key(word):
			word = self.check_whitelist(word)
			word = "*" + word
		else:
			word = self.check_whitelist(word)
		return word
	
	def run_menus(self):
		cont_prog = 1
		#Continue to use the program
		while cont_prog == 1:
			self.settings()
			cont_generate = 0
			cont_prog = int(raw_input("Would you like to continue using the program?\n 1. Yes\n 2. Change settings \n 3. Quit"))
			if cont_prog == 1:
				cont_generate = 1
			if cont_prog == 2:
				self.change_settings()
				cont_prog = 1
			if cont_prog == 3:
				sys.exit(0)
			
			# Continue to generate trees
			while cont_generate == 1:
				iinput = 1
				if iinput == 1:
					input_list = raw_input('Enter word and part of speech ("n" or "v")\n').split(' ')
					if len(input_list) == 2:
						word, pos = input_list
						self.generated_tree = self.get_subtree(0, None, word, pos)
						self.prune_category_tree(self.pruned_tree, 0, self.generated_tree)
						print self.print_branches(word, 0)
				iinput = int(raw_input("Select task\n 1. Generate a new hyponym category tree \n 2. Finalize current hyponym category tree"))
				if iinput == 2:
					break
			#Finalize a generated tree
			cont_edit = 1
			self.set_tree()
			self.tree.create_node(word, word)  # root node
			flags = {}
			## Flags
			flags.update({'--help': "Display options"})
			flags.update({'--af' : "Add Family: -af x a b c d ....; Add a, b, c d as children of x \n"})
			flags.update({'--ef' : "Edit Family: --ef x ; Edit x and x's generated descendents \n"})
			flags.update({'--ma' : "Manually Add: -ma x y; add y as a child of x \n"})
			flags.update({'--s' : "Show: -s z; show z's descendents in generated tree \n"})
			flags.update({'--f': "Finalize tree for export to file or database"})
			flags.update({'--aa': "Automatically Add: --aa x y; Add y and any of its descendants below x"})
			while cont_edit == 1:
				print "Current Tree"
				self.tree.show(word)
				einput = raw_input("Enter command:" ).split(' ')
				flag = einput[0]
				##Help
				if flag == "--help" or flag == "-help" or flag == "help" or flag == "h":
						for key in flags.keys():
							print "{0} \t {1}".format(key, flags[key])
				#Other options
				if flags.has_key(flag) and len(einput) > 1:
					if flag == "--aa":
						parent = einput[1]
						child = einput[2]
						if parent != word:
							self.add_child(parent, child)
							self.add_entire_family(child)
						if parent == word:
							self.add_entire_family(parent)
					elif  flag =='--s':
						key = einput[1]
						if self.pruned_tree.has_key(key):
							self.print_branches(key, 0)
						else:
							print "Key {0} does not exist".format(key)
					elif flag == "--ma":
						self.add_child(einput[1], einput[2])
					elif flag == "--af":
						parent = einput[1]
						children = einput[2:] 
						self.add_family(parent,children)
					elif flag == '--ef':
						parent = einput[1]
						if self.pruned_tree.has_key(parent):
							children = self.pruned_tree[parent]
							cont_editing = 1 
							while cont_editing != 3:
								cont_editing = int(raw_input("1. Edit parent's name from {0} \n 2. Add or remove children \n {1}\n 3. Add family to tree \n".format(parent, str(children))))
								if cont_editing == 1:
									parent = raw_input("Enter the new name to replace {0}\n".format(parent))
								elif cont_editing == 2:
									edit_children = raw_input("Current children: \n {0}\n Input +name to add -name to remove from list".format(str(children))).split(' ')
									for edit in edit_children:
										if edit[0] == "+":
											children.append(edit[1:])
										elif edit[0] == "-" and children.count(edit[1:]) > 0:
											children.remove(edit[1:])
							grandparent = raw_input("Enter parent for {0} \n".format(parent))
							if grandparent != parent:
								self.add_child(grandparent, parent)
								self.add_family(parent, children)
							else:
								self.add_family(word, children)
						else:
							print "Please input node with children in the generated tree. \n"
				elif flag == '--f':
					self.final_menu(word)
					cont_edit=2
				else:
					print "Please enter correct input:\n"
					for key in flags.keys():
						print "{0} \t {1}".format(key, flags[key])
