# Copyright 2014 Kontron Europe GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os.path
import warnings
from robot.utils.connectioncache import ConnectionCache

with warnings.catch_warnings():
    warnings.filterwarnings("ignore",category=DeprecationWarning)
    from pysnmp.smi import builder
    from pysnmp.entity import engine
    from pysnmp.entity.rfc3413.oneliner import cmdgen
    from pyasn1.type import univ
    from pysnmp.proto import rfc1902

class _SnmpConnection:
    def __init__(self, host, port=161, community_string=None):

        self.host = host
        self.port = port
        self.community_string = community_string


def try_int(i):
    try:
        return int(i)
    except ValueError:
        return i

class SnmpLibrary:
    AGENT_NAME = 'robotframework agent'
    def __init__(self):
        e = engine.SnmpEngine()
        self._snmp_engine = e
        self._builder = e.msgAndPduDsp.mibInstrumController.mibBuilder
        self._active_connection = None
        self._cache = ConnectionCache()

    def open_snmp_connection(self, host, community_string=None, port=161,
            alias=None):
        """Opens a new Snmp Connection to the given host.

        Set `community_string` that is used for this connection.

        If no `port` is given, the default port 161 is used.

        The optional `alias` is a name for the connection and it can be used
        for switching between connections, similarly as the index. See `Switch
        Connection` for more details about that.
        """

        host = str(host)
        port = int(port)

        if alias:
            alias = str(alias)

        conn = _SnmpConnection(host, port, community_string)
        self._active_connection = conn

        return self._cache.register(self._active_connection, alias)

    def close_snmp_connection(self):
        """Closes the current connection.
        """
        pass

    def close_all_snmp_connections(self):
        """Closes all open connections and empties the connection cache.

        After this keyword, new indexes got from the `Open Connection`
        keyword are reset to 1.

        This keyword should be used in a test or suite teardown to
        make sure all connections are closed.
        """

        self._active_connection = self._cache.close_all()

    def switch_snmp_connection(self, index_or_alias):
        """Switches between active connections using an index or alias.

        The index is got from `Open Connection` keyword, and an alias
        can be given to it.

        Returns the index of previously active connection.
        """

        old_index = self._cache.current_index
        self._active_connection = self._cache.switch(index_or_alias)
        return old_index

    def add_mib_search_path(self, path):
        """Adds a path to the MIB search path.

        Example:
        | Add MIB Search Path | /usr/share/mibs/ |
        """

        self._info('Adding MIB path %s' % (path,))
        if not os.path.exists(path):
            raise RuntimeError('Path "%s" does not exist' % path)

        paths = self._builder.getMibPath()
        paths += (path, )
        self._debug('New paths: %s' % ' '.join(paths))
        self._builder.setMibPath(*paths)

    def preload_mibs(self, *names):
        """Preloads MIBs.

        Preloading MIBs can be useful in cases where the `Get`- or
        `Set`-keyword should be executed as fast as possible.

        `names` can either be a list of MIB names or can be empty in which case
        all available MIBs are preloaded.

        This keyword should be used within the test setup.

        Note: Preloading all MIBs take a long time.
        """
        if len(names):
            self._info('Preloading MIBs %s' % ' '.join(list(names)))
        else:
            self._info('Preloading all available MIBs')
        self._builder.loadModules(*names)

    def _parse_oid(self, oid):
        # The following notations are possible:
        #   SNMPv2-MIB::sysDescr.0
        #   .1.3.6.1.2.1.1.1.0
        #   .iso.org.6.internet.2.1.1.1.0
        #   sysDescr.0
        if not isinstance(oid, basestring):
            return oid
        elif '::' in oid:
            mib, sym = oid.split('::', 1)
            oid = None
        elif oid.startswith('.'):
            oid = map(try_int, oid[1:].split('.'))
            oid = tuple(oid)
        else:
            mib = ''
            sym = oid
            oid = None

        if oid is None:
            sym, suffixes = sym.split('.', 1)
            suffixes = suffixes.split('.')
            suffixes = map(try_int, suffixes)
            suffixes = tuple(suffixes)
            oid = ((mib, sym),) + suffixes

        return oid

    def get(self, oid, idx=(0,)):
        """Does a SNMP GET request for the specified 'oid'.

        'idx' can be specified as tuple or as string.

        Examples:
        | ${value}=  | Get | SNMPv2-MIB::sysDescr.0 |
        | ${value}=  | Get | .1.3.6.1.2.1.1.1.0 |
        | ${value}=  | Get | .iso.org.6.internet.2.1.1.1.0 |
        | ${value}=  | Get | sysDescr.0 |
        | ${value}=  | Get | sysDescr.0 | 6
        """

        host = self._active_connection.host
        port = self._active_connection.port
        community = self._active_connection.community_string

        if not host:
            raise RuntimeError('No host set')

        if  isinstance(idx,basestring):
            idx = (int(idx),)
        else:
            idx = tuple(idx)

        oid = self._parse_oid(oid) + idx
        self._info('Fetching OID %s' % (oid,))

        error_indication, error, _, var = \
            cmdgen.CommandGenerator(self._snmp_engine).getCmd(
                cmdgen.CommunityData(self.AGENT_NAME, community),
                cmdgen.UdpTransportTarget((host, port)),
                oid
        )

        if error_indication is not None:
            raise RuntimeError('SNMP GET failed: %s' % error_indication)
        if error != 0:
            raise RuntimeError('SNMP GET failed: %s' % error.prettyPrint())

        oid, obj = var[0]

        if obj == univ.Null(''):
            raise RuntimeError('Object with OID ".%s" not found' %
                    '.'.join(map(str, oid)))

        value = obj.prettyOut(obj)
        self._info('... was %s' % (value,))

        return value

    def set(self, oid, value, idx=(0,)):
        """Does a SNMP SET request.

        See `Get` for more information on possible OID notations.

        Automatic converting to the SNMP type expected by the remote system is
        only supported for OIDs for which there is a MIB describing it. If you
        want to use an OID which is not described by a MIB, you'll have to use
        the `Set XXX`-keyword or `Convert To XXX`-keyword.

        Example:
        | Set | SNMPv2::sysDescr.0 | New System Description |
        """

        host = self._active_connection.host
        port = self._active_connection.port
        community = self._active_connection.community_string

        if not host:
            raise RuntimeError('No host set')

        if  isinstance(idx, basestring):
            idx = (int(idx),)
        else:
            idx = tuple(idx)

        oid = self._parse_oid(oid) + idx
        self._info('Setting OID %s to %s' % (oid, value))

        #from pysnmp.proto import rfc1902
        #value = rfc1902.OctetString(value)

        error_indication, error, _, var = \
            cmdgen.CommandGenerator(self._snmp_engine).setCmd(
                cmdgen.CommunityData(self.AGENT_NAME, community),
                cmdgen.UdpTransportTarget((host, port)),
                (oid, value)
        )

        if error_indication is not None:
            raise RuntimeError('SNMP SET failed: %s' % error_indication)
        if error != 0:
            raise RuntimeError('SNMP SET failed: %s' % error.prettyPrint())

    def walk(self, oid):
        """Does a SNMP WALK request and returns the result as OID list.
        """

        host = self._active_connection.host
        port = self._active_connection.port
        community = self._active_connection.community_string

        if not host:
            raise RuntimeError('No host set')

        oid =  self._parse_oid(oid)

        errorIndication, error, _, varBindTable = \
            cmdgen.CommandGenerator(self._snmp_engine).nextCmd (
                cmdgen.CommunityData(self.AGENT_NAME, community),
                cmdgen.UdpTransportTarget((host, port)),
                oid
        )

        if errorIndication:
            raise RuntimeError('SNMP WALK failed: %s' % errorIndication)
        if error != 0:
            raise RuntimeError('SNMP WALK failed: %s' % error.prettyPrint())

        oids = list()
        for varBindTableRow in varBindTable:
            oid, obj = varBindTableRow[0]
            oids.append((oid.prettyOut(oid), obj.prettyOut(obj)))

        return oids

    def find_oid_by_value(self, oid, value):
        """Return the first OID that matches a value in a list
        """

        oids = self.walk(oid)

        for o in oids:
            print o
            if str(o[1]) == str(value):
                return o[0]

        raise RuntimeError('value=%s not found' % value)

    def get_index_from_oid(self, oid, length=1):
        """Return last part of oid.
        If length is 1 only one element is returned.
        Otherwise a tuple is returened.

        Example:
        |${val}=  | Get Index From OID | 1.3.6.1.2.1.2.2.1.2.10102 | 1 |
        """

        length = int(length)

        oid = self._parse_oid(oid)
        return oid[-length:]

    def convert_to_octetstring(self, value):
        """Converts a value to a SNMP OctetString object."""
        return rfc1902.OctetString(value)

    def convert_to_integer(self, value):
        """Converts a value to a SNMP Integer object."""
        return rfc1902.Integer(value)

    def convert_to_integer32(self, value):
        """Converts a value to a SNMP Integer32 object."""
        return rfc1902.Integer32(value)

    def convert_to_counter32(self, value):
        """Converts a value to a SNMP Counter32 object."""
        return rfc1902.Counter32(value)

    def convert_to_counter64(self, value):
        """Converts a value to a SNMP Counter64 object."""
        return rfc1902.Counter64(value)

    def convert_to_gauge32(self, value):
        """Converts a value to a SNMP Gauge32 object."""
        return rfc1902.Gauge32(value)

    def convert_to_unsigned32(self, value):
        """Converts a value to a SNMP Unsigned32 object."""
        return rfc1902.Unsigned32(value)

    def convert_to_timeticks(self, value):
        """Converts a value to a SNMP TimeTicks object."""
        return rfc1902.TimeTicks(value)

    def set_octetstring(self, oid, value, idx=(0,)):
        """Does a SNMP SET request after converting the value to an
        OctetString SNMP Object.

        This is a convenient keyword, it does the same as a `Convert To
        OctetString` followed by a `Set`.
        """

        value = self.convert_to_octetstring(value)
        self.set(oid, value, idx)

    def set_integer(self, oid, value, idx=(0,)):
        """Does a SNMP SET request after converting the value to an
        Integer SNMP Object.

        This is a convenient keyword, it does the same as a `Convert To
        Integer` followed by a `Set`.
        """

        value = self.convert_to_integer(value)
        self.set(oid, value, idx)

    def set_integer32(self, oid, value, idx=(0,)):
        """Does a SNMP SET request after converting the value to an
        Integer32 SNMP Object.

        See also `Set Integer`.
        """

        value = self.convert_to_integer32(value)
        self.set(oid, value, idx)

    def set_counter32(self, oid, value, idx=(0,)):
        """Does a SNMP SET request after converting the value to a
        Counter32 SNMP Object.

        See also `Set Integer`.
        """

        value = self.convert_to_counter32(value)
        self.set(oid, value, idx)

    def set_counter64(self, oid, value, idx=(0,)):
        """Does a SNMP SET request after converting the value to a
        Counter64 SNMP Object.

        See also `Set Integer`.
        """

        value = self.convert_to_counter64(value)
        self.set(oid, value, idx)

    def set_gauge32(self, oid, value, idx=(0,)):
        """Does a SNMP SET request after converting the value to a
        Gauge32 SNMP Object.

        See also `Set Integer`.
        """

        value = self.convert_to_gauge32(value)
        self.set(oid, value, idx)

    def set_unsigned32(self, oid, value, idx=(0,)):
        """Does a SNMP SET request after converting the value to a
        Unsigned32 SNMP Object.

        See also `Set Integer`.
        """

        value = self.convert_to_unsigned32(value)
        self.set(oid, value, idx)

    def set_timeticks(self, oid, value, idx=(0,)):
        """Does a SNMP SET request after converting the value to a
        TimeTicks SNMP Object.

        See also `Set Integer`.
        """

        value = self.convert_to_timeticks(value)
        self.set(oid, value, idx)

    def _warn(self, msg):
        self._log(msg, 'WARN')

    def _info(self, msg):
        self._log(msg, 'INFO')

    def _debug(self, msg):
        self._log(msg, 'DEBUG')

    def _log(self, msg, level=None):
        self._is_valid_log_level(level, raise_if_invalid=True)
        msg = msg.strip()
        if level is None:
            level = self._default_log_level
        if msg != '':
            print '*%s* %s' % (level.upper(), msg)

    def _is_valid_log_level(self, level, raise_if_invalid=False):
        if level is None:
            return True
        if isinstance(level, basestring) and \
                level.upper() in ['TRACE', 'DEBUG', 'INFO', 'WARN', 'HTML']:
            return True
        if not raise_if_invalid:
            return False
        raise RuntimeError("Invalid log level '%s'" % level)


