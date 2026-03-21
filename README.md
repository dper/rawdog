# README

__Rawdog__ (RSS Aggregator Without Delusions of Grandeur) is a feed aggregator, capable of producing a personal "river of news" or a public "planet" page. It supports all common feed formats, including RSS and Atom. It collects articles from a number of feeds and generates a static HTML page listing the newest articles in order.

This fork was created and is maintained by Douglas Perkins. After forking, the code was updated from Python 2 to Python 3, and many plugins and options were removed.

* <https://github.com/dper/rawdog>. This fork. Douglas's first commit was on July 13, 2022.
* <https://github.com/chirlu/rawdog>. The original code, written by Adam Sampson. Adam's first commit was on May 5, 2003.

## Dependencies

* Python 3.10 or later
* feedparser 6.0.8 or later

## Installation

1. Download the program. Copy `config` into `$HOME/.rawdog` and adjust the configuration settings as you prefer.
2. Adjust the configuration settings as you prefer.
3. Copy `style.css` to the same director as your HTML output.
4. Run the program. Typically, `rawdog --update --write` or the equivalent `rawdog -uw`.
5. Check that the output is correct. The first time you run it, articles might show up out of order. This corrects itself after a day or so, if new entries are being posted.

A cronjob entry such as the following is recommended:

    @hourly /path/to/rawdog -uw > /dev/null 2>&1

If you want rawdog to fetch URLs through a proxy server, then set your `http_proxy` environment variable appropriately; depending on your version of cron, put something like this in your crontab:

    http_proxy=http://myproxy.mycompany.com:3128/

If rawdog gets horribly confused (for instance, if the system clock is off by a few decades), you can clear its state by removing the `~/.rawdog/state` file (and `~/.rawdog/feeds/*.state`, if necessary).
