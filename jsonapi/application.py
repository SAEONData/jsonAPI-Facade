#!/usr/bin/env python
import cherrypy
import json

from jsonapi import CONFIG_FILE, auth
from ckanapi import RemoteCKAN


class Application:

    @staticmethod
    def _call_ckan(action, apikey, **kwargs):
        url = cherrypy.config['ckan.url']
        get_only = action.endswith(('_list', '_show'))

        with RemoteCKAN(url, apikey=apikey, get_only=get_only) as ckan:
            try:
                result = ckan.call_action(action, data_dict=kwargs)
            except Exception as e:
                result = e.args[0] if len(e.args) == 1 else e.args

        return json.dumps(result, indent=4)

    @cherrypy.expose
    def create_metadata(self, __ac_name, __ac_password, institution, repository,
                        schema_name, schema_version, metadata_json):
        apikey = auth.authenticate(__ac_name, __ac_password)
        return self._call_ckan('metadata_record_create', apikey,
                               owner_org=institution,
                               metadata_collection_id=repository,
                               infrastructures=[],
                               schema_name=schema_name,
                               schema_version=schema_version,
                               content_json=metadata_json,
                               content_raw='',
                               content_url='')


if __name__ == "__main__":
    application = Application()
    dispatcher = cherrypy.dispatch.RoutesDispatcher()
    dispatcher.connect(
        name='create-metadata',
        route='/Institutions/{institution}/{repository}/metadata/jsonCreateMetadataAsJson',
        controller=application,
        action='create_metadata',
        conditions=dict(method=['POST']),
    )
    cherrypy.config.update(CONFIG_FILE)
    cherrypy.quickstart(application, config={'/': {'request.dispatch': dispatcher}})
