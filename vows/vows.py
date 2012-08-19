import os
from datetime import datetime
import operator
from pyvows import Vows, expect
from tagging import Document, DocumentTree, htmlCloud, tagResourceHTML, documentToHTML, generateAllTagResourceHTML


@Vows.batch
class BuildingDocumentTree(Vows.Context):
    class AddSixDocumentsWithSixTags(Vows.Context):

        def topic(self):
            tree = DocumentTree()
            now = datetime(2012, 1, 31)
            doc1 = Document(title="Doc 1", date=now, excerpt="Document one.", tags=('atag',))
            doc2 = Document(title="Doc 2", date=now, excerpt="Document two.", tags=('atag', 'btag'))
            doc3 = Document(title="Doc 3", date=now, excerpt="Document three.", tags=('atag', 'btag', 'ctag'))
            doc4 = Document(title="Doc 4", date=now, excerpt="Document four.", tags=('atag', 'btag', 'ctag', 'dtag'))
            doc5 = Document(title="Doc 5", date=now, excerpt="Document five.", tags=('atag', 'btag', 'ctag', 'dtag', 'etag'))
            doc6 = Document(title="Doc 6", date=now, excerpt="Document six.", tags=('atag', 'btag', 'ctag', 'dtag', 'etag', 'ftag'))
            tree.add(doc1)
            tree.add(doc2)
            tree.add(doc3)
            tree.add(doc4)
            tree.add(doc5)
            tree.add(doc6)
            return tree, doc1, doc2, doc3, doc4, doc5, doc6

        def should_have_six_tags(self, topic):
            tree, doc1, doc2, doc3, doc4, doc5, doc6 = topic
            expect(tree.tags.keys()).to_be_like(['atag', 'btag', 'ctag', 'dtag', 'etag', 'ftag'])

        def should_have_six_documents_with_atag(self, topic):
            tree, doc1, doc2, doc3, doc4, doc5, doc6 = topic
            expect(tree.tags['atag']).to_be_like([doc1, doc2, doc3, doc4, doc5, doc6])

        def should_have_five_documents_with_btag(self, topic):
            tree, doc1, doc2, doc3, doc4, doc5, doc6 = topic
            expect(tree.tags['btag']).to_be_like([doc2, doc3, doc4, doc5, doc6])

        def should_have_four_documents_with_ctag(self, topic):
            tree, doc1, doc2, doc3, doc4, doc5, doc6 = topic
            expect(tree.tags['ctag']).to_be_like([doc3, doc4, doc5, doc6])

        def should_have_three_documents_with_ctag(self, topic):
            tree, doc1, doc2, doc3, doc4, doc5, doc6 = topic
            expect(tree.tags['dtag']).to_be_like([doc4, doc5, doc6])

        def should_have_two_documents_with_etag(self, topic):
            tree, doc1, doc2, doc3, doc4, doc5, doc6 = topic
            expect(tree.tags['etag']).to_be_like([doc5, doc6])

        def should_have_one_document_with_ftag(self, topic):
            tree, doc1, doc2, doc3, doc4, doc5, doc6 = topic
            expect(tree.tags['ftag']).to_be_like([doc6])

        def should_create_cloud_with_six_weights(self, topic):
            tree, doc1, doc2, doc3, doc4, doc5, doc6 = topic
            cloud = tree.cloudify(minCount=0, numBuckets=6, suffix=".htm", baseURL="/blog/tags/")
            expect(cloud).to_be_like([('atag', 6, "/blog/tags/atag.htm"),
                                      ('btag', 5, "/blog/tags/btag.htm"),
                                      ('ctag', 4, "/blog/tags/ctag.htm"),
                                      ('dtag', 3, "/blog/tags/dtag.htm"),
                                      ('etag', 2, "/blog/tags/etag.htm"),
                                      ('ftag', 1, "/blog/tags/ftag.htm")])

        def should_create_cloud_with_three_weights(self, topic):
            tree, doc1, doc2, doc3, doc4, doc5, doc6 = topic
            cloud = tree.cloudify(minCount=0, numBuckets=3, suffix=".htm", baseURL="/blog/tags/")
            expect(cloud).to_be_like([('atag', 3, "/blog/tags/atag.htm"),
                                      ('btag', 2, "/blog/tags/btag.htm"),
                                      ('ctag', 2, "/blog/tags/ctag.htm"),
                                      ('dtag', 1, "/blog/tags/dtag.htm"),
                                      ('etag', 1, "/blog/tags/etag.htm")])

        def should_create_cloud_with_six_weights_and_ignore_counts_less_than_two(self, topic):
            tree, doc1, doc2, doc3, doc4, doc5, doc6 = topic
            cloud = tree.cloudify(minCount=2, numBuckets=6, suffix=".htm", baseURL="/blog/tags/")
            expect(cloud).to_be_like([('atag', 6, "/blog/tags/atag.htm"),
                                      ('btag', 5, "/blog/tags/btag.htm"),
                                      ('ctag', 4, "/blog/tags/ctag.htm"),
                                      ('dtag', 3, "/blog/tags/dtag.htm"),
                                      ('etag', 2, "/blog/tags/etag.htm"),])

        def create_html_cloud(self, topic):
            tree, doc1, doc2, doc3, doc4, doc5, doc6 = topic
            cloud = tree.cloudify(minCount=2, numBuckets=6, suffix=".htm", baseURL="/blog/tags/")
            # sort alpha by tag name
            cloud = sorted(cloud, key=operator.itemgetter(0))
            expect(htmlCloud(cloud)).to_equal("""<div class="tag-cloud"><a class="tag-6" href="/blog/tags/atag.htm">atag</a><a class="tag-5" href="/blog/tags/btag.htm">btag</a><a class="tag-4" href="/blog/tags/ctag.htm">ctag</a><a class="tag-3" href="/blog/tags/dtag.htm">dtag</a><a class="tag-2" href="/blog/tags/etag.htm">etag</a></div>""")

        def create_html_document_for_one_tag(self, topic):
            """Yes this is a horrible and brittle test..."""
            tree, doc1, doc2, doc3, doc4, doc5, doc6 = topic
            html = tagResourceHTML("atag", tree.tags["atag"], dateFormat="2012/01/31 0:00:00")
            expect(html).to_equal('Articles tagged with \'atag\'\nmeta-creation_date: 2012/01/31 0:00:00\n\n<div class="tag-docs"><div class="tag-doc date"><h2><a href="">Doc 1</a></h2><div class="date">31 Jan 2012</div><div class="body"><p>Document one.</p><a class="seemore" href="">Read more...</a><ul class="tags"><li class="tag"><a href="/atag.html">atag</a></li></ul></div></div><div class="tag-doc date"><h2><a href="">Doc 2</a></h2><div class="date">31 Jan 2012</div><div class="body"><p>Document two.</p><a class="seemore" href="">Read more...</a><ul class="tags"><li class="tag"><a href="/atag.html">atag</a></li><li class="tag"><a href="/btag.html">btag</a></li></ul></div></div><div class="tag-doc date"><h2><a href="">Doc 3</a></h2><div class="date">31 Jan 2012</div><div class="body"><p>Document three.</p><a class="seemore" href="">Read more...</a><ul class="tags"><li class="tag"><a href="/atag.html">atag</a></li><li class="tag"><a href="/btag.html">btag</a></li><li class="tag"><a href="/ctag.html">ctag</a></li></ul></div></div><div class="tag-doc date"><h2><a href="">Doc 4</a></h2><div class="date">31 Jan 2012</div><div class="body"><p>Document four.</p><a class="seemore" href="">Read more...</a><ul class="tags"><li class="tag"><a href="/atag.html">atag</a></li><li class="tag"><a href="/btag.html">btag</a></li><li class="tag"><a href="/ctag.html">ctag</a></li><li class="tag"><a href="/dtag.html">dtag</a></li></ul></div></div><div class="tag-doc date"><h2><a href="">Doc 5</a></h2><div class="date">31 Jan 2012</div><div class="body"><p>Document five.</p><a class="seemore" href="">Read more...</a><ul class="tags"><li class="tag"><a href="/atag.html">atag</a></li><li class="tag"><a href="/btag.html">btag</a></li><li class="tag"><a href="/ctag.html">ctag</a></li><li class="tag"><a href="/dtag.html">dtag</a></li><li class="tag"><a href="/etag.html">etag</a></li></ul></div></div><div class="tag-doc date"><h2><a href="">Doc 6</a></h2><div class="date">31 Jan 2012</div><div class="body"><p>Document six.</p><a class="seemore" href="">Read more...</a><ul class="tags"><li class="tag"><a href="/atag.html">atag</a></li><li class="tag"><a href="/btag.html">btag</a></li><li class="tag"><a href="/ctag.html">ctag</a></li><li class="tag"><a href="/dtag.html">dtag</a></li><li class="tag"><a href="/etag.html">etag</a></li><li class="tag"><a href="/ftag.html">ftag</a></li></ul></div></div></div>')

        class GenerateTagHTMLFiles(Vows.Context):
            def topic(self, treeTopic):
                doctree = treeTopic[0]
                generateAllTagResourceHTML(doctree, "/tmp/tags")
                return doctree

            def atag_file_exists(self, doctree):
                expect(os.path.exists("/tmp/tags/atag.html")).to_be_true()

            def btag_file_exists(self, doctree):
                expect(os.path.exists("/tmp/tags/btag.html")).to_be_true()

            def ctag_file_exists(self, doctree):
                expect(os.path.exists("/tmp/tags/ctag.html")).to_be_true()

            def dtag_file_exists(self, doctree):
                expect(os.path.exists("/tmp/tags/dtag.html")).to_be_true()

            def etag_file_exists(self, doctree):
                expect(os.path.exists("/tmp/tags/etag.html")).to_be_true()

            def ftag_file_exists(self, doctree):
                expect(os.path.exists("/tmp/tags/ftag.html")).to_be_true()

    class AddDocumentsWithoutTags(Vows.Context):
        def topic(self):
            tree = DocumentTree()
            doc = Document()
            tree.add(doc)
            return tree, doc

        def documents_with_two_tags_have_two_tags(self, topic):
            tree, doc = topic
            expect(tree.tags.keys()).to_be_empty()


