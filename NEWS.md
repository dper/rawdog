# NEWS

## rawdog 3.3

* Removed optional TidyLib use. TidyLib, when enabled, was leading to unexpected formatting around apostrophes and Japanese characters.

## rawdog 3.2

* Removed plugins.
* Removed around half of the old options. If you have an old config file, you might get startup errors. If you really need behavior that is no longer supported, you'll have to edit the code manually. However, many of those options added flexiblity that's not useful in a simple single user setup, so there shouldn't be major concerns.

## rawdog 3.1

* Switched some text files to markdown.
* Cleaned up `style.css` and the page layout. Removed the "next update" column in the stats table at the bottom. This information is already in the config file.
* Added `favicon.ico`.
* Removed some legacy code. There is no longer a logger, and output goes to `stdout`. References to version 1 are all gone now.

## rawdog 3.0

* Converted to Python 3 by Douglas Perkins. In the process, many things were removed. Some options are gone from the config. Plugins are not recognized. You can no longer build this program, but it works in place, as it always did. Templates are no longer supported.

## rawdog 2.24

feedscanner now sets User-Agent explicitly, so `rawdog --add/--find` use rawdog's User-Agent rather than the default one. As some blogging services block requests with the default Python User-Agent, this makes scanning a bit more effective.

Use the Python 3-style print function (supported since Python 2.6).

## rawdog 2.23

rawdog now requires Python 2.7. Python 2.6 doesn't build with current toolchains, and hasn't been included in Debian for several releases, so I can't test against it any more.

When automatically updating the config file in response to an HTTP redirect fails, produce a more sensible error message (including the URL of the feed in question).

Add the `--find option`, which shows what feedscanner returns for a given URL (as `--dump` does for feedparser).

The location of `BASE_OPTIONS` has changed in pytidylib 0.3.2; rather than trying to change it, override the corresponding options explicitly.  The meaning of tidylib's wrap option has also changed, so set a sensible default value.

Support the current development version of feedparser (which will presumably be the 5.3 release eventually), which has been restructured into multiple modules, and raises network exceptions (e.g. timeouts) directly from `feedparser.parse` rather than putting them in `bozo_exception`.

rawdog's exception-handling code has been cleaned up as a result of the above, and should work consistently for old and new versions of feedparser. In the feedparser result dict, `bozo_exception` is now converted to `rawdog_exception` for network errors, and `rawdog_timeout` is set if a timeout exception occurred. For compatibility with existing plugins, an empty `feed` is also provided on a timeout.

Update COPYING and the GPL v2 license notices to the FSF's current recommended text.

## rawdog 2.22

When handling an HTTP 301 redirect response, check whether the new location is an absolute URI (as the HTTP/1.1 specification says it should be). Some broken servers return a relative path, or junk, and in those cases rawdog shouldn't update the URL in the config file.

Fix some more style problems reported by pylint.

Specify the input and output character encodings for pytidylib explicitly. tidylib 5 has changed the defaults from ASCII to UTF-8; rawdog relies on it being ASCII in order to generate ASCII output (reported by Lucas Nussbaum).

## rawdog 2.21

Don't crash when asked to show a non-existant template (`-s foo`) -- and fix `test-rawdog` so that it detects when a test is expected to fail with an error message, but actually crashes.

Use `grep -a` when searching for locales in `test-rawdog`, since some locales have non-ASCII names.

Fix some style problems reported by pylint.

Use `cStringIO` rather than `StringIO` in all modules (rather than some using one and some using the other).

Don't crash when feedparser returns a date that Python can't format.  Since feedparser's date parser is pretty liberal, it can occasionally interpret an invalid date incorrectly (e.g. treating a time zone as a year number).

When an error occurs while parsing the config file, exit with a non-zero return code, rather than continuing with an incomplete config. This has always been the intended behaviour, but rawdog 2.13 accidentally removed the check.

## rawdog 2.20

Add a test for the `maxage` option (suggested by joelmo).

Add a rule to `style.css` to scale down large images.

When looking for SSL timeout exceptions, match any form of `timeout`, `time out` or `timed out` in the message. This makes rawdog detect SSL connection timeouts correctly with Debian's Python 2.7.8 package (reported by David Suárez).

## rawdog 2.19

Make `test-rawdog` not depend on having a host it can test connection timeouts against, and add a `-T` option if you do have one.

