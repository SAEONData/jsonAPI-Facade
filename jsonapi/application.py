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

    @staticmethod
    def _generate_name(text):
        return re.sub('[^a-z0-9_\-]+', '-', text.lower())

    @cherrypy.expose
    @cherrypy.tools.json_in(force=False)  # allow content types other than 'application/json'
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

        metadata_standard = data.pop('metadataType', '')
        metadata_json = data.pop('jsonData', '')

        # For compatibility with the legacy portal:
        # Requests from the portal to create metadata always have institution==repository.
        # But in CKAN, repositories cannot have the same name as their owning institutions,
        # as both are Group type objects. We assume that for an institution and repository
        # named 'foo' in Plone, the corresponding repository (metadata collection) in CKAN
        # would be named 'foo-repository'.
        if institution == repository:
            repository += '-repository'

        try:
            with RemoteCKAN(ckanurl, apikey=apikey) as ckan:
                ckanresult = ckan.call_action('metadata_record_create', data_dict={
                    'owner_org': institution,
                    'metadata_collection_id': repository,
                    'infrastructures': [],
                    'metadata_standard_id': metadata_standard,
                    'metadata_json': metadata_json,
                    'metadata_raw': '',
                    'metadata_url': '',
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
    def get_metadata(self, institution, repository, **kwargs):
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
        if types != 'Metadata':
            return {
                'status': 'failed',
                'msg': 'Expecting param types=Metadata',
            }

        # For compatibility with the legacy portal (see comment in create_metadata)
        if institution == repository:
            repository += '-repository'

        try:
            with RemoteCKAN(ckanurl, apikey=apikey) as ckan:
                ckanresult = ckan.call_action('metadata_record_list', data_dict={
                    'owner_org': institution,
                    'metadata_collection_id': repository,
                    'all_fields': True,
                })

            for org_dict in ckanresult:
                org_dict['context_path'] = cherrypy.request.wsgi_environ['wsgi.url_scheme'] + '://' + \
                                           cherrypy.request.wsgi_environ['HTTP_HOST'] + \
                                           '/Institutions/' + org_dict['name']
            return ckanresult

        except Exception as e:
            return {
                'status': 'failed',
                'msg': self._extract_error(e),
            }

    @cherrypy.expose
    @cherrypy.tools.json_in(force=False)  # allow content types other than 'application/json'
    @cherrypy.tools.json_out()
    def create_institution(self, **kwargs):
        self._set_response_headers()
        if cherrypy.request.method == 'OPTIONS':
            return

        try:
            data = cherrypy.request.json
        except AttributeError:
            data = kwargs

        ckanurl = cherrypy.config['ckan.url']
        apikey = self._authenticate(data)

        title = data.pop('title', '')
        name = self._generate_name(title)

        try:
            with RemoteCKAN(ckanurl, apikey=apikey) as ckan:
                ckanresult = ckan.call_action('organization_create', data_dict={
                    'name': name,
                    'title': title,
                })

                # create a default repository (in the legacy JSON API, this would be named
                # identically to the institution; see comment in create_metadata)
                try:
                    ckan.call_action('metadata_collection_create', data_dict={
                        'name': name + '-repository',
                        'title': title + ' Repository',
                        'organization_id': ckanresult['id'],
                    })
                except:
                    try:
                        ckan.call_action('organization_delete', data_dict={'id': ckanresult['id']})
                    except:
                        pass
                    raise

            return {
                'status': 'success',
                'url': ckanurl + '/api/action/organization_show?id=' + ckanresult['id'],
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
                'msg': 'Expecting param types=Institution',
            }

        try:
            with RemoteCKAN(ckanurl, apikey=apikey) as ckan:
                ckanresult = ckan.call_action('organization_list', data_dict={'all_fields': True})

            for org_dict in ckanresult:
                org_dict['context_path'] = cherrypy.request.wsgi_environ['wsgi.url_scheme'] + '://' + \
                                           cherrypy.request.wsgi_environ['HTTP_HOST'] + \
                                           '/Institutions/' + org_dict['name']
            return ckanresult

        except Exception as e:
            return {
                'status': 'failed',
                'msg': self._extract_error(e),
            }

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def list_users(self, **kwargs):
        self._set_response_headers()
        if cherrypy.request.method == 'OPTIONS':
            return

        try:
            data = cherrypy.request.json
        except AttributeError:
            data = kwargs

        ckanurl = cherrypy.config['ckan.url']
        apikey = self._authenticate(data)

        users = data.pop('user_id', [])
        if users:
            users = users.split('|')

        try:
            with RemoteCKAN(ckanurl, apikey=apikey) as ckan:
                ckanresult = ckan.call_action('user_list', data_dict={'all_fields': True})
                if users:
                    ckanresult = [user_dict for user_dict in ckanresult
                                  if user_dict['name'] in users]
                return ckanresult

        except Exception as e:
            return {
                'status': 'failed',
                'msg': self._extract_error(e),
            }

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def get_user(self, username, **kwargs):
        self._set_response_headers()
        if cherrypy.request.method == 'OPTIONS':
            return

        try:
            data = cherrypy.request.json
        except AttributeError:
            data = kwargs

        ckanurl = cherrypy.config['ckan.url']
        apikey = self._authenticate(data)

        try:
            with RemoteCKAN(ckanurl, apikey=apikey) as ckan:
                return ckan.call_action('user_show', data_dict={'id': username})

        except Exception as e:
            return {
                'status': 'failed',
                'msg': self._extract_error(e),
            }

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def json_content_generic(self, **kwargs):
        self._set_response_headers()
        if cherrypy.request.method == 'OPTIONS':
            return

        try:
            data = cherrypy.request.json
        except AttributeError:
            data = kwargs

        if data.get('types') == 'Institution':
            return self.list_institutions(**kwargs)


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
        name='get-metadata',
        route='/Institutions/{institution}/{repository}/metadata/jsonContent',
        controller=application,
        action='get_metadata',
        conditions=dict(method=['OPTIONS', 'POST', 'GET']),
    )
    dispatcher.connect(
        name='create-institution',
        route='/Institutions/jsonCreateInstitution',
        controller=application,
        action='create_institution',
        conditions=dict(method=['OPTIONS', 'POST']),
    )
    dispatcher.connect(
        name='list-institutions',
        route='/Institutions/jsonContent',
        controller=application,
        action='list_institutions',
        conditions=dict(method=['OPTIONS', 'POST', 'GET']),
    )
    dispatcher.connect(
        name='list-users',
        route='/jsonUser',
        controller=application,
        action='list_users',
        conditions=dict(method=['OPTIONS', 'POST', 'GET']),
    )
    dispatcher.connect(
        name='get-user',
        route='/Members/{username}/jsonContent',
        controller=application,
        action='get_user',
        conditions=dict(method=['OPTIONS', 'POST', 'GET']),
    )
    dispatcher.connect(
        name='json-content-generic',
        route='/jsonContent',
        controller=application,
        action='json_content_generic',
        conditions=dict(method=['OPTIONS', 'POST', 'GET']),
    )
    cherrypy.config.update(CONFIG_FILE)
    cherrypy.tree.mount(application, '/', config={'/': {'request.dispatch': dispatcher}})
    cherrypy.engine.start()
    cherrypy.engine.block()
