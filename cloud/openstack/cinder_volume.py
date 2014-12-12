#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Harri Hämäläinen <harri.hamalainen@csc.fi>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: cinder_volume
short_description: Create/Delete volumes from OpenStack
description:
   - Create or delete volumes from OpenStack
options:
   size:
     description:
        - Size of volume in GB
     required: true
   login_username:
     description:
        - Login username to authenticate to keystone
     required: true
   login_password:
     description:
        - Password of login user
     required: true
   login_tenant_name:
     description:
        - The tenant name of the login user
     required: true
   auth_url:
     description:
        - The keystone url for authentication
     required: true
   availability_zone:
     description:
        - Availability zone for volume
     required: false
     default: None
   state:
     description:
        - Indicate desired state of the resource
     choices: ['present', 'absent']
     default: present
   volume_id:
     description:
        - ID of the volume
     required: false
     default: None
   volume_name:
     description:
        - Name of the volume
     required: false
     default: None
   display_description:
     description:
        - Description of the volume
     required: false
     default: None
   source_volid:
     description:
        - Create volume from volume id
     required: false
     default: None
   snapshot_id:
     description:
        - Create volume from snapshot id
     required: false
     default: None
   image_ref:
     description:
         - Reference to an image stored in glance
     required: false
     default: None
   volume_type:
     description:
         - Type of the volume
     required: false
     default: None
requirements: ["cinderclient"]

'''

EXAMPLES = '''
# Allocate 10G volume
- cinder_client: login_username=clouduser
                 login_password=passme
                 login_tenant_name=cloudusers
                 auth_url=http://127.0.0.1:35357/v2.0/
                 size=10
                 state=present
'''

try:
    import cinderclient.v1.client as cinderclient
except ImportError:
    print("failed=True msg='cinderclient is required'")


def _get_cinder_client(module, kwargs):
    try:
        client = cinderclient.Client(kwargs.get('login_username'), kwargs.get('login_password'),
                                     kwargs.get('login_tenant_name'), kwargs.get('auth_url'))
    except Exception, e:
        module.fail_json(msg="Error in connecting to Cinder: %s" % e.message)
    return client


def _cinder_volume_present(module, params, client):
    try:
        for volume in client.volumes.list():
            if volume.display_name == params['volume_name']:
                return volume.id
            elif volume.id == params['volume_id']:
                return volume.id
        return None
    except Exception, e:
        module.fail_json(msg="Error in fetching volume list: %s" % e.message)


def _cinder_volume_create(module, params, client):
    try:
        volume = client.volumes.create(params.get('size'),
                                       snapshot_id=params.get('snapshot_id'),
                                       display_name=params.get('volume_name'),
                                       display_description=params.get('display_descriptions'),
                                       volume_type=params.get('volume_type'),
                                       availability_zone=params.get('availability_zone'),
                                       imageRef=params.get('image_ref'))
        return volume.id
    except Exception, e:
        module.fail_json(msg="Error in creating volume: %s" % e.message)


def _cinder_volume_delete(module, params, client):
    try:
        for volume in client.volumes.list():
            volume_id = volume.id
            volume_name = volume.display_name
            if volume_id == params['volume_id'] or volume_name == params['volume_name']:
                client.volumes.delete(volume.id)
    except Exception, e:
        module.fail_json(msg="Error in deleting volume: %s" % e.message)


def main():
    argument_spec = openstack_argument_spec()
    argument_spec.update(dict(
        size                = dict(required=True, type='int'),
        volume_id           = dict(default=None),
        volume_name         = dict(default=None),
        display_description = dict(default=None),
        availability_zone   = dict(default=None),
        image_id            = dict(default=None),
        source_volid        = dict(default=None),
        snapshot_id         = dict(default=None),
        volume_type         = dict(default=None),
        image_ref           = dict(default=None),
        endpoint_type       = dict(default='publicURL', choices=['publicURL', 'internalURL']),
        state               = dict(default='present', choices=['absent', 'present']),
    ))
    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ['image_id', 'source_volid', 'snapshot_id'],
            ['volume_id', 'volume_name']
        ],
    )

    if module.params['state'] == 'present':
        if not module.params['volume_name'] and not module.params['volume_id']:
            module.fail_json(msg="Parameter 'volume_name' or `volume_id` is required if state == 'present'")
        client = _get_cinder_client(module, module.params)
        volume_id = _cinder_volume_present(module, module.params, client)
        if not volume_id:
            volume_id = _cinder_volume_create(module, module.params, client)
            module.exit_json(changed=True, volume_id=volume_id, result="success")
        else:
            module.exit_json(changed=False, volume_id=volume_id, result="success")

    if module.params['state'] == 'absent':
        client = _get_cinder_client(module, module.params)
        volume_id = _cinder_volume_present(module, module.params, client)
        if not volume_id:
            module.exit_json(changed=False, result="not present")
        else:
            _cinder_volume_delete(module, module.params, client)
            module.exit_json(changed=True, result="deleted")


# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
main()
