#!/usr/bin/env python
import cherrypy
import re

from jsonapi import CONFIG_FILE
from ckanapi import RemoteCKAN


class Application:

    @staticmethod
    def _set_response_headers():
        cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
        cherrypy.response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        cherrypy.response.headers['Access-Control-Allow-Headers'] = 'Content-Type'

    @staticmethod
    def _authenticate(data_dict):
        # TODO: authenticate with identity server and return access token
        username = data_dict.pop('__ac_name', '')
        password = data_dict.pop('__ac_password', '')
        apikey = cherrypy.config.get('ckan.apikey')
        if not apikey:
            raise cherrypy.HTTPError(403, 'Access denied')
        return apikey

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
    def create_metadata(self, institution, repository, **kwargs):
        self._set_response_headers()
        if cherrypy.request.method == 'OPTIONS':
            return

        try:
            data = cherrypy.request.json
        except AttributeError:
            data = kwargs

        ckanurl = cherrypy.config['ckan.url']
        apikey = self._authenticate(data)

        schema_name = data.pop('metadataType', '')
        metadata_json = data.pop('jsonData', '')

        try:
            with RemoteCKAN(ckanurl, apikey=apikey) as ckan:
                ckanresult = ckan.call_action('metadata_record_create', data_dict={
                    'owner_org': institution,
                    'metadata_collection_id': repository,
                    'infrastructures': [],
                    'schema_name': schema_name,
                    'schema_version': '',
                    'content_json': metadata_json,
                    'content_raw': '',
                    'content_url': '',
                })
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

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def list_institutions(self, **kwargs):
        self._set_response_headers()
        if cherrypy.request.method == 'OPTIONS':
            return

        try:
            data = cherrypy.request.json
        except AttributeError:
            data = kwargs

        ckanurl = cherrypy.config['ckan.url']
        apikey = self._authenticate(data)

        types = data.pop('types', '')
        if types != 'Institution':
            return {
                'status': 'failed',
                'msg': "Missing parameter 'types'",
            }

        try:
            with RemoteCKAN(ckanurl, apikey=apikey) as ckan:
                return ckan.call_action('organization_list', data_dict={'all_fields': True})

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
    dispatcher.connect(
        name='list-institutions',
        route='/Institutions/jsonContent',
        controller=application,
        action='list_institutions',
        conditions=dict(method=['OPTIONS', 'POST', 'GET']),
    )
    cherrypy.config.update(CONFIG_FILE)
    cherrypy.tree.mount(application, '/', config={'/': {'request.dispatch': dispatcher}})
    cherrypy.engine.start()
    cherrypy.engine.block()
