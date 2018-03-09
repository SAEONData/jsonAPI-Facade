import pkg_resources

INDEX_HTML = pkg_resources.resource_string(__name__, '../static/index.html').decode('utf-8')
SAMPLE_METADATA = pkg_resources.resource_string(__name__, '../static/sample_metadata.json').decode('utf-8')
