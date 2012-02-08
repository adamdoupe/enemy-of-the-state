import pdb
import threading
from mock_debugging_object import *
from w3afException import w3afException

class basePlugin(object):

    def __init__(self, crawler_info):
        '''
        Create some generic attributes that are going to be used by most plugins.
        '''
        # The crawler will be used to make the requests in _sendMutant
        self.response_queue = crawler_info[0]
        self.request_queue = crawler_info[1]

        self._urlOpener = mock_debugging_object("basePlugin._urlOpener")
        # Thread Manager, used to execute lots of tasks. Going to have to stub it.
        self._tm = mock_debugging_object("basePlugin._tm")
        self._plugin_lock = threading.RLock()

    def setUrlOpener( self, urlOpener):
        pass

    def setOptions( self, optionsMap ):
        pass

    def setOptions( self, optionsMap ):
        '''
        Sets the Options given on the OptionList to self. The options are the result of a user
        entering some data on a window that was constructed using the options that were
        retrieved from the plugin using getOptions()
        
        This method MUST be implemented on every plugin. 
        
        @return: No value is returned.
        ''' 
        raise w3afException('Plugin "'+self.getName()+'" is not implementing required method setOptions' )
        
    def getOptions(self):
        pass

    def setOptions( self, optionsMap ):
        '''
        Sets the Options given on the OptionList to self. The options are the result of a user
        entering some data on a window that was constructed using the options that were
        retrieved from the plugin using getOptions()
        
        This method MUST be implemented on every plugin. 
        
        @return: No value is returned.
        ''' 
        raise w3afException('Plugin "'+self.getName()+'" is not implementing required method setOptions' )
        
    def getOptions(self):
        '''
        @return: A list of option objects for this plugin.
        '''
        raise w3afException('Plugin "'+self.getName()+'" is not implementing required method getOptions' )

    def getPluginDeps( self ):
        pass

    def setOptions( self, optionsMap ):
        '''
        Sets the Options given on the OptionList to self. The options are the result of a user
        entering some data on a window that was constructed using the options that were
        retrieved from the plugin using getOptions()
        
        This method MUST be implemented on every plugin. 
        
        @return: No value is returned.
        ''' 
        raise w3afException('Plugin "'+self.getName()+'" is not implementing required method setOptions' )
        
    def getOptions(self):
        '''
        @return: A list of option objects for this plugin.
        '''
        raise w3afException('Plugin "'+self.getName()+'" is not implementing required method getOptions' )

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be 
        runned before the current one.
        '''
        raise w3afException('Plugin is not implementing required method getPluginDeps' )

    def getDesc( self ):
        pass

    def setOptions( self, optionsMap ):
        '''
        Sets the Options given on the OptionList to self. The options are the result of a user
        entering some data on a window that was constructed using the options that were
        retrieved from the plugin using getOptions()
        
        This method MUST be implemented on every plugin. 
        
        @return: No value is returned.
        ''' 
        raise w3afException('Plugin "'+self.getName()+'" is not implementing required method setOptions' )
        
    def getOptions(self):
        '''
        @return: A list of option objects for this plugin.
        '''
        raise w3afException('Plugin "'+self.getName()+'" is not implementing required method getOptions' )

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be 
        runned before the current one.
        '''
        raise w3afException('Plugin is not implementing required method getPluginDeps' )

    def getDesc( self ):
        '''
        @return: A description of the plugin.
        
        >>> b = basePlugin()
        >>> b.__doc__ = 'abc'
        >>> b.getDesc()
        'abc'
        >>> b = basePlugin()
        >>> b.__doc__ = '    abc\t'
        >>> b.getDesc()
        'abc'
        '''
        if self.__doc__ is not None:
            res2 = self.__doc__.replace( '\t' , '' )
            res2 = self.__doc__.replace( '    ' , '' )
            res = ''.join ( [ i for i in res2.split('\n') if i != '' and '@author' not in i ] )
        else:
            res = ''
        return res
    
    def getLongDesc( self ):
        pass

    def setOptions( self, optionsMap ):
        '''
        Sets the Options given on the OptionList to self. The options are the result of a user
        entering some data on a window that was constructed using the options that were
        retrieved from the plugin using getOptions()
        
        This method MUST be implemented on every plugin. 
        
        @return: No value is returned.
        ''' 
        raise w3afException('Plugin "'+self.getName()+'" is not implementing required method setOptions' )
        
    def getOptions(self):
        '''
        @return: A list of option objects for this plugin.
        '''
        raise w3afException('Plugin "'+self.getName()+'" is not implementing required method getOptions' )

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be 
        runned before the current one.
        '''
        raise w3afException('Plugin is not implementing required method getPluginDeps' )

    def getDesc( self ):
        '''
        @return: A description of the plugin.
        
        >>> b = basePlugin()
        >>> b.__doc__ = 'abc'
        >>> b.getDesc()
        'abc'
        >>> b = basePlugin()
        >>> b.__doc__ = '    abc\t'
        >>> b.getDesc()
        'abc'
        '''
        if self.__doc__ is not None:
            res2 = self.__doc__.replace( '\t' , '' )
            res2 = self.__doc__.replace( '    ' , '' )
            res = ''.join ( [ i for i in res2.split('\n') if i != '' and '@author' not in i ] )
        else:
            res = ''
        return res
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        raise w3afException('Plugin is not implementing required method getLongDesc' )
    
    def printUniq( self, infoObjList, unique ):
        pass


    def _sendMutant(self, mutant, analyze=True, grepResult=True,
                    analyze_callback=None, useCache=True):
        '''
        Sends a mutant to the remote web server.
        '''
        
        self.request_queue.put(mutant)
        
        res = self.response_queue.get()
        
        if analyze:
            if analyze_callback:
                analyze_callback(mutant, res)
            else:
                self._analyzeResult(mutant, res)
        return res

    def _analyzeResult(self,  mutant,  res):
        '''
        Analyze the result of sending the mutant to the remote web server.
        
        @parameter mutant: The mutated request.
        @parameter res: The HTTP response.
        '''
        msg = 'You must override the "_analyzeResult" method of basePlugin if'
        msg += ' you want to use "_sendMutant" with the default callback.'
        raise w3afException( msg )

    def end( self ):
        pass

    def getType( self ):
        return 'plugin'

    def getName( self ):
        return self.__class__.__name__

    def handleUrlError(self, url_error):
        '''
        Handle UrlError exceptions raised when requests are made. Subclasses
        should redefine this method for a more refined behavior.
        
        @param url_error: w3afMustStopOnUrlError exception instance
        @return: True if the exception should be stopped by the caller.
        '''
        pass
