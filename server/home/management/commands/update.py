import argparse
from datetime import datetime
import importlib
import logging

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from funder.settings import FETCHER_PROVIDER
from home.models import Fund, FundFile, NetValue

Fetcher = getattr(importlib.import_module('.fetcher.' + FETCHER_PROVIDER,
                                          'home.management.commands'),
                  'Fetcher')

_provider_address = 'http://stock.finance.qq.com/fund/jzzx/kfs.js?'

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Update net value from fund website'

    def add_arguments(self, parser):
        parser.add_argument('-d', '--date', type=self._date_type,
                            default=self._get_default_date(),
                            help='Set the date to update.')

    def handle(self, *args, **options):
        logger.info("Start updating net value.")
        try:
            update(options['date'])
        except Exception:
            logger.exception('Update net value error.')
        else:
            logger.info('Net value update finished.')

    @staticmethod
    def _date_type(string):
        try:
            return datetime.strptime(string, '%Y%m%d').date()
        except ValueError:
            raise argparse.ArgumentTypeError('Invalid date "%s".' % string)

    @staticmethod
    def _get_default_date():
        now = datetime.now()
        result = now.date()
        # If it is before eight o'clock in the morning,
        # then the fetched data is generated yesterday.
        if now.hour < 8:
            result -= timezone.timedelta(days=1)
        return result


def update(update_date):
    fetcher = Fetcher(update_date)
    _save_fund_file(update_date, fetcher.get_response())
    _update_fund_database(fetcher.get_net_values())


def _save_fund_file(update_date, data):
    fund_file, created = FundFile.objects.update_or_create(
        date=update_date, provider=FETCHER_PROVIDER,
        defaults={'fetch_time': timezone.now()}
    )
    fund_file.file.save(
        name='%s-%s.js' % (update_date.strftime('%Y%m%d'), FETCHER_PROVIDER),
        content=ContentFile(data))


def _update_fund_database(net_values):
    logger.info('Start updating fund database.')
    with transaction.atomic():
        db_net_values = NetValue.objects.all()
        for net_value in net_values:
            fund = net_value.fund
            net_value.fund, created = Fund.objects.update_or_create(
                code=fund.code, defaults={
                    'name': fund.name, 'is_focus': False
                })

            if not db_net_values.filter(
                    date=net_value.date, fund=fund).exists():
                net_value.save()
    logger.info('Fund database update finished.')