When renaming a feed's state file in splitstate mode, don't fail if the state file doesn't exist -- which can happen if we get a 301 response for a feed the first time we fetch it. Also rename the lock file along with the state file.

Add some more comprehensive tests for the `changeconfig` option; in particular, test it more thoroughly with splitstate both on and off.

Don't crash if feedparser raises an exception during an update (i.e.  assume that any part of feedparser's response might be missing, until we've checked that there wasn't an exception).

## rawdog 2.18

Be consistent about catching `AttributeError` when looking for attributes that were added to Rawdog during the 2.x series (spotted by Jakub Wilk).

Add some advice in PLUGINS about escaping template parameters. Willem reported that the enclosure plugin didn't do this, and having had a look at the others it seems to be a common problem.

Make feedscanner handle `Content-Encoding: gzip` in responses, as tumblr.com's webservers will use this even if you explicitly refuse it in the request.

## rawdog 2.17

Add a one-paragraph description of rawdog to the README file, for use by packagers.

Fix some misquoted dashes in the man page (spotted by lintian).

Set `LC_ALL=C` and `TZ=UTC` when running tests, in order to get predictable results regardless of locale or timezone (reported by Etienne Millon).

Give sensible error messages on startup (rather than crashing) if the config file or a template file is missing, or contains characters that aren't in the system encoding.

Give `test-rawdog` some command-line options; you can now use it to test an installed version of rawdog, or rawdog running under a non-default Python version.

Add some more tests to the test suite, having done a coverage analysis to work out which features weren't yet being tested: date formatting in varying locales and timezones; RSS 1.0 support; `--dump`, `-c`, `-f`, `-l`, `-N`, `-v` and `-W`; include; plugin loading; feed format and id options; author formatting; template conditionals: broken 301 redirects; useids; content vs.  summary; daysections/timesections; removing articles from a feed; keeping comments; numthreads; outputfile; various error messages.

Use author URIs retrieved from feeds when formatting author names (rather than ignoring them; this was the result of a feedparser change).

Make subclasses of Persistable call Persistable's constructor.  (Identified by coverage analysis.)

Don't crash when trying to show a template that doesn't exist.

When removing a feed in splitstate mode, remove its lock file too.

## rawdog 2.16

Remove the bundled copy of feedparser, and document that it's now a dependency.

Update the package metadata in `setup.py`.

## rawdog 2.15

rawdog now requires Python 2.6 (rather than Python 2.2). This is the version in Debian and Red Hat's previous stable releases, so it should be safe to assume on current systems.

Make `setup.py` complain if you have an inappropriate Python version.

Remove obsolete code that supported pre-2.6 versions of Python (`timeoutsocket.py`, conditional imports, 0/1 for bools, dicts for sets, locking without with, various standard library features).

Tidy up the code formatting in a few places to make it closer to PEP 8.

Make the `rawdog(1)` man page describe all of rawdog's options, and make some other minor improvements to the documentation and help.

Remove the `--upgrade option`; I think it's highly unlikely that anybody still has any rawdog 1 state files around.

