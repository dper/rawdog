# rawdog: RSS aggregator without delusions of grandeur.
#
# Copyright 2003-2021 Adam Sampson <ats@offog.org>
# Copyright 2022 Douglas Perkins
#
# https://github.com/dper/rawdog/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from six.moves import map
import six
from six.moves import range
VERSION = "3.3"
HTTP_AGENT = "rawdog/" + VERSION
STATE_VERSION = 2

import rawdoglib.feedscanner
from rawdoglib.persister import Persistable, Persister

from io import StringIO
import base64
import calendar
import cgi
import feedparser
import getopt
import hashlib
import html
import locale
import os
import re
import socket
import string
import sys
import threading
import time
import types
import six.moves.urllib.request, six.moves.urllib.error, six.moves.urllib.parse
import six.moves.urllib.parse

try:
	import mx.Tidy as mxtidy
	print("mxTidy not found.")
except:
	mxtidy = None

try:
	_resolveRelativeURIs = feedparser.urls.resolve_relative_uris
except AttributeError:
	_resolveRelativeURIs = feedparser._resolveRelativeURIs
try:
	_HTMLSanitizer = feedparser.sanitizer._HTMLSanitizer
except AttributeError:
	_HTMLSanitizer = feedparser._HTMLSanitizer

persister = None
system_encoding = None

def get_system_encoding():
	"""Get the system encoding."""
	return system_encoding

def safe_ftime(format, t):
	"""Format a time value into a string in the current locale (as
	time.strftime), but encode the result as ASCII HTML."""
	try:
		u = time.strftime(format, t)
	except ValueError as e:
		u = "(bad time %s; %s)" % (repr(t), str(e))
	return encode_references(u)

def format_time(secs, config):
	"""Format a time and date nicely."""
	try:
		t = time.localtime(secs)
	except ValueError as e:
		return "(bad time %s; %s)" % (repr(secs), str(e))
	format = config["datetimeformat"]
	if format is None:
		format = config["dayformat"] + " " + config["timeformat"]
	return safe_ftime(format, t)

def encode_references(s):
	"""Encode characters in a Unicode string using HTML references."""

	high_char_re = re.compile(r'[^\000-\177]')

	def encode(m):
		return "&#" + str(ord(m.group(0))) + ";"
	return high_char_re.sub(encode, s)

def sanitise_html(html, baseurl, inline, config):
	"""Attempt to turn arbitrary feed-provided HTML into something
	suitable for safe inclusion into the rawdog output. The inline
	parameter says whether to expect a fragment of inline text, or a
	sequence of block-level elements."""

	block_level_re = re.compile(r'^\s*<(p|h1|h2|h3|h4|h5|h6|ul|ol|pre|dl|div|noscript|blockquote|form|hr|table|fieldset|address)[^a-z]', re.I)

	if html is None:
		return None

	html = encode_references(html)
	type = "text/html"

	# sgmllib handles "<br/>/" as a SHORTTAG; this workaround from
	# feedparser.
	html = re.sub(r'(\S)/>', r'\1 />', html)

	# sgmllib is fragile with broken processing instructions (e.g.
	# "<!doctype html!>"); just remove them all.
	html = re.sub(r'<![^>]*>', '', html)

	html = _resolveRelativeURIs(html, baseurl, "UTF-8", type)
	p = _HTMLSanitizer("UTF-8", type)
	p.feed(html)
	html = p.output()

	if not inline:
		# If we're after some block-level HTML and the HTML doesn't
		# start with a block-level element, then insert a <p> tag
		# before it. This still fails when the HTML contains text, then
		# a block-level element, then more text, but it's better than
		# nothing.
		if block_level_re.match(html) is None:
			html = "<p>" + html

	args = {
		"numeric_entities": 1,
		# In tidy 0.99 these are ASCII; in tidy 5, UTF-8.
		"input_encoding": "ascii",
		"output_encoding": "ascii",
		"output_html": 1,
		"output_xhtml": 0,
		"output_xml": 0,
		"indent": 0,
		"tidy-mark": 0,
		"alt-text": "",
		"doctype": "strict",
		"force-output": 1,
		# In tidy 0.99, wrap=0 means don't wrap.
		# In tidy 5, wrap=0 means wrap to width 0.
		"wrap": 68,
		}
	if mxtidy is not None:
		output = mxtidy.tidy(html, None, None, **args)[2]
	else:
		# No Tidy bindings installed -- do nothing.
		output = "<body>" + html + "</body>"
	html = output[output.find("<body>") + 6
	              : output.rfind("</body>")].strip()

	return html

def select_detail(details):
	"""Pick the preferred type of detail from a list of details."""
	TYPES = {
		"text/html": 30,
		"application/xhtml+xml": 20,
		"text/plain": 10,
		}

	if details is None:
		return None
	if type(details) is not list:
		details = [details]

	ds = []
	for detail in details:
		ctype = detail.get("type", None)
		if ctype is None:
			continue
		if ctype in TYPES:
			score = TYPES[ctype]
		else:
			score = 0
		if detail["value"] != "":
			ds.append((score, detail))
	ds.sort()

	if len(ds) == 0:
		return None
	else:
		return ds[-1][1]

def detail_to_html(details, inline, config, force_preformatted=False):
	"""Convert a detail hash or list of detail hashes as returned by
	feedparser into HTML."""
	detail = select_detail(details)
	if detail is None:
		return None

	if force_preformatted:
		h = "<pre>" + html.escape(detail["value"]) + "</pre>"
	elif detail["type"] == "text/plain":
		h = html.escape(detail["value"])
	else:
		h = detail["value"]

	return sanitise_html(h, detail["base"], inline, config)

