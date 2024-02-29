# HTML fetcher

This script fetches urls from the given sitemap file

Created in Python 3.9.13

To run a sample execute:

`py main.py --cfg cfg/aniagotuje_conf.yml`

The description of parametres is included in the example config file 

`./cfg/aniagotuje_conf.yml`

Config file may contain not all the possible parametres, in this case the missing ones will be replaced with the default values.

To get a sitemap file access the `robots.txt` file of the website and follow the link with the sitemap if present. Example links for accessing `robots.txt`:

`https://www.newgrounds.com/robots.txt`

`https://aniagotuje.pl/robots.txt`

