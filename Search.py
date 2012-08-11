
class Search:

	(DEPTH_FIRST, BREADTH_FIRST, ASTAR, IDASTAR) = (1, 2, 3, 4)

	NULL_HEURISTIC = lambda N: 0

	def __init__(self, init_state, goal_fn, method = None, new_node = None, heuristic_fn = None):

		if not method:
			method = self.ASTAR

		if not new_node:
			new_node = self.Node

		if not heuristic_fn:
			heuristic_fn = self.NULL_HEURISTIC

		self.method = method
		self.state = init_state
		self.goal = goal_fn
		self.heuristic = heuristic_fn
		self.visit = visit_fn
		
		self.new_node = new_node

		self.cycle_check = True
		self.verbose = False

		if self.cycle_check:
			self.cycle_check_hash = {}

	def get_method(self):

		return self.method

	def set_method(self, new_method):

		if 1 <= new_method and new_method <= 4:
			self.meth

	def cycle_check_on(self):
		self.cycle_check = True

	def cycle_check_off(self):
		self.cycle_check = False

	def verbose_on(self):
		self.verbose = True

	def verbose_off(self):
		self.verbose = False

	def get_visited_states(self):
		return self.cycle_check_hash.keys()

	def go(self):

		self.goal_node = self.__search()


	def __search(self):

		OPEN = self.open

		while not OPEN.empty():

			node = OPEN.extract()

			if self.goal(node.state):
				return node

			if self.cycle_check and self.cycle_check_hash[node.state] <= node.G:
				continue

			successors = node.state.successors()

			for succ in successors:

				if (self.cycle_check and succ in self.cc_dictionary) or succ.G >= self.cycle_check_hash[succ]:
					continue

				OPEN.insert(self.new_node(succ, heuristic(succ)))

				if self.cycle_check:
					self.cycle_check_hash[succ] = succ.G

		return None

	class Open:

		def __init__(self, method):

			if method == Search.ASTAR:
				self.open = []
				Node.compare_type = Node.COMPARE_HG
				self.insert = lambda N: heapq.heappush(self.open, N)
				self.extract = lambda: heapq.heappop(self.open)
			elif method == Search.BREADTH_FIRST:
				self.open = deque()
				self.insert = self.open.append
				self.extract = self.open.popleft
			elif method == Search.DEPTH_FIRST:
				self.open = []
				self.insert = self.open.append
				self.extract = self.open.pop
			elif method == Search.IDASTAR:
				self.open = []
				self.insert = self.open.append
				self.extract = self.open.pop

		def empty(self):
			return not self.open


	class State:

		def __init__(self, action, G, parent):

			self.action = action
			self.gval = G
			self.parent = parent

		def successors(self):
			'''Return a list of States that are successors to the current state'''
			raise Search.Error.NOT_IMPLEMENTED

		def __str__(self):
			raise Search.Error.NOT_IMPLEMENTED

		def __hash__(self):
			raise Search.Error.NOT_IMPLEMENTED

		def get_path(self):
			'''Return a list of the states visisted so far to reach this state.'''
			s = self
			states = []
			while s:
				states.append(s)
				s = s.parent
			return states

	class Node:

		COMPARE_H = 1
		COMPARE_G = 2
		COMPARE_HG = 3

		compare_type = COMPARE_H

		def __init__(self, state, H):
			self.state = state
			self.H = H
			self.G = state.G

		def __str__(self):
			raise Search.Error.NOT_IMPLEMENTED

		def __lt__(self, other_node):

			if self.compare_type == COMPARE_HG:

				if self.G + self.H == other_node.G + other_node.H:
					return self.G > other_node.G
				return self.G + self.H < other_node.G + other_node.H

			if self.compare_type == COMPARE_H:
				return self.H < other_node.H

			return self.G < other_node.G



	class Error:

		NOT_IMPLEMENTED = NotImplementedError('Expected to be overridden.')