def author_to_html(entry, feedurl, config):
	"""Convert feedparser author information to HTML."""
	author_detail = entry.get("author_detail")

	if author_detail is not None and "name" in author_detail:
		name = author_detail["name"]
	else:
		name = entry.get("author")

	url = None
	fallback = "author"
	if author_detail is not None:
		if "href" in author_detail:
			url = author_detail["href"]
		elif "email" in author_detail and author_detail["email"] is not None:
			url = "mailto:" + author_detail["email"]
		if "email" in author_detail and author_detail["email"] is not None:
			fallback = author_detail["email"]
		elif "href" in author_detail and author_detail["href"] is not None:
			fallback = author_detail["href"]

	if name == "":
		name = fallback

	if url is None:
		h = name
	else:
		h = "<a href=\"" + html.escape(url) + "\">" + html.escape(name) + "</a>"

	# We shouldn't need a base URL here anyway.
	return sanitise_html(h, feedurl, True, config)

def string_to_html(s, config):
	"""Convert a string to HTML."""
	return sanitise_html(html.escape(s), "", True, config)

template_re = re.compile(r'(__[^_].*?__)')
def fill_template(template, bits):
	"""Expand a template, replacing __x__ with bits["x"], and only
	including sections bracketed by __if_x__ .. [__else__ ..]
	__endif__ if bits["x"] is not "". If not bits.has_key("x"),
	__x__ expands to ""."""

	f = StringIO()
	if_stack = []
	def write(s):
		if not False in if_stack:
			f.write(s)

	for part in template_re.split(template):
		if part.startswith("__") and part.endswith("__"):
			key = part[2:-2]
			if key.startswith("if_"):
				k = key[3:]
				if_stack.append(k in bits and bits[k] != "")
			elif key == "endif":
				if if_stack != []:
					if_stack.pop()
			elif key == "else":
				if if_stack != []:
					if_stack.append(not if_stack.pop())
			elif key in bits:
				write(bits[key])
		else:
			write(part)
	v = f.getvalue()
	f.close()
	return v

file_cache = {}
def load_file(name):
	"""Read the contents of a template file, caching the result so we don't
	have to read the file multiple times. The file is assumed to be in the
	system encoding; the result will be an ASCII string."""
	if name not in file_cache:
		try:
			f = open(name)
			data = f.read()
			f.close()
		except IOError:
			raise ConfigError("Can't read template file: " + name)

		data = encode_references(data)
		file_cache[name] = data.encode(get_system_encoding())
	return file_cache[name]

def write_ascii(f, s, config):
	"""Write the string s, which should only contain ASCII characters."""
	try:
		f.write(s)
	except UnicodeEncodeError as e:
		print("Error encoding output as ASCII; UTF-8 has been written instead.\n", e)
		f.write(s.encode("UTF-8"))

def short_hash(s):
	"""Return a human-manipulatable 'short hash' of a string."""
	b = s.encode('utf-8')
	return hashlib.sha1(b).hexdigest()[-8:]

def ensure_unicode(value, encoding):
	"""Convert a structure returned by feedparser into an equivalent where
	all strings are represented as fully-decoded unicode objects."""

	if isinstance(value, str):
		return value
	elif isinstance(value, six.text_type) and type(value) is not six.text_type:
		# This is a subclass of unicode (e.g.  BeautifulSoup's
		# NavigableString, which is unpickleable in some versions of
		# the library), so force it to be a real unicode object.
		return six.text_type(value)
	elif isinstance(value, dict):
		d = {}
		for (k, v) in list(value.items()):
			d[k] = ensure_unicode(v, encoding)
		return d
	elif isinstance(value, list):
		return [ensure_unicode(v, encoding) for v in value]
	else:
		return value

class BasicAuthProcessor(six.moves.urllib.request.BaseHandler):
	"""urllib2 handler that does HTTP basic authentication
	or proxy authentication with a fixed username and password."""

	def __init__(self, user, password, proxy=False):
		self.auth = base64.b64encode(user + ":" + password)
		if proxy:
			self.header = "Proxy-Authorization"
		else:
			self.header = "Authorization"

	def http_request(self, req):
		req.add_header(self.header, "Basic " + self.auth)
		return req

	https_request = http_request

class DisableIMProcessor(six.moves.urllib.request.BaseHandler):
	"""urllib2 handler that disables RFC 3229 for a request."""

	def http_request(self, req):
		# Request doesn't provide a method for removing headers --
		# so overwrite the header instead.
		req.add_header("A-IM", "identity")
		return req

	https_request = http_request

class ResponseLogProcessor(six.moves.urllib.request.BaseHandler):
	"""urllib2 handler that maintains a log of HTTP responses."""

	# Run after anything that's mangling headers (usually 500 or less), but
	# before HTTPErrorProcessor (1000).
	handler_order = 900

	def __init__(self):
		self.log = []

	def http_response(self, req, response):
		entry = {
			"url": req.get_full_url(),
			"status": response.getcode(),
			}
		location = response.info().get("Location")
		if location is not None:
			entry["location"] = location
		self.log.append(entry)
		return response

	https_response = http_response

	def get_log(self):
		return self.log

