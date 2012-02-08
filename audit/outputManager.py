import os
import sys
import string

# severity constants for vuln messages
import severity as severity

# I changed this to output everything to the console
class outputManager:
    '''
    This class manages output. 
    It has a list of output plugins and sends the events to every plugin on that list.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        self._outputPluginList = []
        self._outputPlugins = []
        self._pluginsOptions = {}
        self._echo = True

    def _make_printable(self, a_string):
        result = ''
        for char in a_string:
            if char in string.printable:
                result += char
        return result


    def debug(self, message, newLine = True ):
        '''
        Sends a debug message to every output plugin on the list.
        
        @parameter message: Message that is sent.
        '''
        to_print = message
        if newLine == True:
            to_print += '\r\n'
        sys.stdout.write( self._make_printable(to_print) )
        sys.stdout.flush()

    def information(self, message, newLine = True ):
        '''
        Sends a informational message to every output plugin on the list.
        
        @parameter message: Message that is sent.
        '''
        to_print = message
        if newLine == True:
            to_print += '\r\n'
        sys.stdout.write( self._make_printable(to_print) )
        sys.stdout.flush()
            
    def error(self, message, newLine = True ):
        '''
        Sends an error message to every output plugin on the list.
        
        @parameter message: Message that is sent.
        '''
        self.information(message, newLine)

    def logHttp( self, request, response ):
        '''
        Sends the request/response object pair to every output plugin on the list.
        
        @parameter request: A fuzzable request object
        @parameter response: A httpResponse object
        '''
        self.information(message, newLine)
            
    def vulnerability(self, message, newLine = True, severity=severity.MEDIUM ):
        '''
        Sends a vulnerability message to every output plugin on the list.
        
        @parameter message: Message that is sent.
        '''
        self.information(message, newLine)

    def console( self, message, newLine = True ):
        '''
        This method is used by the w3af console to print messages to the outside.
        '''
        self.information(message, newLine)
    
    def echo( self, onOff ):
        '''
        This method is used to enable/disable the output.
        '''
        self._echo = onOff

out = outputManager()
