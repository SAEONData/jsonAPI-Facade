#!/usr/bin/env python
import cherrypy
import json

from jsonapi import INDEX_HTML, SAMPLE_METADATA, ckanclient


class Application:

    @cherrypy.expose
    def index(self):
        return INDEX_HTML.replace('SAMPLE_METADATA', SAMPLE_METADATA)

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def create_metadata(self, server_url, api_key, institution, repository,
                        schema_name, schema_version, metadata_json):

        result = ckanclient.metadata_record_create(
            server_url, api_key, institution, repository,
            schema_name, schema_version, metadata_json)
        return json.dumps(result, indent=4)


if __name__ == "__main__":
    application = Application()
    dispatcher = cherrypy.dispatch.RoutesDispatcher()
    dispatcher.connect(
        name='home',
        route='/',
        controller=application,
        action='index',
        conditions=dict(method=['GET']),
    )
    dispatcher.connect(
        name='create-metadata',
        route='/Institutions/{institution}/{repository}/metadata/jsonCreateMetadataAsJson',
        controller=application,
        action='create_metadata',
        conditions=dict(method=['POST']),
    )
    cherrypy.config.update({'server.socket_port': 9090})
    cherrypy.quickstart(application, config={'/': {'request.dispatch': dispatcher}})