@Vows.batch
class ReadingDocument(Vows.Context):
    class ProcessingEmptyTagsLine(Vows.Context):
        def topic(self):
            return Document()._extractExplicitTags("")

        def no_tags_are_found(self, topic):
            expect(topic).to_be_empty()

    class ProcessingTagsLine(Vows.Context):
        def topic(self):
            return Document()._extractExplicitTags("TAGS: atag, btag")

        def two_tags_are_found(self, topic):
            expect(topic).to_length(2)

        def tags_include_atag(self, topic):
            expect(topic).to_be_like(["btag", "atag"])

    class ParsingTextWithoutTags(Vows.Context):
        def topic(self):
            doc = Document()
            doc.parse("A Title\nmeta-creation_date: 8/13/2012 10:20\n\n<p>some text goes here\n<div>div text</div>\n</p><p>ignore [[ATAG a tag]] [[BTAG b tag]]\nthis text</p>")
            return doc

        def should_find_title(self, topic):
            expect(topic.title).to_equal("A Title")

        def should_find_date(self, topic):
            expect(topic.date).to_equal(datetime(2012, 8, 13, 10, 20))

        def should_find_only_body_tags(self, topic):
            expect(topic.tags).to_be_like(("ATAG", "BTAG"))

        def should_find_excerpt(self, topic):
            expect(topic.excerpt).to_equal("some text goes here\n<div>div text</div>\n")

    class ParsingTextWithTags(Vows.Context):
        def topic(self):
            doc = Document()
            doc.parse("A Title\nmeta-creation_date: 8/13/2012 10:20\nTAGS: atag, btag\n<p>some text goes here</p><div>div text</div></p><p>ignore this [[ATAG a tag]] text</p>\n")
            return doc

        def should_find_title(self, topic):
            expect(topic.title).to_equal("A Title")

        def should_find_date(self, topic):
            expect(topic.date).to_equal(datetime(2012, 8, 13, 10, 20))

        def should_find_explicit_and_body_tags(self, topic):
            expect(topic.tags).to_be_like(("ATAG", "atag", "btag"))

        def should_find_excerpt(self, topic):
            expect(topic.excerpt).to_equal("some text goes here")
