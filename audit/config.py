from get_local_ip import get_local_ip
from get_net_iface import get_net_iface


class config:
    '''
    This class saves config parameters sent by the user.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        self._cf = {}
        
    def save( self, variableName, value ):
        '''
        This method saves the variableName value to a dict.
        '''
        self._cf[ variableName ] = value
        
    def getData( self, variableName ):
        '''
        @return: Returns the data that was saved to the variableName
        '''
        res = None
        if variableName in self._cf.keys():
            res = self._cf[ variableName ]
        return res
        
cf = config()
# These default configs are taken from miscSettings.py
cf.save('fuzzableCookie', False )
cf.save('fuzzFileContent', True )
cf.save('fuzzFileName', False )
cf.save('fuzzFCExt', 'txt' )
cf.save('fuzzFormComboValues', 'tmb')
cf.save('autoDependencies', True )
cf.save('maxDiscoveryTime', 120 )
cf.save('maxThreads', 15 )
cf.save('fuzzableHeaders', [] )
cf.save('msf_location', '/opt/metasploit3/bin/' )
ifname = get_net_iface()
cf.save('interface', ifname )
local_address = get_local_ip()
if not local_address:
    local_address = '127.0.0.1' #do'h!                
cf.save('localAddress', local_address)
cf.save('demo', False )
cf.save('nonTargets', [] )
cf.save('exportFuzzableRequests', '')
cf.save('targetOS', 'unix')
