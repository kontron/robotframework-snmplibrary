# Copyright 2014-2015 Kontron Europe GmbH
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
from itertools import islice, izip
from robot.utils.connectioncache import ConnectionCache

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    from pysnmp.smi import builder
    from pysnmp.entity import engine, config
    from pysnmp.entity.rfc3413.oneliner import cmdgen
    from pyasn1.type import univ
    from pysnmp.proto import rfc1902

from .traps import _Traps
from . import utils
from . import __version__

class _SnmpConnection:

    def __init__(self, authentication, transport_target):
        eng = engine.SnmpEngine()
        self.builder = eng.msgAndPduDsp.mibInstrumController.mibBuilder

        self.cmd_gen = cmdgen.CommandGenerator(eng)
        self.authentication_data = authentication
        self.transport_target = transport_target

        self.prefetched_table = {}

    def close(self):
        # nothing to do atm
        pass

class SnmpLibrary(_Traps):
    AGENT_NAME = 'robotframework agent'
    ROBOT_LIBRARY_VERSION = __version__
    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'

    def __init__(self):
        _Traps.__init__(self)
        self._active_connection = None
        self._cache = ConnectionCache()

    def open_snmp_v2c_connection(self, host, community_string=None, port=161,
            alias=None):
        """Opens a new SNMP v2c connection to the given host.

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

        authentication_data = cmdgen.CommunityData(self.AGENT_NAME,
                                       community_string)
        transport_target = cmdgen.UdpTransportTarget((host, port))

        connection = _SnmpConnection(authentication_data, transport_target)
        self._active_connection = connection

        return self._cache.register(self._active_connection, alias)

    # backwards compatibility, will be removed soon
    open_snmp_connection = open_snmp_v2c_connection

    def open_snmp_v3_connection(self, host, user, password='',
            encryption_password=None, authentication_protocol=None,
            encryption_protocol=None, port=161, alias=None):
        """Opens a new SNMP v3 Connection to the given host.

        If no `port` is given, the default port 161 is used.

        Valid values for `authentication_protocol` are `MD5`, `SHA`, and None.
        Valid values for `encryption_protocol` are `DES`,`3DES`, `AES128`,
        `AES192`, `AES256` and None.

        The optional `alias` is a name for the connection and it can be used
        for switching between connections, similarly as the index. See `Switch
        Connection` for more details about that.
        """

        host = str(host)
        port = int(port)
        user = str(user)
        if password is not None:
            password = str(password)

        if encryption_password is not None:
            encryption_password = str(encryption_password)

        if alias:
            alias = str(alias)

        if authentication_protocol is not None:
            authentication_protocol = authentication_protocol.upper()

        try:
            authentication_protocol = {
                None: cmdgen.usmNoAuthProtocol,
                'MD5': cmdgen.usmHMACMD5AuthProtocol,
                'SHA': cmdgen.usmHMACSHAAuthProtocol
            }[authentication_protocol]
        except KeyError:
            raise RuntimeError('Invalid authentication protocol %s' %
                                                    authentication_protocol)

        if encryption_protocol is not None:
            encryption_protocol = encryption_protocol.upper()

        try:
            encryption_protocol = {
                None: cmdgen.usmNoPrivProtocol,
                'DES': cmdgen.usmDESPrivProtocol,
                '3DES': cmdgen.usm3DESEDEPrivProtocol,
                'AES128': cmdgen.usmAesCfb128Protocol,
                'AES192': cmdgen.usmAesCfb192Protocol,
                'AES256': cmdgen.usmAesCfb256Protocol,
            }[encryption_protocol]
        except KeyError:
            raise RuntimeError('Invalid encryption protocol %s' %
                                                    encryption_protocol)

        authentication_data = cmdgen.UsmUserData(
                                    user,
                                    password,
                                    encryption_password,
                                    authentication_protocol,
                                    encryption_protocol)

        transport_target = cmdgen.UdpTransportTarget((host, port))

        conn = _SnmpConnection(authentication_data, transport_target)
        self._active_connection = conn

        return self._cache.register(self._active_connection, alias)

    def close_snmp_connection(self):
        """Closes the current connection.
        """
        self._active_connection.close()
        self._active_connection = None

    def close_all_snmp_connections(self):
        """Closes all open connections and empties the connection cache.

        After this keyword, new indexes got from the `Open Connection`
        keyword are reset to 1.

        This keyword should be used in a test or suite teardown to
        make sure all connections are closed.
        """

        self._active_connection = self._cache.close_all()
        self._active_connection = None

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

        paths = self._active_connection.builder.getMibPath()
        paths += (path, )
        self._debug('New paths: %s' % ' '.join(paths))
        self._active_connection.builder.setMibPath(*paths)

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
        self._active_connection.builder.loadModules(*names)

    def _get(self, oid, idx=(0,), expect_display_string=False):

        if self._active_connection is None:
            raise RuntimeError('No transport host set')

        idx = utils.parse_idx(idx)
        oid = utils.parse_oid(oid) + idx

        error_indication, error, _, var = \
            self._active_connection.cmd_gen.getCmd(
                self._active_connection.authentication_data,
                self._active_connection.transport_target,
                oid
        )

        if error_indication is not None:
            raise RuntimeError('SNMP GET failed: %s' % error_indication)
        if error != 0:
            raise RuntimeError('SNMP GET failed: %s' % error.prettyPrint())

        oid, obj = var[0]

        if obj == univ.Null(''):
            raise RuntimeError('Object with OID %s not found' %
                    utils.format_oid(oid))

        if expect_display_string:
            if not univ.OctetString().isSuperTypeOf(obj):
                raise RuntimeError('Returned value is not an octetstring')
            value = obj.prettyOut(obj)
        elif univ.OctetString().isSuperTypeOf(obj):
            value = obj.asNumbers()
        else:
            value = obj.prettyOut(obj)

        self._info('OID %s has value %s' % (utils.format_oid(oid), value))

        return value

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
        return self._get(oid, idx)

    def get_display_string(self, oid, idx=(0,)):
        """Does a SNMP GET request for the specified 'oid'.

        For more information and an example see `Get`.
        """
        return self._get(oid, idx, expect_display_string=True)

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

        if self._active_connection is None:
            raise RuntimeError('No transport host set')

        idx = utils.parse_idx(idx)
        oid = utils.parse_oid(oid) + idx
        self._info('Setting OID %s to %s' % (utils.format_oid(oid), value))

        error_indication, error, _, var = \
            self._active_connection.cmd_gen.setCmd(
                self._active_connection.authentication_data,
                self._active_connection.transport_target,
                (oid, value)
        )

        if error_indication is not None:
            raise RuntimeError('SNMP SET failed: %s' % error_indication)
        if error != 0:
            raise RuntimeError('SNMP SET failed: %s' % error.prettyPrint())

    def walk(self, oid):
        """Does a SNMP WALK request and returns the result as OID list.
        """

        if self._active_connection is None:
            raise RuntimeError('No transport host set')

        oid = utils.parse_oid(oid)

        error_indication, error, _, var_bind_table = \
            self._active_connection.cmd_gen.nextCmd(
                self._active_connection.authentication_data,
                self._active_connection.transport_target,
                oid
        )

        if error_indication:
            raise RuntimeError('SNMP WALK failed: %s' % error_indication)
        if error != 0:
            raise RuntimeError('SNMP WALK failed: %s' % error.prettyPrint())

        oids = list()
        for var_bind_table_row in var_bind_table:
            oid, obj = var_bind_table_row[0]
            oids.append((oid, obj.prettyOut(obj)))

        return oids

    def prefetch_oid_table(self, oid):
        """Prefetch the walk result of the given oid.

        The later operation for find_oid_by_value will be done on the stored
        oid list.
        """

        oids = self.walk(oid)
        self._active_connection.prefetched_table[oid] = oids

    def find_oid_by_value(self, oid, value, strip=False):
        """Return the first OID that matches a value in a list
        """

        if self._active_connection.prefetched_table.has_key(oid):
            oids = self._active_connection.prefetched_table[oid]
        else:
            oids = self.walk(oid)

        for oid in oids:
            s = str(oid[1])
            if strip is True:
                s = s.strip()
            if s == str(value):
                return oid[0]

        raise RuntimeError('value=%s not found' % value)

    def find_index(self, index_length, *args):
        """Searches an index in given datasets.

        There are some SNMP tables where the index is an arbitrary one. In this
        case you have to walk through the table and find a row where some
        columns match your values.

        For example consider the following table:

        | =a= | =b= | =c= | =d= | =e= |
        |  2  |  2  |  2  |  3  |  3  |
        |  2  |  3  |  2  |  5  |  6  |

        You want to know the value of d where a is 2 and b is 3.

        | ${a}= | Walk ${oidOfA} | | | | | |
        | ${b}= | Walk ${oidOfB} | | | | | |
        | ${idx}= | Find Index | 1 | ${a} | 2 | ${b} | 3 |
        | ${valueOfD}= | Get | ${oidOfD} | index=${idx} | | | |

        The index_length parameter is the length of the part of the OID which
        denotes the index. Eg. if you have an OID .1.3.6.1.4.1234.1.2.3 and
        index_length is 2, the index would be (2,3).
        """
        if len(args) % 2 != 0:
            raise RuntimeError('Called with an invalid amount of arguments')

        data = islice(args, 0, None, 2)
        match = islice(args, 1, None, 2)

        l = list()
        for e in izip(data, match):
            # match our desired value
            d = filter(lambda x: x[1] == e[1], e[0])

            # we only need the index part of the oid
            d = map(lambda x: (x[0][-int(index_length):]), d)

            # now convert the list of indices to a set
            d = set(d)
            l.append(d)

        # intersect all sets
        s = set(l[0]).intersection(*l[1:])

        if len(s) == 0:
            raise RuntimeError('No index found for the given matches')
        if len(s) > 1:
            raise RuntimeError('Ambiguous match. Found %d matching indices' %
                    len(s))
        return s.pop()

    def get_index_from_oid(self, oid, length=1):
        """Return last part of oid.

        If length is 1 only one element is returned.
        Otherwise a tuple is returened.

        Example:
        |${val}=  | Get Index From OID | 1.3.6.1.2.1.2.2.1.2.10102 | 1 |
        """

        length = int(length)
        oid = utils.parse_oid(oid)

        if length == 1:
            return oid[-1]
        else:
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

