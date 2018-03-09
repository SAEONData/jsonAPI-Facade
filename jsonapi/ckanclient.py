import requests


def _call_ckan_api(action, server_url, api_key, **kwargs):
    url = server_url + '/api/action/' + action
    headers = {'Authorization': api_key}
    try:
        response = requests.post(url, json=kwargs, headers=headers)
        return response.json()

    except ValueError:
        return {
            'success': False,
            'error': 'Indecipherable response received from CKAN server'
        }


def metadata_record_create(server_url, api_key,
                           organization, metadata_collection,
                           schema_name, schema_version, content_json):

    return _call_ckan_api('metadata_record_create', server_url, api_key,
                          owner_org=organization,
                          metadata_collection_id=metadata_collection,
                          schema_name=schema_name,
                          schema_version=schema_version,
                          content_json=content_json,
                          content_raw='',
                          content_url='',
                          infrastructures=[])