class Feed:
	"""An RSS feed."""

	non_alphanumeric_re = re.compile(r'<[^>]*>|\&[^\;]*\;|[^a-z0-9]')

	def __init__(self, url):
		self.url = url
		self.period = 30 * 60
		self.args = {}
		self.etag = None
		self.modified = None
		self.last_update = 0
		self.feed_info = {}

	def is_timeout_exception(self, exc):
		"""Return True if the exception suggests a timeout occurred."""

		timeout_re = re.compile(r'timed? ?out', re.I)

		if exc is None:
			return False

		if isinstance(exc, socket.timeout):
			return True

		# Since urlopen throws away the original exception object,
		# we have to look at the stringified form to tell if it was a timeout.
		#
		# The message we're looking for is something like:
		#   <urlopen error _ssl.c:495: The handshake operation timed out>
		return timeout_re.search(str(exc)) is not None

	def needs_update(self, now):
		"""Return True if it's time to update this feed, or False if
		its update period has not yet elapsed."""
		return (now - self.last_update) >= self.period

	def get_state_filename(self):
		return "feeds/%s.state" % (short_hash(self.url),)

	def fetch(self, rawdog, config):
		"""Fetch the current set of articles from the feed."""

		handlers = []
		logger = ResponseLogProcessor()
		handlers.append(logger)

		proxies = {}
		for name, value in list(self.args.items()):
			if name.endswith("_proxy"):
				proxies[name[:-6]] = value
		if len(proxies) != 0:
			handlers.append(six.moves.urllib.request.ProxyHandler(proxies))

		if "proxyuser" in self.args and "proxypassword" in self.args:
			handlers.append(BasicAuthProcessor(self.args["proxyuser"], self.args["proxypassword"], proxy=True))

		if "user" in self.args and "password" in self.args:
			handlers.append(BasicAuthProcessor(self.args["user"], self.args["password"]))

		if self.get_keepmin(config) == 0 or config["currentonly"]:
			# If RFC 3229 and "A-IM: feed" is used, then there's
			# no way to tell when an article has been removed.
			# So if we only want to keep articles that are still
			# being published by the feed, we have to turn it off.
			handlers.append(DisableIMProcessor())

		url = self.url
		# Turn plain filenames into file: URLs. (feedparser will open
		# plain filenames itself, but we want it to open the file with
		# urllib2 so we get a URLError if something goes wrong.)
		if not ":" in url:
			url = "file:" + url

		parse_args = {
			"etag": self.etag,
			"modified": self.modified,
			"agent": HTTP_AGENT,
			"handlers": handlers,
			}
		# Turn off content-cleaning, as we need the original content
		# for hashing and we'll do this ourselves afterwards.
		if hasattr(feedparser, "api"):
			parse_args["sanitize_html"] = False
			parse_args["resolve_relative_uris"] = False

		try:
			result = feedparser.parse(url, **parse_args)

			# Older versions of feedparser return some kinds of
			# download errors in bozo_exception rather than raising
			# them from feedparser.parse. Normalise this.
			e = result.get("bozo_exception")
			if self.is_timeout_exception(e):
				result = {"rawdog_timeout": e}
			elif isinstance(e, six.moves.urllib.error.URLError):
				result = {"rawdog_exception": e}
		except Exception as e:
			if self.is_timeout_exception(e):
				result = {"rawdog_timeout": e}
			else:
				result = {
					"rawdog_exception": e,
					"rawdog_traceback": sys.exc_info()[2],
					}
		result["rawdog_responses"] = logger.get_log()
		return result

	def update(self, rawdog, now, config, articles, p):
		"""Add new articles from a feed to the collection.
		Returns True if any articles were read, False otherwise."""

		# The feedparser might have thrown an exception,
		# so until we print the error message and return, we
		# can't assume that p contains any particular field.

		responses = p.get("rawdog_responses")
		if len(responses) > 0:
			last_status = responses[-1]["status"]
		elif len(p.get("feed", [])) != 0:
			# Some protocol other than HTTP -- assume it's OK,
			# since we got some content.
			last_status = 200
		else:
			# Timeout, or empty response from non-HTTP.
			last_status = 0

		version = p.get("version")
		if version is None:
			version = ""

		self.last_update = now
		errors = []
		fatal = False
		old_url = self.url

		if len(responses) != 0 and responses[0]["status"] == 301:
			# Permanent redirect(s). Find the new location.
			i = 0
			while i < len(responses) and responses[i]["status"] == 301:
				i += 1
			location = responses[i - 1].get("location")

			# According to RFC 2616, the Location header should be
			# an absolute URI. This doesn't stop the occasional
			# server sending something like "Location: /" or
			# "Location: //foo/bar". If so, fail.
			valid_uri = True
			if location is not None:
				parsed = six.moves.urllib.parse.urlparse(location)
				if parsed.scheme == "" or parsed.netloc == "":
					valid_uri = False

			if not valid_uri:
				errors.append("New URL:     " + location)
				errors.append("The feed returned a permanent redirect, but with an invalid new location.")
			elif location is None:
				errors.append("The feed returned a permanent redirect, but without a new location.")
			else:
				errors.append("New URL:     " + location)
				errors.append("The feed has moved permanently to a new URL.")
				rawdog.change_feed_url(self.url, location, config, errors.append)
			errors.append("")

		if "rawdog_timeout" in p:
			errors.append("Timeout while reading feed.")
			errors.append("")
			fatal = True
		elif "rawdog_exception" in p:
			errors.append("Error fetching or parsing feed:")
			errors.append(str(p["rawdog_exception"]))
			errors.append("")
			fatal = True
		elif last_status == 304:
			# The feed hasn't changed.
			return False
		elif last_status in [403, 410]:
			# The feed is disallowed or gone.
			errors.append("The feed has gone.")
			errors.append("You should remove it from your config file.")
			errors.append("")
			fatal = True
		elif last_status / 100 != 2:
			# Some sort of client or server error.
			errors.append("The feed returned an error.")
			errors.append("If this condition persists, you should remove it from your config file.")
			errors.append("")
			fatal = True
		elif version == "" and len(p.get("entries", [])) == 0:
			# feedparser couldn't detect the type of this feed.
			errors.append("The data retrieved from this URL could not be understood as a feed.")
			errors.append("You should check whether the feed has changed URLs or been removed.")
			errors.append("")
			fatal = True

		old_error = "\n".join(errors)

		if len(errors) != 0:
			print("Feed:        ", old_url)
			if last_status != 0:
				print("HTTP Status: ", last_status)
			for line in errors:
				print(line)
			if fatal:
				return False

		# From here, assume a complete feedparser response.
		p = ensure_unicode(p, p.get("encoding") or "UTF-8")

		# No entries means the feed hasn't changed, but for some reason
		# we didn't get a 304 response. Handle it the same way.
		if len(p["entries"]) == 0:
			return False

		self.etag = p.get("etag")
		self.modified = p.get("modified")
		self.feed_info = p["feed"]
		feed = self.url

		article_ids = {}
		# Find IDs for existing articles.
		for (hash, a) in list(articles.items()):
			id = a.entry_info.get("id")
			if a.feed == feed and id is not None:
				article_ids[id] = a

		seen_articles = set()
		sequence = 0
		for entry_info in p["entries"]:
			article = Article(feed, entry_info, now, sequence)
			seen_articles.add(article.hash)
			sequence += 1

			id = entry_info.get("id")
			if id in article_ids:
				existing_article = article_ids[id]
			elif article.hash in articles:
				existing_article = articles[article.hash]
			else:
				existing_article = None

			if existing_article is not None:
				existing_article.update_from(article, now)
			else:
				articles[article.hash] = article

		if config["currentonly"]:
			for (hash, a) in list(articles.items()):
				if a.feed == feed and hash not in seen_articles:
					del articles[hash]

		return True

	def get_html_name(self, config):
		if "title_detail" in self.feed_info:
			r = detail_to_html(self.feed_info["title_detail"], True, config)
		elif "link" in self.feed_info:
			r = string_to_html(self.feed_info["link"], config)
		else:
			r = string_to_html(self.url, config)
		if r is None:
			r = ""
		return r

	def get_html_link(self, config):
		s = self.get_html_name(config)
		if "link" in self.feed_info:
			return '<a href="' + string_to_html(self.feed_info["link"], config) + '">' + s + '</a>'
		else:
			return s

	def get_id(self, config):
		if "id" in self.args:
			return self.args["id"]
		else:
			r = self.get_html_name(config).lower()
			return self.non_alphanumeric_re.sub('', r)

	def get_keepmin(self, config):
		return self.args.get("keepmin", config["keepmin"])

