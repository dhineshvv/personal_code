#!/usr/bin/env python
"""This cgi script should print out a list of all unique del.icio.us posts with a given tag

Put this file on a webserver with python CGI access and call it like:
    <url of this script>?tag=python+ipod
    
If the webserver runs windows, you will have to replace the shebang line above
this text with the line:
    #!<path to your python installation>

This script is in the public domain; you may do with it as you like. If you
improve it or hate it, I'd like to hear from you at bill.mill@gmail.com . Bill
Mill (yes that's my real name) released this script on 05.09.05.

Please respect the del.icio.us API and call the gen_tag(...) function no more
frequently than once a second.
"""
import cgi, cgitb
cgitb.enable()
import re, time, urllib
del_url = 'http://del.icio.us/'

TITLE = re.compile('href="(\S+)">([\S ]+)</a></h3>')
EXTENDED = re.compile('class="extended">([\S ]+)</div>')
TAG = re.compile('href="\S*?">(.*?)<')
DATE = re.compile('... on ([\d\-:]+)')

def gen_tag(f):
    """yields tag dictionaries from an open del.icio.us file handle

    f should be an open file handle to a del.icio.us page, whether stored on
    disk or opened with urllib.urlopen(<link>).

    This function will yield dictionaries with the following members:
        link: the url being linked to
        title: the title given to the post
        extended: extended text (set to '' if null)
        date: the date of the post
        tags: a list of the tags attached to the post
        author: the author of the post
    
    Note that this function only depends on the "re" module.

    TODO: handle utf-8
    """
    for line in f:
        if line.startswith('<div class="post">'):
            data = {}
            data['link'], data['title'] = TITLE.search(f.next()).groups()
            line = f.next()
            r = EXTENDED.search(line)
            if r:
                data['extended'] = r.groups()[0].strip()
                line = f.next()
            else:
                data['extended'] = ''
            data['tags'] = TAG.findall(line)
            data['date'] = DATE.search(line).groups()[0]
            data['author'] = data['tags'].pop()
            yield data

def html_delpost(post):
    """output a post as html"""
    print '<a href="%s">%s</a><br>' % (post['link'], post['title'])
    if post['extended']:
        print '%s<br>' % post['extended']
    print 'to: ',
    for tag in post['tags']:
        print '<a href="%stag/%s">%s</a>, ' % (del_url, tag, tag)
    print 'by %d users<p>' % post['users']

def gen_unique(tag, depth=10):
    """returns a dictionary of unique posts with the given tag

    the tag parameter is the tag to search for; I used "python+ipod" in my
    testing.
    Depth tells this function how many pages back in the tag history to search
    for new links; remember that this function will wait a second between
    each level before you set depth really high.

    Returns a dictionary whose keys are the unique URLs and whose values are the
    tag dictionaries as generated by gen_tag .
    """
    visited = {}
    for i in range(1, depth + 1):
        p = urllib.urlopen('%stag/%s?page=%d' % (del_url, tag, i))
        t1 = time.time()
        for t in gen_tag(p):
            link = t['link']
            if link not in visited:
                visited[link] = t
                visited[link]['users'] = 1
            else:
                for kw in t['tags']:
                    if kw not in visited[link]['tags']:
                        visited[link]['tags'].append(kw)
                if t['extended'].strip():
                    if visited[link]['extended']:
                        visited[link]['extended'] += '<p>'
                    visited[link]['extended'] += t['extended']
                visited[link]['users'] += 1
        #now sleep for at least a second, to follow the del.icio.us api
        s = 1 - (time.time() - t1)
        time.sleep(s)
    return visited

#I print out this information as a webpage, but you're certainly welcome to
#modify the script to output it however you want it
print "Content-Type: text/html\n"
print "<html><head><title>Del.icio.us Uniqueness Engine</title></head><body>"
form = cgi.FieldStorage()
if form.has_key('tag'):
    tag = form['tag'].value
    print "<h2>%s</h2><p>" % tag
    u = gen_unique(urllib.quote_plus(tag))
    for post in u.itervalues():
        html_delpost(post)
else:
    print "Please put a ?tag=<value> at the end of the url"
print "</body></html>"
