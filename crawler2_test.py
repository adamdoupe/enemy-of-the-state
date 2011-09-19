#!/usr/bin/env python

import crawler2 as crawler

import BaseHTTPServer
import SimpleHTTPServer
import threading
import unittest

LISTEN_ADDRESS = '127.0.0.1'
LISTEN_PORT = 4566
BASE_URL = 'http://%s:%d/test/' % (LISTEN_ADDRESS, LISTEN_PORT)

class BaseCrawlerTest(unittest.TestCase):
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
        self.assertTrue(e.cr.headreqresp.next is None)
        self.assertTrue(e.ag is None)

if __name__ == '__main__':
    unittest.main()
