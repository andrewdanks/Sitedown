import sys, os, urllib2, re, datetime
from pyquery import pyquery
from urlparse import urlparse
from BeautifulSoup import BeautifulSoup
from Search import Search

class Sitedown:

	DIR_SEP = '/'
	RESOURCES_DIR = './resources/'

	CSS_EXT = '.css'
	JS_EXT = '.js'

	# A list of errors that have occurred during the process.
	errors = []

	def __init__(self, root_url, output_dir = None):

		self.site_url = root_url
		self.site_url_parsed = urlparse(root_url)

		self.output_dir = output_dir

		if not self.output_dir:
			now = datetime.datetime.now()
			self.output_dir = '.'+self.DIR_SEP+self.site_url_parsed.netloc+'_'+now.year+now.month+now.day+'_'+now.hour+now.minute+now.second+now.microsecond

		# A dictionary of all the resourcees
		self.resources = []

		# A dictionary of urls that need to be downloaded. The keys
		# are the original urls and the values are the location they
		# will be downloaded to.
		self.to_download = {}

		# The search object
		self.search = None

	def go(self):

		self.__crawl()
		self.__find_resources()

		# Done searching, create necessary directories to dump
		# downloaded data.

		if not os.path.exists(self.output_dir):
			os.makedirs(self.output_dir)

		self.__downlaod_resouces()

	def __crawl(self):

		init_state = self.State(url = self.root_url, G=0)
		self.search = Search(self.root_url, init_state=init_state, goal_fn=lambda N: False, new_node=self.SitedownNode)

	def __find_resources():
		'''At this point, the search is complete, and we want to go through
		all the States (which has the parsed HTML object) to discover resources
		that will be downloaded later. Such resources just include images, css,
		and JavaScript'''

		# The key is the element we want to look for, and the value is the attribute
		# we want the value for.
		types = {'script':'src', 'link':'href', 'img':'src'}

		for state in self.search.get_visited_states():
			soup = state.soup
			for t in types:
				attr = types[t]
				resources = soup.find_all(t)
				for r in resources:
					if attr in r:
						src = r[attr]
						new_src = self.__convert_path(src)
						self.to_download[src] = new_src
						r[attr] = new_src


	def __visit_css_page(self, css):
		'''Want to add all references to resources to the download list
		and convert the paths'''

		pattern = r'url\([\'"]?(.*?)[\'"]?\)'


	def get_contents_at_url(url):
		'''Given a URL, return the contents located at URL as a string.
		Returns None on failure.'''

		try:
			contents = urllib2.urlopen(url).read()
		except URLError:
			contents = None
			Sitedown.errors.append(Sitedown.Error(Sitedown.Error.OPEN_URL, url))
		return contents


	def __downlaod_resouces(self):
		'''Download all the necessary resources: css, js, images.'''

		download_urls = self.to_download.keys()

		while download_urls:
			url = download_urls.pop()
			contents = Sitedown.get_contents_at_url(url)

			# Want to get all resources that CSS files refer to as well.
			if url.endswith(Sitedown.CSS_EXT):

				(css_resources, contents) = self.__download_css(contents)
				for resource in css_resources:
					self.to_download[resource] = self.__convert_path(resource)
					download_urls.append(resource)




	def __convert_path(self, url):

		url_parsed = urlparse(url)
		path = url_parsed.path

		if not path:
			return ''

		if path[0] == DIR_SEP and len(path) > 1:
			path = path[1]

		return self.RESOURCES_DIR + path.replace(DIR_SEP, '__')
		

	def is_same_website(self, url):
		'''Return True iff url is from the same website as self.site_url'''

		url_parsed = urlparse(url)

		domain = self.__clean_domain(url_parsed.netloc)
		site_domain = self.__clean_domain(root_url_parsed.netloc)

		return domain == site_domain

	def __clean_domain(self, domain):
		''' '''

		cleaned = re.sub(r'^www\.', '', domain, flags=re.IGNORECASE)
		return cleaned

	class Node(Search.Node):

		def __init__(self, state, H):

			Search.Node.__init__(state, H)
			self.state = state
			self.H = H


	class State(Search.State):
		''' '''

		def __init__(self, url, G, parent = None):

			Search.State.__init__(self, url, G, parent)

			self.url = url
			self.G = G
			self.parent = parent

		def successors(self):
			'''This is the function called upon visiting a node, when we want to get what
			states can be reached by this one. This is essentially extracting all the links'''

			succs = []

			new_G = self.G + 1

			# Download page contents:
			page_contents = Sitedown.get_contents_at_url(self.url)

			if not page_contents:
				return succs

			# Parse the HTML page:
			try:
				self.soup = BeautifulSoup(page_contents)
			except HTMLParser.HTMLParseError:
				self.errors.append(self.Error(self.Error.PARSE, url))
				return succs

			links = self.soup.find_all('a')

			for a in links:

				if 'href' not in a:
					continue

				url = a['href']

				# Only a successor if it's on the same website 
				if self.Sitedown.is_same_website(url):
					new_state = self.State(self.Sitedown, url, new_G, self)
					succs.append(new_state)

			return succs


		def __str__(self):

			return self.url

		def __hash__(self):

			return self.url

	class Error:

		OPEN_URL = 'Could not open %'
		PARSE = 'Could not parse %. Try installing lxml and html5lib'

		def __init__(self, error, args):

			self.message = self.__format(error, args)

		def __format(self, strng, args):

			i = 0
			L = len(args)
			last_s = None
			new_strng = ''
			for s in strng:
				if s == '%' and last_s != '\\' and i < L:
					s = args[i]
					i += 1
				new_strng.append(s)
				last_s = s

			return new_strng


		def __repr__(self):
			return self.message

		def __str__(self):
			return self.message




# class HTMLRegex:

# 	def get(element, attributes):

# 		quote_pattern = r'["']'
# 		space_pattern = r'\s+'

# 		pattern = r'<'+element

# 		for attr in attributes:
# 			pattern += space_pattern+attr+space_pattern+r'='+space_pattern+quote_pattern+'(.*?)'+quote_pattern

# 		pattern += r'.*?>'








