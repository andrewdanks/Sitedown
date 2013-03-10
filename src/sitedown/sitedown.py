import sys, os, urllib2, re, datetime, hashlib, mimetypes, string
from urlparse import urlparse, urljoin
from httplib import BadStatusLine

try:
    from BeautifulSoup import BeautifulSoup, SoupStrainer
except ImportError:
    print('BeautifulSoup is required for Sitedown.')
    sys.exit()

class Sitedown:

    DEFAULT_OPTIONS = {
        'directory_separator' : '/',

        # List of supported extensions for each resource type
        'css_extensions' : ['.css'],
        'js_extensions' : ['.js'],
        'media_extensions' : ['.gif', '.png', '.jpg', '.tiff', '.svg'],

        # Protocols that will be visited and considered the same
        'valid_protocols' : ['http', 'https'],
        'default_protocol' : 'http',

        # Subdomains that will be stripped from the original domain
        'redundant_subdomains' : ['www'],

        'html_resource_links' : {
            'script' : 'src',
            'link' : 'href',
            'img' : 'src'
        },

        'output_directory' : './',
        'resources_directory' : 'resources/',

        'output_page_extension' : '.html',

        # Whether logging should be outputted to stdout
        'verbose' : False,

        'max_depth' : 25
    }

    def __init__(self, root_url, options={}):

        self.resources_to_download = {}
        self.errors = []
        self.options = {}

        self._init_options(options)
        self._init_root_url(root_url)

        self.current_url = None
        self.current_url_parsed = None

    def _init_root_url(self, url):
        self.root_url = self._format_url(url)
        self.parsed_root_url = urlparse(self.root_url)

    def _init_options(self, options):
        new_options = {}
        for o in Sitedown.DEFAULT_OPTIONS:
            if o in options:
                new_options[o] = options[o]
            else:
                new_options[o] = Sitedown.DEFAULT_OPTIONS[o]
        self.options = new_options

    def _log(self, output):
        if self.options['verbose']:
            print output

    def go(self):

        self._make_directory(self.options['output_directory'])
        self._make_directory(self.options['output_directory'] + self.options['resources_directory'])

        self._search()
        self._download_resources()

    def _download_resources(self):

        while self.resources_to_download:
            to_download = dict(self.resources_to_download)
            for resource_url in self.resources_to_download:
                save_location = self.resources_to_download[resource_url]
                # todo: need a better way to do this; not ideal for large files
                resource_contents = self._get_contents_at_url(resource_url)

                if self._is_css_file(resource_url):
                    new_resources_to_download, resource_contents = self._visit_css_file(resource_contents, resource_url)
                    to_download = self.combine_dicts(to_download, new_resources_to_download)

                self._save_resource(save_location, resource_contents)
                del to_download[resource_url]
            self.resources_to_download = to_download

    def _visit_css_file(self, contents, url):
        
        new_contents = contents
        to_download = {}
        matches = re.findall(r'url\(["\'](.+?)["\']\);', contents, flags=re.IGNORECASE)
        for m in matches:
            download_url = urljoin(url, m)
            to_download[download_url] = self._get_resource_save_location(url)
            new_contents = re.sub(m, to_download[download_url], new_contents)

        return to_download, new_contents

    def combine_dicts(self, dict1, dict2):
        for d in dict2:
            dict1[d] = dict2[d]
        return dict1

    def _visit_url(self, url):

        self._log('Visiting ' + url)
        self.current_url = url
        self.current_url_parsed = urlparse(url)

        page_contents = self._get_contents_at_url(url)
        if not page_contents:
            self._log('No content found at ' + url)
            return []

        parsed_page = self._parse_page(page_contents)
        if not parsed_page:
            self._log('Could not parse page, ' + url)

        new_urls = set()
        links = self._find_links(parsed_page)

        for link in links:
            if self._is_valid_link(link) and self._is_same_site(link['href']):
                new_url = self._format_url(link['href'])
                link['href'] = os.path.basename(new_url) + self.options['output_page_extension']

                new_urls.add(new_url)
                self._log('Adding "' + new_url + '" to queue')

        parsed_page = self._find_resources_in_page(parsed_page)

        new_page_contents = parsed_page.renderContents()
        self._save_resource(self._get_page_save_location(self.current_url), new_page_contents)

        return new_urls

    def _find_resources_in_page(self, parsed_page):

        for resource_element in self.options['html_resource_links']:
            attr = self.options['html_resource_links'][resource_element]

            resources = self._find_elements_with_attr(parsed_page, resource_element, attr)

            for r in resources:

                resource_url = self._format_url(self._fix_url(r[attr]))
                save_location = self._get_resource_save_location(resource_url)
                r[attr] = re.sub(self.options['output_directory'],'',save_location)

                if resource_url not in self.resources_to_download:
                    self.resources_to_download[resource_url] = save_location
                    self._log('Adding "' + resource_url + '" to list of resources to download')

        return parsed_page

    def _get_page_save_location(self, url):
        return self.options['output_directory'] + os.path.basename(url) + self.options['output_page_extension']

    def _get_resource_save_location(self, url):
        return self.options['output_directory'] + self.options['resources_directory'] + self._get_random(5) + os.path.basename(url)

    def _get_random(self, N):
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(N))

    def _search(self):
        init_url = self.root_url
        queue = set([init_url])
        count = 0
        while queue and (self.options['max_depth'] == None or count < self.options['max_depth']):
            next = self._format_url(queue.pop())
            next_urls = self._visit_url(next)
            queue = queue.union(next_urls)
            count += 1

    def _is_same_site(self, url):

        parsed_url = urlparse(self._format_url(url))
        path = self._format_path(parsed_url.path)

        if not parsed_url.scheme and not parsed_url.netloc and (not path or path.startswith(self.options['directory_separator'])):
            return True
        if parsed_url.netloc == self.parsed_root_url.netloc:
            return True
        return False

    def _is_valid_link(self, link):
        if link['href'] and not link['href'].startswith('#'):
            for ext in self.options['media_extensions']:
                if link['href'].endswith(ext):
                    return False
            return True
        return False

    def _is_css_file(self, url):
        for ext in self.options['css_extensions']:
            if url.endswith(ext):
                return True
        return False

    def _parse_page(self, page_contents):
        try:
            soup = BeautifulSoup(page_contents)
        except HTMLParser.HTMLParseError, e:
            soup = None
            self._add_error(e)
        return soup

    def _find_links(self, parsed_page):
        return self._find_elements_with_attr(parsed_page, 'a', 'href')

    def _find_elements_with_attr(self, parsed_page, element, attr):
        return parsed_page.findAll(element, attrs={attr : re.compile('.+')})

    def _get_contents_at_url(self, url):
        try:
            contents = urllib2.urlopen(url).read()
        except (urllib2.URLError, urllib2.HTTPError, BadStatusLine, ValueError), e:
            contents = None
            self._add_error(e)
        return contents

    def _fix_url(self, url):

        if url.startswith('://'):
            url = self.options['default_protocol'] + url

        return url

    def _format_url(self, url):

        if not url:
            return self.root_url

        dir_sep = self.options['directory_separator']

        parsed_url = urlparse(url)

        if not parsed_url.netloc and not parsed_url.scheme:
            url = self.root_url + dir_sep + url.lstrip(dir_sep)
            parsed_url = urlparse(url)

        formatted_url = parsed_url.scheme + '://'

        domain = parsed_url.netloc
        for subdomain in self.options['redundant_subdomains']:
            domain = re.sub(r'^' + subdomain + r'\.', '', domain, flags=re.IGNORECASE)

        formatted_url += domain

        path = parsed_url.path.rstrip(dir_sep)

        formatted_url += path

        return formatted_url

    def _format_path(self, path):

        dir_sep = self.options['directory_separator']

        parts = path.split(dir_sep)
        formatted_path = dir_sep if path.startswith(dir_sep) else ''
        for part in parts:
            if part:
                formatted_path += part + dir_sep
        return formatted_path

    def _save_resource(self, save_location, contents):
        try:
            fp = open(save_location, 'wb')
            fp.write(contents)
            fp.close()
            self._log('Saved file to ' + save_location)
        except (IOError, TypeError), e:
            self._add_error(e)
            self._log('Error saving file to ' + save_location + ' because ' + str(e))

    def _make_directory(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
            self._log('Create directory, ' + path)

    def _add_error(self, e):
        self._log('Error: ' + str(e))
        self.errors.append(e)

    def get_errors(self):
        return self.errors

if __name__ == '__main__':

    sd = Sitedown('http://futilitycloset.com', {'verbose': True,
                                                'output_directory' : './sandbox/',
                                                'max_depth' : None
                                                })
    sd.go()