if __name__ == "__main__":
    s = SnmpLibrary()
    s.set_host('10.0.113.254')
    s.set_community_string('private')

    #s.preload_mibs('SNMPv2-MIB')
    #s.load_mibs()
    #print s.get((1,3,6,1,2,1,1,1,0))
    #print s.get((('SNMPv2-MIB', 'sysDescr'), 0))
    #print s.get(('SNMPv2-MIB', ''))
    #print s.get('SNMPv2-MIB::sysDescr.0')
    #print s.get('sysDescr.0')
    #print s.get('.1.3.6.1.2.1.1.1.1')
    #s.set('.iso.org.6.internet.2.1.1.1.0', 'test')
    #print s.get('.1.3.6.1.2.1.1.1.0')
    #s.set('.1.3.6.1.2.1.1.6.0', 'Test')
    #print s.get('SNMPv2-MIB::sysLocation.0')
    #print s.get('KEX-MCG-MIB::clkRefValid.1.1')
    #print s.get('.1.3.6.1.4.1.15000.5.2.1.0')
    #s.set('.1.3.6.1.4.1.15000.5.2.1.0', Gauge32(200))
    #s.set_gauge32('.1.3.6.1.4.1.15000.5.2.1.0', '200')
    #print s.get('.1.3.6.1.4.1.15000.5.2.1.0')
    print s.walk('.1.3.6.1.4.1.9.5.1.4.1.1')