class Article:
	"""An article retrieved from an RSS feed."""

	def __init__(self, feed, entry_info, now, sequence):
		self.feed = feed
		self.entry_info = entry_info
		self.sequence = sequence
		self.date = None

		parsed = entry_info.get("updated_parsed")
		if parsed is None:
			parsed = entry_info.get("published_parsed")
		if parsed is None:
			parsed = entry_info.get("created_parsed")
		if parsed is not None:
			try:
				self.date = calendar.timegm(parsed)
			except OverflowError:
				pass

		self.hash = self.compute_initial_hash()
		self.last_seen = now
		self.added = now

	def compute_initial_hash(self):
		"""Compute an initial unique hash for an article."""
		h = hashlib.sha1()
		def add_hash(s):
			h.update(s.encode("UTF-8"))

		add_hash(self.feed)
		entry_info = self.entry_info
		if "title" in entry_info:
			add_hash(entry_info["title"])
		if "link" in entry_info:
			add_hash(entry_info["link"])
		if "content" in entry_info:
			for content in entry_info["content"]:
				add_hash(content["value"])
		if "summary_detail" in entry_info:
			add_hash(entry_info["summary_detail"]["value"])

		return h.hexdigest()

	def update_from(self, new_article, now):
		"""Update contents from a newer identical article."""
		self.entry_info = new_article.entry_info
		self.sequence = new_article.sequence
		self.date = new_article.date
		self.last_seen = now

	def can_expire(self, now, config):
		return (now - self.last_seen) > config["expireage"]

	def get_sort_date(self, config):
		if config["sortbyfeeddate"]:
			return self.date or self.added
		else:
			return self.added

class DayWriter:
	"""Utility for writing day sections into a series of articles."""

	def __init__(self, file, config):
		self.lasttime = []
		self.file = file
		self.counter = 0
		self.config = config

	def start_day(self, tm):
		self.file.write('<div class="day">\n')
		day = safe_ftime(self.config["dayformat"], tm)
		self.file.write('<h2 class="day">' + day + '</h2>\n')
		self.counter += 1

	def start_time(self, tm):
		self.file.write('<div class="time">\n')
		clock = safe_ftime(self.config["timeformat"], tm)
		self.file.write('<h3 class="time">' + clock + '</h3>\n')
		self.counter += 1

	def time(self, s):
		try:
			tm = time.localtime(s)
		except ValueError:
			# e.g. "timestamp out of range for platform time_t"
			return
		if tm[:3] != self.lasttime[:3] and self.config["daysections"]:
			self.close(0)
			self.start_day(tm)
		if tm[:6] != self.lasttime[:6] and self.config["timesections"]:
			if self.config["daysections"]:
				self.close(1)
			else:
				self.close(0)
			self.start_time(tm)
		self.lasttime = tm

	def close(self, n=0):
		while self.counter > n:
			self.file.write('</div>\n')
			self.counter -= 1

class ConfigError(Exception):
	pass

