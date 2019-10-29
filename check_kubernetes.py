#!/usr/bin/env python3
""" kubernetes zabbix monitoring tries to read config from file (host, port, token)
    action [discover, get]
    resource [deployment, service]
    name <NAME_OF_THE_RESOURCE>
    key [e.g. ready, ready_replicas]

    cache results for each <config>__<resource>.json for <config.cache_time> seconds
"""
import os
import sys
import importlib.util
import json

from kubernetes import client, config
from datetime import datetime, date

KNOWN_ACTIONS = ['discover', 'get']
KNOWN_RESOURCES = ['deployments', 'services']


def json_serial(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


class CheckKubernetes:
    def __init__(self, config, config_name, action, resource, resource_name, key):
        self.server = 'https://%s:%s' % (config.host, config.port)

        self.cache_time = config.cache_time
        self.action = action
        self.resource = resource
        self.resource_name = resource_name
        self.key = key
        self.config_name = config_name
        self.cache_filename = 'cache/' + self.config_name + '__' + self.resource + '.json'

        self.api_configuration = client.Configuration()
        self.api_configuration.host = self.server
        self.api_configuration.verify_ssl = config.verify_ssl
        self.api_configuration.api_key = {"authorization": "Bearer " + config.token}

        self.api_client = client.ApiClient(self.api_configuration)

    def do_request(self):
        data = None

        # try to get cache
        if os.path.isfile(self.cache_filename):
            mtime = os.path.getmtime(self.cache_filename)
            now = datetime.now().timestamp()
            if now - mtime <= self.cache_time:
                with open(self.cache_filename, 'r') as fh:
                    data = json.load(fh)

        # if empty -> build cache
        if not data:
            data = self.get_data()
            self.write_cache(data)

        getattr(self, action + '_' + resource)(data=data)

    def get_data(self):
        if self.resource == 'deployments':
            apps_v1 = client.AppsV1Api(self.api_client)
            return apps_v1.list_deployment_for_all_namespaces(watch=False).to_dict()

    def write_cache(self, cached_data):
        with open(self.cache_filename, 'w') as fh:
            fh.write(json.dumps(cached_data, default=json_serial))

    def discover_deployments(self, data):
        name_list = []
        for deployment in data['items']:
            name_list.append(deployment['metadata']['name'])

        print(name_list)

    def get_deployments(self, data):
        for deployment in data['items']:
            if deployment['metadata']['name'] == self.resource_name:
                print(deployment['status'][self.key])

    # core_v1 = client.CoreV1Api(api_client)
    # ret = core_v1.list_pod_for_all_namespaces(watch=False)


if __name__ == '__main__':
    if len(sys.argv) < 6:
        print("kubernetes <CONFIG_NAME> <ACTION> <RESOURCE> <RESOURCE_NAME> <KEY>")
        sys.exit(1)

    config_name = sys.argv[1]
    action = sys.argv[2]
    resource = sys.argv[3]
    resource_name = sys.argv[4]
    key = sys.argv[5]

    try:
        config = importlib.import_module(config_name)
    except ImportError:
        print("config file %s not found. ABORTING!" % config_name)
        sys.exit(1)

    if action not in KNOWN_ACTIONS:
        print("action '%s' not found in known list. ABORTING!")
        sys.exit(1)

    if resource not in KNOWN_RESOURCES:
        print("resource '%s' not found in known list. ABORTING!")
        sys.exit(1)

    CheckKubernetes(config, config_name, action, resource, resource_name, key).do_request()
