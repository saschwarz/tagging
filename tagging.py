import cStringIO
from datetime import datetime
import math
import os
import re
import string
import sys
import urlparse
from operator import attrgetter


class DocumentTree(object):
    """
    A collection of Documents and tagging information about them.
    Once constructed an instance can be used to generate a tag cloud
    and static HTML pages of Documents containing each tag.
    """
    def __init__(self):
        self.tags = {} # dict of tag names to Documents
        self.documents = []

    def add(self, document):
        """Add a Document into this collection"""
        self.documents.append(document)
        for tag in document.tags:
            self.tags.setdefault(tag, []).append(document)

    def cloudify(self,
                 minCount=2,
                 numBuckets=6,
                 suffix=".html",
                 baseURL="/blog/tags/",
                 blackList=[],
                 algo='log'):
        """Output a list of tuples of the form:
        [(tagname, bucketNumber, url), ...]"""
        out = []
        maxCount = max([len(x) for x in self.tags.values()])
        bucketSize = maxCount / float("%d" % numBuckets)
        for tag, listOfDocs in self.tags.items():
            count = len(listOfDocs)
            if algo == 'log':
                bucket = int(math.log(count))
            else:
                bucket = int(count / bucketSize)
            # print tag, count, bucket
            if count < minCount or bucket < 1 or tag in blackList:
                continue
            out.append((tag, bucket, baseURL+tag+suffix))
        return out

    def updateRelated(self, limit=6, ignoreTags=[]):
        for doc in self.documents:
            candidates = set()
            # only look at docs (besides the current one) with at least one of our tags
            for tag in filter(lambda x: x not in ignoreTags, doc.tags):
                candidates.update(filter(lambda x: x != doc, self.tags[tag]))
            doc.related = sorted(sorted(candidates, key=attrgetter('date'), reverse=True), key=lambda x: len(doc.tags.intersection(x.tags)), reverse=True)[:limit]

class Document(object):
    """Represent interesting tagged information about a single document/blog post"""

    def __init__(self,
                 url='',
                 excerpt='',
                 title='',
                 date=None,
                 tags=None,
                 file=None,
                 related=None,
                 body=''):
        self.tags = tags and set(tags) or set()
        self.excerpt = excerpt
        self.title = title
        self.date = date or datetime.now()
        self.url = url
        self.file = file
        self.body = body
        self.related = related or set()
        if file:
            self.file = file
            self.load(file)

    def __repr__(self):
        return " ".join((self.title, self.url))

    def load(self, fileName):
        fp = cStringIO.StringIO(open(fileName).read())
        # each element of path are also tags (except root and filename)
        self.tags = set(fileName.split(os.path.sep)[1:-1])
        # print fileName, self.tags
        self._parseLines(fp)
        fp.close()

    def parse(self, text):
        fp = cStringIO.StringIO(text)
        self._parseLines(fp)

    def write(self, fileName, formattedTags=None, formattedRelated=None):
        """Rewrite with extracted tags to specified file overwriting it if it exists"""
        with open(fileName, "w") as fp:
            self._write_head(fp, formattedTags, formattedRelated)
            self._write_body(fp)

    def _write_head(self, fp, formattedTags, formattedRelated):
        fp.write(self.title+"\n")
        fp.write("meta-creation_date: %s\n" % self.date.strftime("%m/%d/%Y %H:%M"))
        fp.write("Tags: %s\n" % ", ".join(self.tags))
        if formattedTags:
            fp.write("meta-tags: %s\n" % formattedTags)
        if formattedRelated:
            fp.write("meta-related: %s\n" % formattedRelated)
        fp.write("\n") # separates head from body

    def _write_body(self, fp):
        fp.write(self.body)

    def _parseLines(self, fp):
        self._parseHead(fp)
        self._parseBody(fp)

    def _parseHead(self, fp):
        self.title = fp.readline().strip()
        line = fp.readline()
        while line:
            date = self._extractDate(line)
            if date:
                self.date = date
            else:
                tags = self._extractExplicitTags(line)
                if tags:
                    self.tags.update(tags)
                    break
            line = fp.readline().strip()

    def _parseBody(self, fp):
        self.body = "".join(fp.readlines())
        bodyTags = self._extractTagsFromBody(self.body)
        if bodyTags:
            self.tags.update(bodyTags)

        excerpt = self._extractExcerpt(self.body)
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
        if match:
            for format in ("%m/%d/%Y %H:%M", "%m/%d/%Y %H:%M:%s", "%m/%d/%Y"):
                try:
                    return datetime.strptime(match.groups(1)[0], format)
                except ValueError:
                    pass
        return ""

    def _extractExcerpt(self, lines):
        match = re.search(r'<p>(.*?)</p>?', lines, flags=re.IGNORECASE|re.MULTILINE|re.DOTALL)
        return match and match.groups(1)[0] or ''

    def _extractTagsFromBody(self, lines):
        """tags are of the form [[tagname words used in link on page]]"""
        reg = re.compile(r'(\[\[([\w-]+)[^[]*?\]\])+', flags=re.MULTILINE)
        return tuple([x.group(2) for x in re.finditer(reg, lines)])



