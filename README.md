# rawdog: RSS Aggregator Without Delusions Of Grandeur

Adam Sampson <ats@offog.org>
Douglas Perkins <https://github.com/dper/rawdog>

rawdog is a feed aggregator, capable of producing a personal "river of news" or a public "planet" page. It supports all common feed formats, including RSS and Atom. It collects articles from a number of feeds and generates a static HTML page listing the newest articles in order.

This version uses Python 3. In the switch from Python 2 to Python 3, many features were removed, including plugins and many options.

## Dependencies

* Python 3.10 or later
* feedparser 6.0.8 or later

## Installation

This program is designed to run without installation.  For example, download it to your `~/src` directory and run it from there using the `rawdog` command. Typically, `rawdog -uw`.

rawdog needs a config file to function. Make the directory `.rawdog` in your `$HOME` directory, copy the provided `config` file into that directory, and edit it. Copy `style.css` file into the same directory as your html output.  Adjust the style as you prefer.

When you invoke rawdog from the command line, you give it a series of actions to perform. For instance, `rawdog --update --write` tells it to download articles from feeds and then write to the HTML file.

A cronjob entry such as the following is recommended:

    0,10,20,30,40,50 * * * *        /path/to/rawdog -uw

If you want rawdog to fetch URLs through a proxy server, then set your `http_proxy` environment variable appropriately; depending on your version of cron, put something like this in your crontab:

    http_proxy=http://myproxy.mycompany.com:3128/

If rawdog gets horribly confused (for instance, if the system clock is off by a few decades), you can clear its state by removing the `~/.rawdog/state` file (and `~/.rawdog/feeds/*.state`, if necessary).