class Config:
	"""The aggregator's configuration."""

	def __init__(self, locking=True):
		self.locking = locking
		self.files_loaded = []
		self.loglock = threading.Lock()
		self.reset()

	def parse_time(self, value, default="m"):
		"""Parse a time period with optional units (s, m, h, d, w) into a time
		in seconds. If no unit is specified, use minutes by default; specify
		the default argument to change this. Raises ValueError if the format
		isn't recognised."""
		units = {
			"s": 1,
			"m": 60,
			"h": 3600,
			"d": 86400,
			"w": 604800,
			}
		for unit, size in list(units.items()):
			if value.endswith(unit):
				return int(value[:-len(unit)]) * size
		return int(value) * units[default]

	def parse_bool(self, value):
		"""Parse a boolean value (0, 1, false or true)."""
		value = value.strip().lower()
		if value == "0" or value == "false":
			return False
		elif value == "1" or value == "true":
			return True
		else:
			raise ValueError("Bad boolean value: " + value)

	def parse_list(self, value):
		"""Parse a list of keywords separated by whitespace."""
		return value.strip().split(None)

	def parse_feed_args(self, argparams, arglines):
		"""Parse a list of feed arguments."""
		args = {}
		for p in argparams:
			ps = p.split("=", 1)
			if len(ps) != 2:
				raise ConfigError("Bad feed argument in config: " + p)
			args[ps[0]] = ps[1]
		for p in arglines:
			ps = p.split(None, 1)
			if len(ps) != 2:
				raise ConfigError("Bad argument line in config: " + p)
			args[ps[0]] = ps[1]
		for name, value in list(args.items()):
			if name == "allowduplicates":
				args[name] = self.parse_bool(value)
			elif name == "keepmin":
				args[name] = int(value)
			elif name == "maxage":
				args[name] = self.parse_time(value)
		return args

	def reset(self):
		# The config file can override some of these.
		self.config = {
			"feedslist" : [],
			"feeddefaults" : {},
			"defines" : {},
			"outputfile" : "index.html",
			"maxarticles" : 200,
			"maxage" : 0,
			"expireage" : 24 * 60 * 60,
			"keepmin" : 0,
			"dayformat" : "%A %Y-%m-%d",
			"timeformat" : "%I:%M %p",
			"datetimeformat" : "%Y-%m-%d %I:%M %p",
			"showfeeds" : True,
			"timeout" : 30,
			"daysections" : True,
			"timesections" : True,
			"sortbyfeeddate" : False,
			"currentonly" : False,
			"newfeedperiod" : "3h",
			"numthreads": 4,
			}

	def __getitem__(self, key):
		return self.config[key]

	def get(self, key, default=None):
		return self.config.get(key, default)

	def __setitem__(self, key, value):
		self.config[key] = value

	def load(self, filename, explicitly_loaded=True):
		"""Load configuration from a config file."""
		if explicitly_loaded:
			self.files_loaded.append(filename)

		lines = []
		try:
			f = open(filename, "r")
			for line in f:
				stripped = line.strip()
				if stripped == "" or stripped[0] == "#":
					continue
				if line[0] in string.whitespace:
					if lines == []:
						raise ConfigError("First line in config cannot be an argument.")
					lines[-1][1].append(stripped)
				else:
					lines.append((stripped, []))
			f.close()
		except IOError:
			raise ConfigError("Can't read config file: " + filename)

		for line, arglines in lines:
			try:
				self.load_line(line, arglines)
			except ValueError:
				raise ConfigError("Bad value in config: " + line)

	def load_line(self, line, arglines):
		"""Process a configuration directive."""

		l = line.split(None, 1)
		if len(l) == 1 and l[0] == "feeddefaults":
			l.append("")
		elif len(l) != 2:
			raise ConfigError("Bad line in config: " + line)

		# Load template files immediately, so errors show up early.
		if l[0].endswith("template") and l[1] != "default":
			load_file(l[1])

		handled_arglines = False
		if l[0] == "feed":
			l = l[1].split(None)
			if len(l) < 2:
				raise ConfigError("Bad line in config: " + line)
			self["feedslist"].append((l[1], self.parse_time(l[0]), self.parse_feed_args(l[2:], arglines)))
			handled_arglines = True
		elif l[0] == "feeddefaults":
			self["feeddefaults"] = self.parse_feed_args(l[1].split(None), arglines)
			handled_arglines = True
		elif l[0] == "define":
			l = l[1].split(None, 1)
			if len(l) != 2:
				raise ConfigError("Bad line in config: " + line)
			self["defines"][l[0]] = l[1]
		elif l[0] == "outputfile":
			self["outputfile"] = l[1]
		elif l[0] == "maxarticles":
			self["maxarticles"] = int(l[1])
		elif l[0] == "maxage":
			self["maxage"] = self.parse_time(l[1])
		elif l[0] == "expireage":
			self["expireage"] = self.parse_time(l[1])
		elif l[0] == "keepmin":
			self["keepmin"] = int(l[1])
		elif l[0] == "showfeeds":
			self["showfeeds"] = self.parse_bool(l[1])
		elif l[0] == "timeout":
			self["timeout"] = self.parse_time(l[1], "s")
		elif l[0] == "daysections":
			self["daysections"] = self.parse_bool(l[1])
		elif l[0] == "timesections":
			self["timesections"] = self.parse_bool(l[1])
		elif l[0] == "sortbyfeeddate":
			self["sortbyfeeddate"] = self.parse_bool(l[1])
		elif l[0] == "currentonly":
			self["currentonly"] = self.parse_bool(l[1])
		elif l[0] == "newfeedperiod":
			self["newfeedperiod"] = l[1]
		elif l[0] == "numthreads":
			self["numthreads"] = int(l[1])
		else:
			raise ConfigError("Unknown config command: " + l[0])

		if arglines != [] and not handled_arglines:
			raise ConfigError("Bad argument lines in config after: " + line)

