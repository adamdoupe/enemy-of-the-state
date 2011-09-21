#!/usr/bin/env python

import crawler2 as crawler

import BaseHTTPServer
import logging
import os
import SimpleHTTPServer
import threading
import unittest

TEST_BASE_PATH = 'test/sites/'

LISTEN_ADDRESS = '127.0.0.1'
LISTEN_PORT = 4566
BASE_URL = 'http://%s:%d/test/sites/' % (LISTEN_ADDRESS, LISTEN_PORT)

EXT_LISTEN_ADDRESS = '127.0.0.1'
EXT_LISTEN_PORT = 80
EXT_BASE_URL = 'http://%s:%d/test/sites/' % (EXT_LISTEN_ADDRESS, EXT_LISTEN_PORT)

class LocalCrawlerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = BaseHTTPServer.HTTPServer(
                (LISTEN_ADDRESS, LISTEN_PORT),
                SimpleHTTPServer.SimpleHTTPRequestHandler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        self.ff = crawler.FormFiller()
        self.e = crawler.Engine(self.ff, None)

    def test_single_page(self):
        url = BASE_URL + 'single/single.html'
        e = self.e
        e.main([url])
        self.assertIsNone(e.cr.headreqresp.next)
        self.assertIsInstance(e.cr.headreqresp.response.page, crawler.Page)
        self.assertEqual(len(e.cr.headreqresp.response.page.links), 0)
        self.assertIsNone(e.ag)

class ExtCrawlerTest(unittest.TestCase):
    def setUp(self):
        self.ff = crawler.FormFiller()
        self.e = crawler.Engine(self.ff, None)

    def test_single_page(self):
        url = EXT_BASE_URL + 'single/single.html'
        e = self.e
        e.main([url])
        self.assertIsNone(e.cr.headreqresp.next)
        self.assertIsInstance(e.cr.headreqresp.response.page, crawler.Page)
        self.assertEqual(len(e.cr.headreqresp.response.page.links), 0)
        self.assertIsNone(e.ag)

    def test_simple(self):
        # Truncate status files
        fd = os.open(TEST_BASE_PATH + '/simple/pages.data',
                     os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
        os.fchmod(fd, 0666)
        os.close(fd)
        fd = os.open(TEST_BASE_PATH + '/simple/pages.lock',
                     os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
        os.fchmod(fd, 0666)
        os.close(fd)
        url = EXT_BASE_URL + 'simple/index.php'
        e = self.e
        e.main([url])
        self.assertEqual(len(e.ag.absrequests), 4)
        urls = set(r.split('/')[-1] for ar in e.ag.absrequests for r in ar.requestset)
        self.assertEqual(len(urls), 21)
        self.assertEqual(set(['viewpage.php?id=%d' % i for i in range(18)] +
                             ['addpage.php',
                              'index.php',
                              'static.php']),
                         urls)
        self.assertEqual(len(e.ag.abspages), 4)

    def test_changing_state(self):
        os.chmod(TEST_BASE_PATH + '/changing_state', 0777)
        try:
            os.unlink(TEST_BASE_PATH + '/changing_state/.lock')
        except OSError:
            pass
        try:
            os.unlink(TEST_BASE_PATH + '/changing_state/a')
        except OSError:
            pass
        url = EXT_BASE_URL + '/changing_state/index.php'
        e = self.e
        e.main([url])
        self.assertEqual(len(e.ag.absrequests), 4)
        urls = set(r.split('/')[-1] for ar in e.ag.absrequests for r in ar.requestset)
        self.assertEqual(len(urls), 4)
        self.assertEqual(set(['a.php',
                              'b.php',
                              'index.php',
                              'changestate.php']),
                         urls)
        self.assertEqual(len(e.ag.abspages), 4)

if __name__ == '__main__':
    #logging.basicConfig(level=logging.DEBUG)
    unittest.main()
