import sys, os, urllib2, re, datetime, md5
from urlparse import urlparse

try:
	from BeautifulSoup import BeautifulSoup
except ImportError:
	print('BeautifulSoup is required for Sitedown.')
	sys.exit()

try:
	from Search import Search
except ImportError:
	print('Sitedown Search module is missing.')
	sys.exit()


class Sitedown:

	DIR_SEP = '/'

	CSS_EXT = '.css'
	JS_EXT = '.js'

	RESOURCES_DIR = './resources/'

	# A list of errors that have occurred during the process.
	errors = []

	def __init__(self, root_url, output_dir = None):

		self.root_url = root_url
		self.root_url_parsed = urlparse(root_url)

		self.output_dir = output_dir

		if not self.output_dir:
			now = datetime.datetime.now()
			self.output_dir = '.'+Sitedown.DIR_SEP+self.root_url_parsed.netloc+'_'+now.year+now.month+now.day+'_'+now.hour+now.minute+now.second+now.microsecond

		# A dictionary of all the resourcees
		self.resources = []

		# A dictionary of urls that need to be downloaded. The keys
		# are the original urls and the values are the location they
		# will be downloaded to.
		self.to_download = {}

		# The search object
		self.search = None

		# At the moment, this does nothing. But it will as Sitedown
		# becomes feature complete.
		self.verbose = False

	def go(self):

		self.__crawl()
		self.__find_resources()

		# Done searching, create necessary directories to dump
		# downloaded data.

		if not os.path.exists(self.output_dir):
			os.makedirs(self.output_dir)

		self.__downlaod_resouces()

	def verbose_on(self):

		self.verbose = True

	def verbose_off(self):

		self.verbose = False

	def __crawl(self):

		init_state = self.State(url = self.root_url)
		self.search = Search(self.root_url, init_state=init_state, goal_fn=lambda N: False, new_node=Search.Node)

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
						url = r[attr]
						new_url = self.__convert_path(url)
						self.to_download[url] = new_url
						r[attr] = new_url


	def __download_css(self, css):
		'''Want to add all references to resources to the download list
		and convert the paths, given the css. Returns a list of resources
		referenced in the CSS file and the new contents of the CSS file.'''

		# TODO: write a faster way of doing this. The following algorithm
		# should be pretty inefficient for large CSS files. Not ideal at all.

		# Find all referenced URLs for properties like background and @import
		pattern = r'url\([\'"]?(.*?)[\'"]?\)'
		matches = re.findall(pattern, css, flags=re.IGNORECASE)

		for url in matches:
			new_url = Sitedown.get_save_location(url)
			css.replace(url, new_url)

		return matches, css

	def __downlaod_resouces(self):
		'''Download all the necessary resources: css, js, images.'''

		download_urls = self.to_download.keys()

		while download_urls:
			url = download_urls.pop()
			contents = Sitedown.get_contents_at_url(url)

			if url.endswith(Sitedown.CSS_EXT):

				# Want to get all resources that CSS files refer to as well
				# and while we also alter the contents of the CSS file --
				# we prepare it for offline use.
				css_resources, contents = self.__download_css(contents)

				for resource in css_resources:
					self.to_download[resource] = self.__convert_path(resource)
					download_urls.append(resource)

			save_location = Sitedown.get_save_location(url)
			Sitedown.save_resource(save_location, contents)

	def __is_same_website(self, url):
		'''Return True iff url is from the same website as self.root_url'''

		# Don't care about www.
		clean_domain = lambda domain: re.sub(r'^www\.', '', domain, flags=re.IGNORECASE)

		url_parsed = urlparse(url)
		root_url_parsed = self.root_url_parsed

		if not clean_domain(root_url_parsed.netloc) == clean_domain(url_parsed.netloc):
			return False

		# Now we want to make sure that url is "within" the same dir as the root_url.
		# Example:
		# Root URL = http://example.com/a/b/
		# Then http://example.com/a/b/c.html is within root, but /a/c/b.html is not.


		root_path = root_url_parsed.path.lstrip('/')

		if not root_path:
			return True

		other_path = url_parsed.path.lstrip('/')

		root_path_deepest_dir = root_path[:root_path.rfind('/')]		

		return other_path.startswith(root_path_deepest_dir)


	def add_error(Error_object):
		'''Record an error.'''

		Sitedown.errors.append(Error_object)

	def get_errors(self):

		return Sitedown.errors

	def get_save_location(original_url):

	url_parsed = urlparse(original_url)
	path = url_parsed.path

	if not path:
		return ''

	if path[0] == self.DIR_SEP and path[1:]:
		path = path[1]

	file_name, file_ext = os.path.splitext(path)
	new_file_name = hashlib.md5(file_name).hexdigest()

	return self.RESOURCES_DIR+new_file_name+file_ext

	def save_resource(save_location, contents):

		try:
			fp = open(save_location, 'w')
			fp.write(contents)
			fp.close()
		except IOError:
			Sitedown.add_error(Sitedown.Error(Sitedown.Error.SAVE_FILE, {'file':save_location}))


	def get_contents_at_url(url):
		'''Given a URL, return the contents located at URL as a string.
		Returns None on failure.'''

		try:
			contents = urllib2.urlopen(url).read()
		except URLError:
			contents = None
			Sitedown.errors.append(Sitedown.Error(Sitedown.Error.OPEN_URL, {'url':url}))

		return contents


	class State(Search.State):
		'''A state during the site search. Each state is a page on the site. Its
		successors are all the links on the page leading to another page of the
		same site.'''

		def __init__(self, url, G = 0, parent = None):

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
				Sitedown.errors.append(Sitedown.Error(self.Error.PARSE, {'url':url}))
				return succs

			links = self.soup.find_all('a')

			for a in links:

				# Skip if not href attribute or link doesn't refer to another page
				if 'href' not in a or not a['href'] or a['href'][0] == '#':
					continue

				url = a['href']

				# Only a successor if it's on the same website 
				if self.is_same_website(self.root_url, url):
					new_state = Sitedown.State(url, new_G, self)
					succs.append(new_state)

			return succs


		def __str__(self):

			return self.url

		def __hash__(self):

			return self.url

	class Error:

		OPEN_URL = 'Could not open %(url)'
		PARSE = 'Could not parse %(url). Try installing lxml and html5lib'
		SAVE_FILE = 'Could not save file %(file)'

		def __init__(self, error, args):

			self.message = self.error % args

		def __repr__(self):
			return self.message

		def __str__(self):
			return self.message





