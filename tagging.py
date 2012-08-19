import cStringIO
from datetime import datetime
import os
import re
import string
import sys

import urlparse


class DocumentTree(object):
    """
    A collection of Documents and tagging information about them.
    Once constructed an instance can be used to generate a tag cloud
    and static HTML pages of Documents containing each tag.
    """
    def __init__(self):
        self.tags = {}

    def add(self, document):
        """Add a Document into this collection"""
        for tag in document.tags:
            self.tags.setdefault(tag, []).append(document)

    def cloudify(self, minCount=2, numBuckets=6, suffix=".html", baseURL="/"):
        """Output a list of tuples of the form:
        [(tagname, bucketNumber, url), ...]"""
        out = []
        maxCount = max([len(x) for x in self.tags.values()])
        bucketSize = maxCount / float("%d" % numBuckets)
        for tag, listOfDocs in self.tags.items():
            count = len(listOfDocs)
            bucket = int(count / bucketSize)
            if count < minCount or bucket < 1:
                continue
            out.append((tag, bucket, baseURL+tag+suffix))
        return out


class Document(object):
    """Represent interesting tagged information about a single document/blog post"""

    def __init__(self, url='', excerpt='', title='', date=None, tags=None, file=None):
        self.tags = tags or ()
        self.excerpt = excerpt
        self.title = title
        self.date = date or datetime.now()
        self.url = url
        self.file = file
        if file:
            self.file = file
            self.load(file)

    def load(self, fileName):
        fp = open(fileName)
        self._parseLines(fp)
        fp.close()

    def parse(self, text):
        fp = cStringIO.StringIO(text)
        self._parseLines(fp)

    def _parseLines(self, fp):
        self.title = fp.readline().strip()
        line = fp.readline()
        while line:
            date = self._extractDate(line)
            if date:
                self.date = date
            else:
                tags = self._extractExplicitTags(line)
                if tags:
                    self.tags = tags
                    break
            line = fp.readline()

        bodyTags = self._extractTagsFromBody(fp.getvalue())
        if bodyTags:
            self.tags = tuple(set(self.tags + bodyTags))

        excerpt = self._extractExcerpt(fp.getvalue())
        if excerpt:
            self.excerpt = excerpt

    def _extractExplicitTags(self, line):
        tags = ()
        match = re.match('^Tags:', line)
        if match:
            tags = tuple([x.strip() for x in line[match.end():].split(",")])
        return tags

    def _extractDate(self, line):
        match = re.search(r'^meta-creation_date:\s*(.*?)$', line)
        return match and datetime.strptime(match.groups(1)[0], "%m/%d/%Y %H:%M") or ''

    def _extractExcerpt(self, lines):
        match = re.search(r'<p>(.*?)</p>?', lines, flags=re.IGNORECASE|re.MULTILINE|re.DOTALL)
        return match and match.groups(1)[0] or ''

    def _extractTagsFromBody(self, lines):
        """tags are of the form [[tagname words used in link on page]]"""
        reg = re.compile(r'(\[\[(\w+)[^[]*?\]\])+', flags=re.MULTILINE)
        return tuple([x.group(2) for x in re.finditer(reg, lines)])



def buildDocumentTree(directoryRoot=None, suffix="", baseURL="/", docClass=Document):
    """
    Helper/example of populating DocumentTree
    For my needs:
        When using directoryRoot and baseURL run from a relative directory
        so each Document.url is set according to relative directory from the
        directoryRoot.

        If suffix is supplied any suffix on discovered file will be replaced
        by the suffix keyword.
    """
    tree = DocumentTree()
    for root, subFolders, files in os.walk(directoryRoot):
        for filename in files:
            filePath = os.path.join(root, filename)
            url = urlparse.urljoin(baseURL, filePath)
            if suffix:
                url = url.split(".")[0] + "." + suffix
            doc = docClass(file=filePath,
                           url=url)
            tree.add(doc)
    return tree

# Helper functions to provide HTML output of:
# - Documents associated with a tag
#   I use this to generate a static HTML page for each tag. That page contains a link to each document
# - Tag cloud
#   Statically generated HTML fragment with tag name links to each page generated above.
#
# Two ways to customize content:
# 1. override templates
# 2. use functools.partial to wrap functions with customizations
#
TagTemplate = string.Template("""<li class="tag"><a href="$url">$name</a></li>""")
TagWrapperTemplate = string.Template("""<ul class="tags">$tags</ul>""")
def tagFilePath(name,
                baseURL="/",
                suffix="html"):
    """
    Generate URL for resource containing all Documents having this tag name.
    """
    return urlparse.urljoin(baseURL, name+"."+suffix)

def tagsToHTML(tags,
               tagToUrl=tagFilePath,
               parentElement=TagWrapperTemplate,
               tagTemplate=TagTemplate):
    """
    Generate HTML (fragment) for a list of tag names each linked to their own page.
    Assumes all tag page URLs are on the same path
    """
    tags = "".join([tagTemplate.safe_substitute(name=name, url=tagToUrl(name)) for name in tags])
    html = parentElement.safe_substitute(tags=tags)
    return html

DocumentTemplate = string.Template("""<div class="tag-doc date"><h2><a href="$url">$title</a></h2><div class="date">$date</div><div class="body"><p>$excerpt</p><a class="seemore" href="$url">Read more...</a>$tags</div></div>""")

def documentToHTML(doc,
                   dateFormat="%d %b %Y",
                   tagFormatter=tagsToHTML,
                   documentTemplate=DocumentTemplate):
    """
    Generate HTML for Document fragment for inclusion on HTML page
    listing all Documents for a specific tag.
    """
    html = documentTemplate.safe_substitute(title=doc.title,
                                            url=doc.url,
                                            date=doc.date.strftime(dateFormat),
                                            excerpt=doc.excerpt,
                                            tags=tagFormatter(doc.tags))
    return html

PageTemplate = string.Template("""Articles tagged with '$tag'
meta-creation_date: $date

<div class="tag-docs">$docs</div>""")

def tagResourceHTML(tag,
                    docs,
                    docFormatter=documentToHTML,
                    dateFormat="%m/%d/%Y 0:00",
                    pageTemplate=PageTemplate):
    """
    Generate HTML content for a list of
    Documents associated with the specified tag in the order provided.
    """
    output = pageTemplate.safe_substitute(docs="".join([documentToHTML(x) for x in docs]),
                                          tag=tag,
                                          date=datetime.now().strftime(dateFormat))
    return output

def generateAllTagResourceHTML(doctree, destPath, dateFormat="%m/%d/%Y %H:%M", suffix=".html"):
    """
    Example writing HTML files for each tag to disk
    """
    try:
        os.makedirs(destPath)
    except OSError:
        pass
    for tag, docs in doctree.tags.items():
        # sort docs newest to oldest
        docs = sorted(docs, key=lambda x: x.date)
        html = tagResourceHTML(tag, docs, dateFormat=dateFormat)
        with open(os.path.join(destPath, tag+suffix), "w") as f:
            f.write(html)

CloudTemplate = string.Template("""<div class="tag-cloud">$tags</div>""")
CloudTagTemplate = string.Template("""<a class="tag-$bucket" href="$url">$tag</a>""")

def htmlCloud(cloudifyOutput,
              cloudTemplate=CloudTemplate,
              cloudTagTemplate=CloudTagTemplate):
    """Sort cloudifyOutput to suit your outputting needs"""
    tags = "".join([cloudTagTemplate.safe_substitute(tag=tag, bucket=bucket, url=url) for tag, bucket, url in cloudifyOutput])
    output = cloudTemplate.safe_substitute(tags=tags)
    return output

