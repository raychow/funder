__author__ = 'raych'

from enum import IntEnum
import logging
import json
from urllib import request

from home.models import Fund, NetValue
from funder.settings import WMCLOUD_TOKEN

logger = logging.getLogger(__name__)


class Fetcher:
    DOMAIN = 'https://api.wmcloud.com'
    URL_TEMPLATE = DOMAIN + '/data/v1/api/fund/getFundNav.json?dataDate=%s'
    DATE_FORMAT = '%Y%m%d'
    HEADERS = {'Authorization': 'Bearer %s' % WMCLOUD_TOKEN}

    class ReturnCode(IntEnum):
        success = 1
        no_data_returned = -1
        illegal_request_parameter = -2
        service_suspend = -3
        server_error = -4
        server_busy = -5

    def __init__(self, fetch_date):
        url = self.URL_TEMPLATE % fetch_date.strftime(self.DATE_FORMAT)
        logger.info('Fetch url "%s".' % url)
        req = request.Request(url, headers=self.HEADERS)
        self.response = request.urlopen(req).read()
        self.net_values = self._parse_net_values(self.response.decode('utf-8'))

    def get_response(self):
        return self.response

    def get_net_values(self):
        return self.net_values

    @staticmethod
    def _parse_net_values(json_text):
        result = []
        wmcloud_result = json.loads(json_text)
        code = wmcloud_result['retCode'] if 'retCode' in wmcloud_result \
            else wmcloud_result['code']
        message = wmcloud_result['retMsg'] if 'retMsg' in wmcloud_result \
            else wmcloud_result['message']
        data = wmcloud_result['data'] or [] if 'data' in wmcloud_result else []
        logger.info('Return code %d, message "%s", data length: %d.' % (
            code, message, len(data)
        ))
        if not code == Fetcher.ReturnCode.success:
            raise ValueError('Fetch data from wmcloud failed: %s, %s.' % (
                code, message))
        for net_value in data:
            result.append(Fetcher._parse_net_value(net_value))
        return result

    @staticmethod
    def _parse_net_value(orig_net_value):
        fund = Fund(
            code=orig_net_value['ticker'],
            name=orig_net_value['secShortName'],
        )
        return NetValue(
            date=orig_net_value['endDate'],
            fund=fund,
            nav=orig_net_value['NAV'],
            acc_nav=orig_net_value['ACCUM_NAV'],
            adjust_nav=orig_net_value['ADJUST_NAV'],
        )