def buildDocumentTree(directoryRoot=None,
                      findSuffix=".txt",
                      suffix="html",
                      baseURL="/",
                      docClass=Document,
                      dirBlackList=[]):
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
        listed = False
        for folder in dirBlackList:
            if root.startswith(folder):
                listed = True
                break
        if listed:
            continue
        for filename in files:
            if not filename.endswith(findSuffix):
                continue
            filePath = os.path.join(root, filename)
            url = urlparse.urljoin(baseURL, filePath)
            if suffix:
                url = url.split(".")[0] + "." + suffix
            # print "filePath:", filePath
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
TagWrapperTemplate = string.Template("""<table border="0" class="tags-table"><tr><td class="tags-label">Tags: <i class="icon-tags"></i></td><td><ul class="tags">$tags</ul></td</tr></table>""")
def tagFilePath(name,
                baseURL="/blog/tags/",
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

DocumentTemplate = string.Template("""<article style="clear:both;"><h2><a href="$url">$title</a></h2><div class="date">$date</div><div class="body"><p>$excerpt</p><p><a class="seemore" href="$url">Read more...</a></p>$tags</div></article>""")

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

PageTemplate = string.Template("""$num Articles Tagged With: '$tag'
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
                                          num=len(docs),
                                          tag=tag,
                                          date=datetime.now().strftime(dateFormat))
    return output

def generateTagResourcesHTML(doctree, tags, destPath, dateFormat="%m/%d/%Y %H:%M:00", suffix=".txt"):
    """
    Example writing HTML files for each tag to disk
    """
    try:
        os.makedirs(destPath)
    except OSError:
        pass
    for tag in tags:
        docs = doctree.tags[tag]
        # sort docs newest to oldest
        docs = sorted(docs, key=lambda x: x.date, reverse=True)
        html = tagResourceHTML(tag, docs, dateFormat=dateFormat)
        with open(os.path.join(destPath, tag+suffix), "w") as f:
            f.write(html)

CloudTemplate = string.Template("""<div class="tag-cloud">$tags</div>""")
CloudTagTemplate = string.Template("""<a class="tag-$bucket" href="$url">$tag</a> """)

def htmlCloud(cloudifyOutput,
              cloudTemplate=CloudTemplate,
              cloudTagTemplate=CloudTagTemplate):
    """Sort cloudifyOutput to suit your outputting needs."""
    tags = "".join([cloudTagTemplate.safe_substitute(tag=tag, bucket=bucket, url=url) for tag, bucket, url in cloudifyOutput])
    output = cloudTemplate.safe_substitute(tags=tags)
    return output


if __name__ == "__main__":
    def relatedToHTML(docs):
        ret = "".join(["""<li><a href="%s">%s</a></li>""" % (doc.url, doc.title) for doc in docs])
        return ret and """<div class="related"><div class="related-label">Related Articles:</div><ul">""" + ret + "</ul></div>" or ''

    def validTags(element):
        return "_" not in element[0]

    tree = buildDocumentTree(".", baseURL="/blog/", dirBlackList=['./tech', './tags'])
    cloud = filter(validTags, tree.cloudify())

    # sort by tag name
    html = htmlCloud(sorted(cloud, key=lambda x : x[0].lower()))
    # put html cloud into fragment file for inclusion in other pages:
    with open("../plugins/filedata/tagcloud", "w") as cloudFile:
        cloudFile.write(html)
    # generate tag files only for the tags in the cloud
    # tags = [tag for tag, bucket, url in cloud]
    tags = tree.tags
    generateTagResourcesHTML(tree, tags, "./tags")

    tree.updateRelated(ignoreTags=['journal', 'agility',])
    # now update each source file with the updated tags and formatted tags
    for doc in tree.documents:
        doc.write(doc.file + ".new",
                  formattedTags=tagsToHTML(doc.tags),
                  formattedRelated=relatedToHTML(doc.related))
