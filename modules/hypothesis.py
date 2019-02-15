from dataclasses import dataclass, field
import requests


API_URL = 'https://hypothes.is/api/'
API_REF_URL = 'https://h.readthedocs.io/en/latest/api-reference/'
API_TOKEN = '6879-zbVCq3wU5_xddQb4BR85liZRfhL4Iqz6CmOYN56o2Eo'


@dataclass
class HypothesisApi:
    token: str = API_TOKEN
    url: str = API_URL
    documentation_url: str = API_REF_URL
    groups: dict = field(default_factory=lambda: {})
    previous_searches: list = field(default_factory=lambda: [])
    last_search_results: list = field(default_factory=lambda: [])

    def __post_init__(self):
        self._api = requests.get(self.url).json()['links']
        self.req_headers = {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/json'
        }

    def get_groups(self):
        result = requests.request(
            self._api['groups']['read']['method'],
            self._api['groups']['read']['url'],
            headers=self.req_headers
        ).json()

        self.groups = {g['name']: g for g in result}

        return result

    def search(self, params):
        # Todo:
        # - check that result total == len(rows)

        result = requests.request(
            self._api['search']['method'],
            self._api['search']['url'],
            headers=self.req_headers,
            params=params
        ).json()['rows']

        # save query and result count
        query_ref = (params, len(result))
        self.previous_searches.append(query_ref)
        self.last_search_results = result

        return result

    def search_by_group_name(self, group_name, params=None, refresh=False):
        params = params or {}
        if len(self.groups) == 0 or refresh:
            self.get_groups()
        params['group'] = self.groups[group_name]['id']
        return self.search(params)