Make the code that manages the pool of feed-fetching threads only start as many threads as necessary (including none if there's only one feed to fetch), and generally tidy it up.

Add `test-rawdog`, a simple test suite for rawdog with a built-in webserver. You should be able to run this from the rawdog source directory to check that much of rawdog is working correctly.  (If you have the rawdog plugins repo in a subdirectory called `rawdog-plugins`, it'll run tests on some of the plugins too.)

Add a `-V` option, which is like `-v` but appends the verbose output to a file. This is mostly useful for testing.

Significantly rework the `Persister` class: there's now a `Persisted` class that can act as a context manager for `with` statements, which simplifies the code quite a bit, and it correctly handles persisted objects being opened multiple times and renamed. `persister.py` is now under the same license as the rest of rawdog (GPLv2+).

Fix a bug: if you're using splitstate mode, and a feed returns a 301 permanent redirect, rawdog needs to rename the state file and adjust the articles in it so they're attached to the feed's new URL. In previous versions this didn't work correctly for two reasons: it tried to load the existing articles from the new filename, and the resulting file got clobbered because it was already being used by `--update`.

Rework the locking logic in persister so that it uses a separate lock file. This fixes a (mostly) harmless bug: previously if rawdog A was waiting for rawdog B to finish, then rawdog A wouldn't see the changes rawdog B had written to the state file. More importantly, it means rawdog won't leave an empty ("corrupt") state file if it crashes during the first update or write.

Split state files are now explicitly marked as modified if any articles were expired from them. (This won't actually change rawdog's behaviour, since articles were only expired if some articles had been seen during the update, and that would also have marked the state as modified.)

When splitstate is enabled, make the feeds directory if it doesn't already exist. This avoids a confusing error message if you didn't make it by hand.

rawdog now complains if feedparser can't detect the type of a feed or retrieve any items from it. This usually means that the URL isn't actually a feed -- for example, if it's redirecting to an error page.

rawdog can now report more than one error for a feed at once -- e.g.  a permanent redirection to something that isn't a feed.

Show URLError exceptions returned by feedparser -- this means rawdog gives a sensible error message for a file: or ftp: URL that gives an error, rather than claiming it's a timeout. Plain filenames are now turned into file: URLs so you get consistent errors for both, and timeouts are detected by looking for a timeout exception.

Use a custom `urllib2` handler to capture all the HTTP responses that feedparser sees when handling redirects. This means rawdog can now see both the initial and final status code (rather than the combined one feedparser returns) -- so it can correctly handle redirects to errors, and redirects to redirects.

Make `hideduplicates id link` work correctly in the odd corner case where an article has both id and link duplicated, but to different other articles.

Upgrade feedparser to version 5.1.3. As a result of the other changes below, rawdog's copy of feedparser is now completely unmodified -- so it should be safe to remove it and use your system version if you prefer (provided it's new enough).

Add a `--dump` option to pretty-print feedparser's output for a URL.  The feedparser module used to do this if invoked as a script, but more recent versions of feedparser don't support this.

Use a custom `urllib2` handler to do HTTP basic authentication, instead of a feedparser patch. This also fixes proxy authentication, which I accidentally broke by removing a helper class several releases ago.

Use a custom `urllib2` handler to disable RFC 3229, instead of a feedparser patch. The behaviour is slightly different in that it now sends `A-IM: identity` rather than no header at all; this should have the same effect, though.

Remove the feedparser patch that provided `_raw` versions of content (before sanitisation) for use in the article hash, and use the normal version instead. Since we disable sanitisation at fetch time anyway, the only difference with current feedparser is that the `_raw` versions didn't have CP1252 encoding fixes applied -- so in the process of upgrading to this version, you'll see some duplicate articles on feeds with CP1252 encoding problems. Tests suggest this doesn't affect many feeds (3 out of the 1000-odd in my test setup).

Set feedparser behaviour using `SANITIZE_HTML` etc., rather than by directly changing the lists of elements it's looking for.

Replace feedfinder, which has unfixable unclear licensing, with the module that Decklin Foster wrote for his Debian package of rawdog (specifically `rawdog_2.13.dfsg.1-1`).  I've renamed it to `feedscanner`, on the grounds that it may be useful to other projects as well in the future.

Put feedscanner's license notice into `__license__`, for consistency with feedparser.

Make feedscanner understand HTML-style `<link ...>` as well as XHTML-style `<link ... />`.

Fix Debian bug 657206: make feedscanner understand relative links (reported by Peter J. Weisberg).

Fix Debian bug 650776: make feedscanner not crash if it can't parse the URL it was given as HTML (reported by Jonathan Polley).

Make rawdog use feedscanner's preferred order of feeds in addition to its own.

Make feedscanner only return URLs that feedparser can parse successfully as feeds.

Make feedscanner look for `<a>` links pointing to URLs with words in them that suggest they're probably feeds.

Make feedscanner check whether the URL it was given is already a feed before scanning it for links.

Make feedscanner decode the HTML it reads (silently ignoring errors) before trying to parse it.

Move rawdog's feed quality heuristic into feedscanner.

Simplify the options for dealing with templates: there is now a `-s`/`--show` command-line option that takes a template name as an argument (i.e. you do `rawdog -s item` rather than `rawdog -T`), and the `template` config file option is now called `pagetemplate`. This simplifies the code, and makes it possible to add more templates without adding more command-line options. (For backwards compatibility, all the old command-line and config-file options are still accepted, and `rawdog.get_template(config)` will still return the page template.)

Add templates for the feed list and each item in the feed list (based on patch from Arnout Engelen).

Don't append an extra newline when showing a template.

## rawdog 2.14

When adding a new feed from a page that provides several feeds, make a more informed choice rather than just taking the first one: many blogs provide both content and comments feeds, and we usually want the first one.

Add a note to PLUGINS about making sure plugin storage gets saved.

Use `updated_parsed` instead of the obsolete `modified_parsed` when extracting the feed-provided date for an item, and fall back to `published_parsed` and then `created_parsed` if it doesn't exist (reported by Cristian Rigamonti, Martintxo and chrysn). feedparser currently does fallback automatically, but it's scheduled to be removed at some point, so it's better for rawdog to do it.

## rawdog 2.13

Forcibly disable BeautifulSoup support in feedparser, since it returns unpickleable pseudo-string objects, and it crashes when trying to parse twenty or so of my feeds (reported by Joseph Reagle).

Make the code that cleans up feedparser's return value more thorough -- in particular, turn subclasses of "unicode" into real unicode objects.

Decode the config file from the system encoding, and escape `define_`d strings when they're written to the output file (reported by Cristian Rigamonti).

Add the `showtracebacks` option, which causes exceptions that occur while a feed is being fetched to be reported with a traceback in the resulting error message.

Use PyTidyLib in preference to `mx.Tidy` when available (suggested by Joseph Reagle). If neither is available, `tidyhtml true` just does nothing, so it's now turned on in the provided config file. The `mxtidy_args` hook is now called `tidy_args`.

Allow template variables to start with an underscore (patch from Oberon Faelord).

Work around broken DOCTYPEs that confuse sgmllib.

If `-v` is specified, force verbose on again after reading a secondary config file (reported by Jonathan Phillips).

Resynchronise the feed list after loading a secondary config file; previously feeds in secondary config files were ignored (reported by Jonathan Philips).

## rawdog 2.12

Make rawdog work with Python 2.6 (reported by Roy Lanek).

If feedfinder (which now needs Python 2.4 or later) can't be imported, just disable it.

Several changes as a result of profiling that significantly speed up writing output files:

* Make `encode_references()` use regexp replacement.
* Cache the result of `locale.getpreferredencoding()`.
* Use tuple lists rather than custom comparisons when sorting.

Update feedparser to revision 291, which fixes the handling of `<media:title>` elements (reported by Darren Griffith).

Only update the stored `Etag` and `Last-Modified` when a feed changes.

Add the `splitstate` option, which makes rawdog use a separate state file for each feed rather than one large one. This significantly reduces rawdog's memory usage at the cost of some more disk IO during `--write`.  The old behaviour is still the default, but I would recommend turning splitstate on if you read a lot of feeds, if you use a long expiry time, or if you're on a machine with limited memory.

As a result of the splitstate work, the `output_filter` and `output_sort` hooks have been removed (because there's no longer a complete list of articles to work with). Instead, there's now an `output_sort_articles` hook that works with a list of article summaries.

Add the `useids` option, which makes rawdog respect article GUIDs when updating feeds; if an article's GUID matches one we already know about, we just update the existing article's contents rather than treating it as a new article (like most aggregators do). This is turned on in the default configuration, since the behaviour it produces is generally more useful these days -- many feeds include random advertisements, or other dynamic content, and so the old approach resulted in lots of duplicated articles.

## rawdog 2.11

Avoid a crash when a feed's URL is changed and expiry is done on the same run.

Encode dates correctly in non-ASCII locales (reported by Damjan Georgievski).

Strengthen the warning in PLUGINS about the effects of overriding `output_write_files` (suggested by Virgil Bucoci).

Add the state directory to `sys.path`, so you can put modules that plugins need in your `~/.rawdog` (suggested by Stuart Langridge).

When adding a feed, check that it isn't already present in the config file (suggested by Stuart Langridge).

Add `--no-lock-wait` option to make rawdog exit silently if it can't lock the state file (i.e. if there's already a rawdog running).

Update to the latest feedparser, which fixes an encoding bug with Python 2.5, among various other stuff (reported by Paul Tomblin, Tim Bishop and Joseph Reagle).

Handle the `author_detail` fields being None.

## rawdog 2.10

Work around a feedparser bug (returning a detail without a type field for posts with embedded SVG).

Pull in most of the changes from feedparser 4.1.

Fix a bug that stopped rawdog from working properly when no locale information was present in the environment, or on versions of Python without `locale.getpreferredencoding()` (reported by Michael Watkins).

Add `--remove` option to remove a feed from the config file (suggested by Wolfram Sieber).

Produce a more useful error message when `$HOME` isn't set (reported by Wolfram Sieber).

Fix a bug in the expiry code: if you were using keepmin, it could expire articles that were no longer current but should be kept.

Clean up the example config file a bit.

## rawdog 2.9

Fix a documentation bug about time formats (reported by Tim Bishop).

Fix a text-handling problem related to the locale changes (patch from Samuel Hym).

Fix use of the `A-IM: feed` header in HTTP requests. A previous upstream change to feedparser had modified it so that it always sent this header, which results in a subtle rawdog bug: if a feed returns a partial result (226) and then has no changes for a long time, rawdog can expire articles which should still be "current" in the feed. This version adds a `keepmin` option which make a minimum number of articles be kept for each feed; this should avoid expiring articles that are still current.  If you want the old behaviour, you can set `keepmin` to `0`, in which case rawdog won't send the `A-IM: feed` header in its requests. rawdog also won't send that header if `currentonly` is set to true, since in that case the current set of articles is all rawdog cares about. (See <http://www.intertwingly.net/blog/2006/04/29/Now-you-see-it> for Sam Ruby's discussion of the same problem in Planet.)

If the author's name is given as the empty string, fall back to the email address, URL or `author`.

Change the labels in the feed information table to `Last fetched` and `Next fetched after`, to match what rawdog actually does with the times it stores (reported by D. Stussy).

## rawdog 2.8

Fix authentication support -- feedparser now supports Basic and Digest authentication internally, but it needed tweaking to make it useful for rawdog (reported by Tim Bishop).

## rawdog 2.7

Make feedfinder smarter about trying to find the preferred type of feed (patch from Decklin Foster).

Add a plugin hook to let you modify `mx.Tidy` options (suggested by Jon Lasser).

Work correctly if the threading module isn't available (patch from Jack Diederich).

Update to feedparser 4.0.2, which includes some of our patches and fixes an unclear license notice (reported by Jason Diamond, Joe Wreschnig and Decklin Foster).

Fix a feedparser bug that caused things preceding shorttags to be duplicated when sanitising HTML.

Set the locale correctly when rawdog starts up (patch from Samuel Hym).

## rawdog 2.6

Allow maxage to be set per feed (patch from Craig Allen).

Support feeddefaults with no options on the same line, as used in the
sample config file (reported by asher).

## rawdog 2.5

Ensure that all the strings in `entry_info` are in Unicode form, to make it easier for plugins to deal with them.

Fix a feedparser bug that was breaking feeds which includes itunes elements (reported by James Cameron).

Make feedparser handle content types and modes in `atom:content` correctly (reported by David Dorward).

Make feedparser handle the new elements in Atom 1.0 (patch from Decklin Foster).

Remove some unnecessary imports found by pyflakes.

Add `output_sorted_filter` and `output_write_files` hooks, deprecating the `output_write hook` (which wasn't very useful originally, and isn't used by any of the plugins I've been sent). Restructure the `write` code so that it should be far easier to write custom output plugins: there are several new methods on Rawdog for doing different bits of the write process.

When selecting articles to display, don't assume they're sorted in date order (a plugin might have done something different).

Don't write an extra newline at the end of the output file (i.e. use `f.write` rather than `print >>f`), and be more careful about encoding when writing output to stdout.

Provide arbitrary persistent storage for plugins via a `get_plugin_storage` method on Rawdog (suggested by BAM).

Add `-N` option to avoid locking the state file, which may be useful if you're on an OS or filesystem that doesn't support locks (suggested by Andy Dustman).

If `RAWDOG_PROFILE` is set as an environment variable, rawdog will run under the Python profiler.

Make some minor performance improvements.

Change the `Error parsing feed` message to `Error fetching or parsing feed`, since it really just indicates an error somewhere within feedparser (reported by Fred Barnes).

Add support for using multiple threads when fetching feeds, which makes updates go much faster if you've got lots of feeds. (The state-updating part of the update is still done sequentially, since parallelising it would mean adding lots of locking and making the code very messy.) To use this, set `numthreads` to be greater than `0` in your config file.  Since it changes the semantics of one of the plugin hooks, it's off by default.

Update the GPL and LGPL headers to include the FSF's new address (reported by Decklin Foster).

## rawdog 2.4

Provide guid in item templates (suggested by Rick van Rein).

Update article-added dates correctly when `currentonly true` is used (reported by Rick van Rein).

Clarify description of `-c` in README and man page (reported by Rick van Rein).

If you return false from an `output_items_heading` function, then disable DayWriter (suggested by Ian Glover).

Fix description of `article_seen` in PLUGINS (reported by Steve Atwell).

Escape odd characters in links and guids, and add a sanity check that'll trip if non-ASCII somehow makes it to the output (reported by TheCrypto).

## rawdog 2.3

Make the `id=` parameter work correctly (patch from Jon Nelson).

## rawdog 2.2

Add `feeddefaults` statement to specify default feed options.

Update feeds list from the config file whenever rawdog runs, rather than just when doing an update (reported by Decklin Foster).

Reload the config files after `-a`, so that `rawdog -a URL -u` has the expected behaviour (reported by Decklin Foster).

Add `define` statement and `define_X` feed option to allow the user to define extra strings for the template; you can use this, for example, to select classes for groups of feeds, generate different HTML for different sorts of feeds, or set the title in different pages generated from the same template (suggested by Decklin Foster).

Fix a logic error in the `_raw` changes to feedparser: if a feed didn't specify its encoding but contained non-ASCII characters, rawdog will now try to parse it as UTF-8 (which it should be) and, failing that, as ISO-8859-1 (in case it just contains non-UTF-8 junk).

Don't print the `state file may be corrupt` error if the user hits Ctrl-C while rawdog's loading it.

Add support for extending rawdog with plugin modules; see the PLUGINS file for more information.

Make `verbose true` work in the config file.

Provide `__author__` in items, for use in feeds that support that (patch from Decklin Foster).

Fix conditional template expansion (patch from Decklin Foster).

Add `blocklevelhtml` statement to disable the `<p>` workaround for non-block-level HTML; this may be useful if you have a plugin that is doing different HTML sanitisation, or if your template already forces a block-level element around article descriptions.

Fix `-l` for feeds with non-ASCII characters in their titles.

Provide human-readable `__feed_id__` in items (patch from David Durschlag), and add `feed-whatevername` class to the default item template; this should make it somewhat easier to add per-feed styles.

Handle feeds that are local files correctly, and handle file: URLs in feedparser (reported by Chris Niekel).

Allow feed arguments to be given on indented lines after the `feed` or `feeddefaults` lines; this makes it possible to have spaces in feed arguments.

Add a meta element to the default template to stop search engines indexing rawdog pages (patch from Rick van Rein).

Add new feeds at the end of the config file rather than before the first feed line (patch from Decklin Foster).

## rawdog 2.1

Fix a character encoding problem with `format=text` feeds.

Add `proxyuser` and `proxypassword` options for feeds, so that you can use per-feed proxies requiring HTTP Basic authentication (patch from Jon Nelson).

Add a manual page (written by Decklin Foster).

Remove extraneous `##!` line from `feedparser.py` (reported by Decklin Foster).

Update an article's modified date when a new version of it is seen (reported by Decklin Foster).

Support nested ifs in templates (patch from David Durschlag), and add `__else__`.

Make the README file list all the options that rawdog now supports (reported by David Durschlag).

Make `--verbose` work even if it's specified after an action (reported by Dan Noe and David Durschlag).

## rawdog 2.0

Update to feedparser 3.3. This meant reworking some of rawdog's internals; state files from old versions will no longer work with rawdog 2.0 (and external programs that manipulate rawdog state files will also be broken). The new feedparser provides a much nicer API, and is significantly more robust; several feeds that previously caused feedparser internal errors or Python segfaults now work fine.

Add an `--upgrade` option to import state from rawdog 1.x state files into rawdog 2.x. To upgrade from 1.x to 2.x, you'll need to perform the following steps after installing the new rawdog:

    cp -R ~/.rawdog ~/.rawdog-old
    rm ~/.rawdog/state
    rawdog -u
    rawdog --upgrade ~/.rawdog-old ~/.rawdog (to copy the state)
    rawdog -w
    rm -r ~/.rawdog-old (once you're happy with the new version)

Keep track of a version number in the state file, and complain if you use a state file from an incompatible version.

Remove support for the old option syntax (`rawdog update write`).  Remove workarounds for early 1.x state file versions.

Save the state file in the binary pickle format, and use cPickle instead of pickle so it can be read and written more rapidly.

Add `hideduplicates` and `allowduplicates` options to attempt to hide duplicate articles (based on patch from Grant Edwards).

Fix a bug when sorting feeds with no titles (found by Joseph Reagle).

Write the updated state file more safely, to reduce the chance that it'll be damaged or truncated if something goes wrong while it's being written (requested by Tim Bishop).

Include feedfinder, and add a `-a|--add` option to add a feed to the config file.

Correctly handle dates with timezones specified in non-UTC locales (reported by Paul Tomblin and Jon Lasser).

When a feed's URL changes, as indicated by a permanent HTTP redirect, automatically update the config file and state.

## rawdog 1.13

Handle `OverflowError` with parsed dates (patch from Matthew Scott).

## rawdog 1.12

Add `sortbyfeeddate` option for planet pages (requested by David Dorward).

Add `currentonly` option (patch from Chris Cutler).

Handle nested CDATA blocks in feed XML and HTML correctly in feedparser.

## rawdog 1.11

Add `__num_items__` and `__num_feeds__` to the page template, and `__url__` to the item template (patch from Chris Cutler).

Add `daysections` and `timesections` options to control whether to split items up by day and time (based on patch from Chris Cutler).

Add `tidyhtml` option to use `mx.Tidy` to clean feed-provided HTML.

Remove the `<p>` wrapping `__description__` from the default item template, and make rawdog add `<p>...</p>` around the description only if it doesn't start with a block-level element (which isn't perfect, but covers the majority of problem cases). If you have a custom item template and want rawdog to generate a better approximation to valid HTML, you should change `<p>__description__</p>` to `__description__`.

HTML metacharacters in links are now encoded correctly in generated HTML (`foo?a=b&c=d` as `foo?a=b&amp;c=d`).

Content type selection is now performed for all elements returned from the feed, since some Blogger v5 feeds cause feedparser to return multiple versions of the title and link (reported by Eric Cronin).

## rawdog 1.10

Add `ignoretimeouts` option to silently ignore timeout errors.

Fix SSL and socket timeouts on Python 2.3 (reported by Tim Bishop).

Fix entity encoding problem with HTML sanitisation that was causing rawdog to throw an exception upon writing with feeds containing non-US-ASCII characters in attribute values (reported by David Dorward, Dmitry Mark and Steve Pomeroy).

Include `MANIFEST.in` in the distribution (reported by Chris Cutler).

## rawdog 1.9

Add `clear: both;` to item, time and date styles, so that items with floated images in don't extend into the items below them.

Changed how rawdog selects the feeds to update; `--verbose` now shows only the feeds being updated.

rawdog now uses feedparser 2.7.6, which adds date parsing and limited sanitisation of feed-provided HTML; I've removed rawdog's own date-parsing (including `iso8601.py`) and relative-link-fixing code in favour of the more-capable feedparser equivalents.

The persister module in rawdoglib is now licensed under the LGPL (requested by Giles Radford).

Made the error messages that listed the state dir reflect the `-b` setting (patch from Antonin Kral).

Treat empty titles, links or descriptions as if they weren't supplied at all, to cope with broken feeds that specify `<title></title>` (patch from Michael Leuchtenburg).

Make the expiry age configurable; previously it was hard-wired to 24 hours. Setting this to a larger value is useful if you want to have a page covering more than a day's feeds.

Time specifications in the config file can now include a unit; if no unit is specified it'll default to minutes or seconds as appropriate to maintain compatibility with old config files. Boolean values can now be specified as `true` or `false` (or `1` or `0` for backwards compatibility). rawdog now gives useful errors rather than Python exceptions for bad values. (Based on suggestions by Tero Karvinen.)

Added datetimeformat option so that you can display feed and article times differently from the day and time headings, and added some examples including ISO 8601 format to the config file (patch from Tero Karvinen).

Forcing a feed to be updated with `-f` now clears its `ETag` and `Last-Modified`, so it should always be refetched from the server.

Short-form XML tags in RSS (`<description/>`) are now handled correctly.

Numeric entities in RSS encoded content are now handled correctly.

## rawdog 1.8

Add `format=text` feed option to handle broken feeds that make their descriptions unescaped text.

Add `__hash__` and unlinked titles to item templates, so that you can use multiple config files to build a summary list of item titles (for use in the Mozilla sidebar, for instance). (Requested by David Dorward.)

Add the `--verbose` argument (and the `verbose` option to match); this makes rawdog show what it's doing while it's running.

Add an `include` statement in config files that can be used to include another config file.

Add feed options to select proxies (contributed by Neil Padgen). This is straightforward for Python 2.3, but 2.2's `urllib2` has a bug which prevents ProxyHandlers from working; I've added a workaround for now.

## rawdog 1.7

Fix code in iso8601.py that caused a warning with Python 2.3.

## rawdog 1.6

Config file lines are now split on arbitary strings of whitespace, not just single spaces (reported by Joseph Reagle).

Include a link to the rawdog home page in the default template.

Fix the `--dir` argument: `-d` worked fine, but the getopt call was missing an `=` (reported by Gregory Margo).

Relative links (`href` and `src` attributes) in feed-provided HTML are now made absolute in the output. (The feed validator will complain about feeds with relative links in, but there are quite a few out there.)

Item templates are now supported, making it easier to customise item appearance (requested by a number of users, including Giles Radford and David Dorward). In particular, note that `__feed_hash__` can be used to apply a CSS style to a particular feed.

Simple conditions are supported in templates: `__if_x__ .. __endif__` only expands to its contents if `x` is not empty. These conditions cannot be nested.

PyXML's iso8601 module is now included so that rawdog can parse dates in feeds.

## rawdog 1.5

Remove some debugging code that broke timeouts.

## rawdog 1.4

Fix option-compatibility code (reported by BAM).

Add HTTP basic authentication support (which means modifying feedparser again).

Print a more useful error if the statefile can't be read.

## rawdog 1.3

Reverted the "retry immediately" behaviour from 1.2, since it causes denied or broken feeds to get checked every time rawdog is run.

Updated feedparser to 2.5.3, which now returns the XML encoding used.  rawdog uses this information to convert all incoming items into Unicode, so multiple encodings are now handled correctly. Non-ASCII characters are encoded using HTML numeric character references (since this allows me to leave the HTML charset as ISO-8859-1; it's non-trivial to get Apache to serve arbitrary HTML files with the right Content-Type, and using `<meta http-equiv="Content-Type"...>` won't override HTTP headers).

Use standard option syntax (i.e. `--update --write` instead of `update write`).  The old syntax will be supported until 2.0.

Error output from reading the config file and from `--update` now goes to `stderr` instead of stdout.

Made the socket timeout configurable (which also means the included copy of feedparser isn't modified any more).

Added `--config` option to read an additional config file; this lets you have multiple output files with different options.

Allow `outputfile -` to write the output to stdout; useful if you want to have cron mail the output to you rather than putting it on a web page.

Added `--show-template` option to show the template currently in use (so you can customise it yourself), and `template` config option to allow the user to specify their own template.

Added `--dir` option for people who want two lots of rawdog state (for two sets of feeds, for instance).

Added `maxage` config option for people who want "only items added in the last hour", and made it possible to disable maxarticles by setting it to 0.

## rawdog 1.2

Updated feedparser to 2.5.2, which fixes a bug that was making rawdog handle content incorrectly in Echo feeds, handles more content encoding methods, and returns HTTP status codes. (I've applied a small patch to correct handling of some Echo feeds.)

Added useful messages for different HTTP status codes and HTTP timeouts. Since rawdog reads a config file, it can't automatically update redirected feeds, but it will now tell you about them.  Note that for "fatal" errors (anything except a 2xx response or a redirect), rawdog will now retry the feed next time it's run.

Prefer `content` over `content_encoded`, and fall back correctly if no useful `content` is found.

## rawdog 1.1

rawdog now preserves the ordering of articles in the RSS when a group of articles are added at the same time.

Updated rawdog URL in `setup.py`, since it now has a web page.

Updated rssparser to feedparser 2.4, and added very preliminary support for the `content` element it can return (for Echo feeds).

## rawdog 1.0

Initial stable release.