class ChangeFeedEditor:
	def __init__(self, oldurl, newurl):
		self.oldurl = oldurl
		self.newurl = newurl
	def edit(self, inputfile, outputfile):
		for line in inputfile:
			ls = line.strip().split(None)
			if len(ls) > 2 and ls[0] == "feed" and ls[2] == self.oldurl:
				line = line.replace(self.oldurl, self.newurl, 1)
			outputfile.write(line)

class FeedFetcher:
	"""Class that will handle fetching a set of feeds in parallel."""

	def __init__(self, rawdog, feedlist, config):
		self.rawdog = rawdog
		self.config = config
		self.lock = threading.Lock()
		self.jobs = set(feedlist)
		self.results = {}

	def worker(self, num):
		rawdog = self.rawdog
		config = self.config

		while True:
			with self.lock:
				try:
					job = self.jobs.pop()
				except KeyError:
					# No jobs left.
					break

			print(num, "- Fetching feed:", job)
			feed = rawdog.feeds[job]
			result = feed.fetch(rawdog, config)

			with self.lock:
				self.results[job] = result

	def run(self, max_workers):
		max_workers = max(max_workers, 1)
		num_workers = min(max_workers, len(self.jobs))

		print("Fetching", len(self.jobs), "feeds using", num_workers, "threads.")
		workers = []
		for i in range(1, num_workers):
			t = threading.Thread(target=self.worker, args=(i,))
			t.start()
			workers.append(t)
		self.worker(0)
		for worker in workers:
			worker.join()
		print("Fetch complete.")
		return self.results

class FeedState(Persistable):
	"""The collection of articles in a feed."""

	def __init__(self):
		Persistable.__init__(self)
		self.articles = {}

class Rawdog(Persistable):
	"""The aggregator itself."""

	def __init__(self):
		Persistable.__init__(self)
		self.feeds = {}
		self.articles = {}
		self.plugin_storage = {}
		self.state_version = STATE_VERSION

	def check_state_version(self):
		"""Check the version of the state file."""
		try:
			version = self.state_version
		except AttributeError:
			version = 1
		return version == STATE_VERSION

	def edit_file(self, filename, editfunc):
		"""Edit a file in place: for each line in the input file, call
		editfunc(line, outputfile), then rename the output file over the input
		file."""
		newname = "%s.new-%d" % (filename, os.getpid())
		oldfile = open(filename, "r")
		newfile = open(newname, "w")
		editfunc(oldfile, newfile)
		newfile.close()
		oldfile.close()
		os.rename(newname, filename)

	def change_feed_url(self, oldurl, newurl, config, error_fn):
		"""Change the URL of a feed."""

		assert oldurl in self.feeds
		if newurl in self.feeds:
			error_fn("Error: New feed URL is already subscribed; please remove the old one")
			error_fn("from the config file by hand.")
			return

		self.edit_file("config", ChangeFeedEditor(oldurl, newurl).edit)

		feed = self.feeds[oldurl]
		# Changing the URL will change the state filename as well,
		# so we need to save the old name to load from.
		old_state = feed.get_state_filename()
		feed.url = newurl
		del self.feeds[oldurl]
		self.feeds[newurl] = feed

		for article in list(self.articles.values()):
			if article.feed == oldurl:
				article.feed = newurl

		error_fn("The config file has been updated automatically.")

	def list(self, config):
		"""List the configured feeds."""
		for url, feed in list(self.feeds.items()):
			feed_info = feed.feed_info
			print(url)
			print("  ID:", feed.get_id(config))
			print("  Hash:", short_hash(url))
			print("  Title:", feed.get_html_name(config))
			print("  Link:", feed_info.get("link"))

	def sync_from_config(self, config):
		"""Update rawdog's internal state to match the
		configuration."""

		seen_feeds = set()
		for (url, period, args) in config["feedslist"]:
			seen_feeds.add(url)
			if url not in self.feeds:
				print("Adding new feed: ", url)
				self.feeds[url] = Feed(url)
				self.modified()
			feed = self.feeds[url]
			if feed.period != period:
				print("Changed feed period: ", url)
				feed.period = period
				self.modified()
			newargs = {}
			newargs.update(config["feeddefaults"])
			newargs.update(args)
			if feed.args != newargs:
				print("Changed feed options: ", url)
				feed.args = newargs
				self.modified()
		for url in list(self.feeds.keys()):
			if url not in seen_feeds:
				print("Removing feed: ", url)

				for key, article in list(self.articles.items()):
					if article.feed == url:
						del self.articles[key]

				del self.feeds[url]
				self.modified()

	def update(self, config, feedurl=None):
		"""Check feeds for new articles and expire old ones."""
		print("Updating...")
		now = time.time()

		socket.setdefaulttimeout(config["timeout"])

		if feedurl is None:
			update_feeds = [url for url in list(self.feeds.keys())
			                    if self.feeds[url].needs_update(now)]
		elif feedurl in self.feeds:
			update_feeds = [feedurl]
			self.feeds[feedurl].etag = None
			self.feeds[feedurl].modified = None
		else:
			print("No such feed: ", feedurl)
			update_feeds = []

		numfeeds = len(update_feeds)
		print("Will update", numfeeds, "feeds.")

		fetcher = FeedFetcher(self, update_feeds, config)
		fetched = fetcher.run(config["numthreads"])

		seen_some_items = set()
		def do_expiry(articles):
			"""Expire articles from a list. Return True if any
			articles were expired."""

			feedcounts = {}
			for key, article in list(articles.items()):
				url = article.feed
				feedcounts[url] = feedcounts.get(url, 0) + 1

			expiry_list = []
			feedcounts = {}
			for key, article in list(articles.items()):
				url = article.feed
				feedcounts[url] = feedcounts.get(url, 0) + 1
				expiry_list.append((article.added, article.sequence, key, article))
			expiry_list.sort()

			count = 0
			for date, seq, key, article in expiry_list:
				url = article.feed
				if url not in self.feeds:
					print("Expired article for nonexistent feed: ", url)
					count += 1
					del articles[key]
					continue
				if (url in seen_some_items
				    and url in self.feeds
				    and article.can_expire(now, config)
				    and feedcounts[url] > self.feeds[url].get_keepmin(config)):
					count += 1
					feedcounts[url] -= 1
					del articles[key]

			print("Expired", count, "articles, leaving", len(articles))
			return count > 0

		count = 0
		for url in update_feeds:
			count += 1
			print("Updating feed ", count, " of ", numfeeds, ": ", url)
			feed = self.feeds[url]
			articles = self.articles
			content = fetched[url]
			rc = feed.update(self, now, config, articles, content)
			url = feed.url
			if rc:
				seen_some_items.add(url)

		do_expiry(self.articles)
		self.modified()

	def get_page_template(self, config):
		template = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
   "http://www.w3.org/TR/html4/strict.dtd">
