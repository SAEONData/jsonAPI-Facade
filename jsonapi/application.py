#!/usr/bin/env python
import cherrypy
import re

from jsonapi import CONFIG_FILE, auth
from ckanapi import RemoteCKAN


class Application:

    @staticmethod
    def _extract_error(e):
        """
        Get the structured error out of the exception, if available; otherwise, get the
        exception message and remove any HTML error document that might have been returned
        by CKAN in case of an internal error.
        """
        if len(e.args) > 0 and type(e.args[0]) is not str:
            return e.args[0]
        else:
            return re.sub(r"'<!DOCTYPE html .*</html>.*'", "'Server Error'", str(e))

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def create_metadata(self, institution, repository):
        cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
        cherrypy.response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        cherrypy.response.headers['Access-Control-Allow-Headers'] = 'Content-Type'

        if cherrypy.request.method == 'POST':
            data = cherrypy.request.json
            username = data.pop('__ac_name', '')
            password = data.pop('__ac_password', '')
            schema_name = data.pop('metadataType', '')
            metadata_json = data.pop('jsonData', '')

            ckanurl = cherrypy.config['ckan.url']
            apikey = auth.authenticate(username, password)
            data_dict = {
                'owner_org': institution,
                'metadata_collection_id': repository,
                'infrastructures': [],
                'schema_name': schema_name,
                'schema_version': '',
                'content_json': metadata_json,
                'content_raw': '',
                'content_url': '',
            }
            try:
                with RemoteCKAN(ckanurl, apikey=apikey) as ckan:
                    ckanresult = ckan.call_action('metadata_record_create', data_dict)
                return {
                    'status': 'success',
                    'token': ckanresult['name'],
                    'url': ckanurl + '/api/action/metadata_record_show?id=' + ckanresult['id'],
                    'uid': ckanresult['id'],
                    'doi': '',
                }
            except Exception as e:
                return {
                    'status': 'failed',
                    'msg': self._extract_error(e),
                }


if __name__ == "__main__":
    application = Application()
    dispatcher = cherrypy.dispatch.RoutesDispatcher()
    dispatcher.connect(
        name='create-metadata',
        route='/Institutions/{institution}/{repository}/metadata/jsonCreateMetadataAsJson',
        controller=application,
        action='create_metadata',
        conditions=dict(method=['OPTIONS', 'POST']),
    )
    cherrypy.config.update(CONFIG_FILE)
    cherrypy.tree.mount(application, '/', config={'/': {'request.dispatch': dispatcher}})
    cherrypy.engine.start()
    cherrypy.engine.block()
