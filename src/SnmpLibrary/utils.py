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

def try_int(i):
    try:
        return int(i)
    except ValueError:
        return i

# Interpret a string as OID. The following notations are possible:
#   SNMPv2-MIB::sysDescr.0
#   .1.3.6.1.2.1.1.1.0
#   .iso.org.6.internet.2.1.1.1.0
#   sysDescr.0
def parse_oid(oid):
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

def format_oid(oid):
    return '.' + '.'.join(map(str, oid))

# Interpret a string as an SNMP index. The following values are parsed:
#  '1.2.3.4' -> (1,2,3,4)
#  ('1', '2', '3') -> (1, 2, 3)
#  1 -> (1,)
def parse_idx(idx):
    if isinstance(idx, basestring):
        idx = map(int, idx.split('.'))
    elif isinstance(idx, int):
        idx = idx,
    else:
        # Assume interable list
        idx = map(int, idx)
    return tuple(idx)