<html lang="en">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1">
    <meta name="robots" content="noindex,nofollow,noarchive">
    __refresh__
    <link rel="stylesheet" href="style.css" type="text/css">
    <title>rawdog</title>
    <link rel="icon" href="favicon.ico" type="image/x-icon" />
</head>
<body id="rawdog">
<h1 class="title">News</h1>
<div id="items">
__items__
</div>
"""
		if config["showfeeds"]:
			template += """<div id="feedstats">
__feeds__
</div>
"""
		template += """<div id="footer">
<div id="aboutrawdog">Generated by
<a href="https://github.com/dper/rawdog/">rawdog</a>
version __version__
by Adam Sampson.</div>
</div>
</body>
</html>
"""
		return template

	def get_item_template(self):
		return """<div class="item feed-__feed_hash__ feed-__feed_id__" id="item-__hash__">
<p class="itemheader">
<span class="itemtitle">__title__</span>
<span class="itemfrom">[__feed_title__]</span>
</p>
__if_description__<div class="itemdescription">
__description__
</div>__endif__
</div>

"""

	def get_feedlist_template(self):
		return """<table id="feeds">
<tr id="feedsheader">
<th>RSS</th><th>Site</th><th>Updated</th>

</tr>
__feeditems__
</table>
"""

	def get_feeditem_template(self):
		return """
