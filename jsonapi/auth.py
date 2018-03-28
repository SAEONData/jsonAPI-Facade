import cherrypy


def authenticate(username, password):
    """
    Authenticate the given user and return their CKAN API key.
    """
    # TODO: authenticate with identity server and get API key from access token
    apikey = cherrypy.config.get('ckan.apikey')
    if not apikey:
        raise cherrypy.HTTPError(403, 'Access denied')
    return apikey
