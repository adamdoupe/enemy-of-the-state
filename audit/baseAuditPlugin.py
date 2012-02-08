import threading
from basePlugin import basePlugin
from mock_debugging_object import *
import knowledgeBase as kb

kb=kb.kb

class baseAuditPlugin(basePlugin):
    def __init__(self, crawler):
        basePlugin.__init__( self, crawler )
        self.crawler = crawler
        self._urlOpener = None

    def audit_wrapper( self, fuzzable_request ):
        pass

    def audit( self, freq ):
        pass

    def _analyzeResult( self, mutant, res ):
        pass

    def _hasNoBug( self, plugin_name, kb_name, uri, variable ):
        '''
        Verify if a (uri, variable) has a reported vulnerability in the kb or not.
        
        @parameter plugin_name: The name of the plugin that supposingly reported the vulnerability
        @parameter kb_name: The name of the variable in the kb, where the vulnerability was saved.
        
        @parameter uri: The url object where we should search for bugs.
        @parameter variable: The variable that is queried for bugs.
        
        @return: True if the (uri, variable) has NO vulnerabilities reported.
        '''
        vuln_list = kb.getData( plugin_name , kb_name )
        url = uri.uri2url()
        
        for vuln in vuln_list:
            if vuln.getVar() == variable and vuln.getURL().uri2url() == url:
                return False
                
        return True
        
    def getType( self ):
        return 'audit'