<tr class="feedsrow">
<td>__feed_icon__</td>
<td>__feed_title__</td>
<td>__feed_last_update__</td>
</tr>
"""

	def write_article(self, f, article, config):
		"""Write an article to the given file."""
		feed = self.feeds[article.feed]
		entry_info = article.entry_info

		link = entry_info.get("link")
		if link == "":
			link = None

		guid = entry_info.get("id")
		if guid == "":
			guid = None

		itembits = self.get_feed_bits(config, feed)
		for name, value in list(feed.args.items()):
			if name.startswith("define_"):
				itembits[name[7:]] = sanitise_html(value, "", True, config)

		title = detail_to_html(entry_info.get("title_detail"), True, config)

		key = None
		for k in ["content", "summary_detail"]:
			if k in entry_info:
				key = k
				break
		if key is None:
			description = None
		else:
			force_preformatted = (feed.args.get("format", "default") == "text")
			description = detail_to_html(entry_info[key], False, config, force_preformatted)

		date = article.date
		if title is None:
			if link is None:
				title = "Article"
			else:
				title = "Link"

		itembits["title_no_link"] = title
		if link is not None:
			itembits["url"] = string_to_html(link, config)
		else:
			itembits["url"] = ""
		if guid is not None:
			itembits["guid"] = string_to_html(guid, config)
		else:
			itembits["guid"] = ""
		if link is None:
			itembits["title"] = title
		else:
			itembits["title"] = '<a href="' + string_to_html(link, config) + '">' + title + '</a>'

		itembits["hash"] = short_hash(article.hash)

		if description is not None:
			itembits["description"] = description
		else:
			itembits["description"] = ""

		author = author_to_html(entry_info, feed.url, config)
		if author is not None:
			itembits["author"] = author
		else:
			itembits["author"] = ""

		itembits["added"] = format_time(article.added, config)
		if date is not None:
			itembits["date"] = format_time(date, config)
		else:
			itembits["date"] = ""

		itemtemplate = self.get_item_template()
		f.write(fill_template(itemtemplate, itembits))

	def write_remove_dups(self, articles, config, now):
		"""Filter the list of articles to remove articles that are too
		old or are duplicates."""
		kept_articles = []
		seen_links = set()
		seen_guids = set()
		dup_count = 0
		for article in articles:
			feed = self.feeds[article.feed]
			age = now - article.added

			maxage = feed.args.get("maxage", config["maxage"])
			if maxage != 0 and age > maxage:
				continue

			entry_info = article.entry_info

			link = entry_info.get("link")
			if link == "":
				link = None

			guid = entry_info.get("id")
			if guid == "":
				guid = None

			if not feed.args.get("allowduplicates", False):
				is_dup = False
				if guid is not None:
					if guid in seen_guids:
						is_dup = True
					seen_guids.add(guid)
				if is_dup:
					dup_count += 1
					continue

			kept_articles.append(article)
		return (kept_articles, dup_count)

	def get_feed_bits(self, config, feed):
		"""Get the bits that are used to describe a feed."""

		bits = {}
		bits["feed_id"] = feed.get_id(config)
		bits["feed_hash"] = short_hash(feed.url)
		bits["feed_title"] = feed.get_html_link(config)
		bits["feed_title_no_link"] = detail_to_html(feed.feed_info.get("title_detail"), True, config)
		bits["feed_url"] = string_to_html(feed.url, config)
		bits["feed_icon"] = '<a class="xmlbutton" href="' + html.escape(feed.url) + '">XML</a>'
		bits["feed_last_update"] = format_time(feed.last_update, config)
		bits["feed_next_update"] = format_time(feed.last_update + feed.period, config)
		return bits

	def write_feeditem(self, f, feed, config):
		"""Write a feed list item."""
		bits = self.get_feed_bits(config, feed)
		f.write(fill_template(self.get_feeditem_template(), bits))

	def write_feedlist(self, f, config):
		"""Write the feed list."""
		bits = {}

		feeds = [(feed.get_html_name(config).lower(), feed)
		         for feed in list(self.feeds.values())]
		feeds.sort(key=lambda x: x[0])

		feeditems = StringIO()
		for key, feed in feeds:
			self.write_feeditem(feeditems, feed, config)
		bits["feeditems"] = feeditems.getvalue()
		feeditems.close()
		f.write(fill_template(self.get_feedlist_template(), bits))

	def get_main_template_bits(self, config):
		"""Get the bits that are used in the default main template,
		with the exception of items and num_items."""
		bits = {"version": VERSION}
		bits.update(config["defines"])

		refresh = min([config["expireage"]]
		              + [feed.period for feed in list(self.feeds.values())])
		bits["refresh"] = '<meta http-equiv="Refresh" content="' + str(refresh) + '">'

		f = StringIO()
		self.write_feedlist(f, config)
		bits["feeds"] = f.getvalue()
		f.close()
		bits["num_feeds"] = str(len(self.feeds))

		return bits

	def write_output_file(self, articles, article_dates, config):
		"""Write a regular rawdog HTML output file."""
		f = StringIO()
		dw = DayWriter(f, config)

		for article in articles:
			dw.time(article_dates[article])
			self.write_article(f, article, config)

		dw.close()

		bits = self.get_main_template_bits(config)
		bits["items"] = f.getvalue()
		f.close()
		bits["num_items"] = str(len(articles))
		s = fill_template(self.get_page_template(config), bits)
		outputfile = config["outputfile"]
		if outputfile == "-":
			write_ascii(sys.stdout, s, config)
		else:
			print("Writing output file:", outputfile)
			f = open(outputfile + ".new", "w")
			write_ascii(f, s, config)
			f.close()
			os.rename(outputfile + ".new", outputfile)

	def write(self, config):
		"""Write articles to the output file."""
		print("Writing...")
		now = time.time()

		def list_articles(articles):
			return [(-a.get_sort_date(config), a.feed, a.sequence, a.hash) for a in list(articles.values())]
		article_list = list_articles(self.articles)
		numarticles = len(article_list)
		article_list.sort()

		if config["maxarticles"] != 0:
			article_list = article_list[:config["maxarticles"]]

		found = self.articles
		articles = []
		article_dates = {}
		for (date, feed, seq, hash) in article_list:
			a = found.get(hash)
			if a is not None:
				articles.append(a)
				article_dates[a] = -date

		(articles, dup_count) = self.write_remove_dups(articles, config, now)
		print("Selected", len(articles), "of", numarticles, "articles. Ignored", dup_count, "duplicates.")
		self.write_output_file(articles, article_dates, config)

def usage():
	"""Display usage information."""

	print("""rawdog, version """ + VERSION + """
Usage: rawdog [OPTION]...

Actions (performed in order given):
-l, --list                   List feeds known at time of last update
-u, --update                 Fetch data from feeds and store it
-w, --write                  Write out HTML output""")

def main(argv):
	"""The command-line interface to the aggregator."""

	locale.setlocale(locale.LC_ALL, "")

	# This is quite expensive and not threadsafe, so do it on
	# startup and cache the result.
	global system_encoding
	system_encoding = locale.getpreferredencoding()

	try:
		SHORTOPTS = "luw"
		LONGOPTS = [
			"list",
			"update",
			"write",
			]
		(optlist, args) = getopt.getopt(argv, SHORTOPTS, LONGOPTS)
	except getopt.GetoptError as s:
		print(s)
		usage()
		return 1

	if len(args) != 0:
		usage()
		return 1

	if "HOME" in os.environ:
		statedir = os.environ["HOME"] + "/.rawdog"
	else:
		statedir = None
	locking = True
	no_lock_wait = False
	for o, a in optlist:
		if o == "--help":
			usage()
			return 0
	if statedir is None:
		print("$HOME not set and state dir not explicitly specified; please use -d/--dir")
		return 1

	try:
		os.chdir(statedir)
	except OSError:
		print("No " + statedir + " directory")
		return 1

	sys.path.append(".")

	config = Config(locking)
	def load_config(fn):
		try:
			config.load(fn)
		except ConfigError as err:
			print("In", fn, ":")
			print(err)
			return 1
		return 0
	rc = load_config("config")
	if rc != 0:
		return rc

	global persister
	persister = Persister(config)

	rawdog_p = persister.get(Rawdog, "state")
	rawdog = rawdog_p.open(no_block=no_lock_wait)
	if rawdog is None:
		return 0
	if not rawdog.check_state_version():
		print("The state file " + statedir + "/state was created by an older")
		print("version of rawdog, and cannot be read by this version.")
		print("Removing the state file will fix it.")
		return 1

	rawdog.sync_from_config(config)

	for o, a in optlist:
		if o in ("-l", "--list"):
			rawdog.list(config)
		elif o in ("-u", "--update"):
			rawdog.update(config)
		elif o in ("-w", "--write"):
			rawdog.write(config)

	rawdog_p.close()
	return 0
