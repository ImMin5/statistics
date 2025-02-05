import logging
import copy

from spaceone.core.service import *
from spaceone.core import utils

from spaceone.statistics.error import *
from spaceone.statistics.manager.resource_manager import ResourceManager
from spaceone.statistics.manager.schedule_manager import ScheduleManager

_LOGGER = logging.getLogger(__name__)


@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class ScheduleService(BaseService):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resource_mgr: ResourceManager = self.locator.get_manager('ResourceManager')
        self.schedule_mgr: ScheduleManager = self.locator.get_manager('ScheduleManager')

    @transaction(scope="domain_owner:write")
    @check_required(['topic', 'options', 'schedule', 'domain_id'])
    def add(self, params):
        """Add schedule for statistics

        Args:
            params (dict): {
                'topic': 'str',
                'options': 'dict',
                'schedule': 'dict',
                'tags': 'dict',
                'domain_id': 'str'
            }

        Returns:
            schedule_vo
        """

        domain_id = params['domain_id']
        options = copy.deepcopy(params['options'])
        schedule = params['schedule']

        self._check_schedule(schedule)
        self._verify_query_option(options, domain_id)
        return self.schedule_mgr.add_schedule(params)

    @transaction(scope="domain_owner:write")
    @check_required(['schedule_id', 'domain_id'])
    def update(self, params):
        """Update schedule

        Args:
            params (dict): {
                'schedule_id': 'str',
                'schedule': 'dict',
                'tags': 'dict',
                'domain_id': 'str'
            }

        Returns:
            schedule_vo
        """
        schedule = params.get('schedule')

        self._check_schedule(schedule)

        return self.schedule_mgr.update_schedule(params)

    @transaction(scope="domain_owner:write")
    @check_required(['schedule_id', 'domain_id'])
    def enable(self, params):
        """Enable schedule

        Args:
            params (dict): {
                'schedule_id': 'str',
                'domain_id': 'str'
            }

        Returns:
            schedule_vo
        """

        domain_id = params['domain_id']
        schedule_id = params['schedule_id']

        schedule_vo = self.schedule_mgr.get_schedule(schedule_id, domain_id)
        return self.schedule_mgr.update_schedule_by_vo({'state': 'ENABLED'}, schedule_vo)

    @transaction(scope="domain_owner:write")
    @check_required(['schedule_id', 'domain_id'])
    def disable(self, params):
        """Disable schedule

        Args:
            params (dict): {
                'schedule_id': 'str',
                'domain_id': 'str'
            }

        Returns:
            schedule_vo
        """

        domain_id = params['domain_id']
        schedule_id = params['schedule_id']

        schedule_vo = self.schedule_mgr.get_schedule(schedule_id, domain_id)
        return self.schedule_mgr.update_schedule_by_vo({'state': 'DISABLED'}, schedule_vo)

    @transaction(scope="domain_owner:write")
    @check_required(['schedule_id', 'domain_id'])
    def delete(self, params):
        """Delete schedule

        Args:
            params (dict): {
                'schedule_id': 'str',
                'domain_id': 'str'
            }

        Returns:
            None
        """

        self.schedule_mgr.delete_schedule(params['schedule_id'], params['domain_id'])

    @transaction(scope="domain_owner:read")
    @check_required(['schedule_id', 'domain_id'])
    def get(self, params):
        """Get schedule

        Args:
            params (dict): {
                'schedule_id': 'str',
                'domain_id': 'str',
                'only': 'list'
            }

        Returns:
            schedule_vo
        """

        return self.schedule_mgr.get_schedule(params['schedule_id'], params['domain_id'], params.get('only'))

    @transaction(scope="domain_owner:read")
    @check_required(['domain_id'])
    @append_query_filter(['schedule_id', 'topic', 'state', 'data_source_id', 'resource_type', 'domain_id'])
    @append_keyword_filter(['schedule_id', 'topic', 'resource_type'])
    def list(self, params):
        """ List schedules

        Args:
            params (dict): {
                'schedule_id': 'str',
                'topic': 'str',
                'state': 'str',
                'data_source_id': 'str',
                'resource_type': 'str',
                'domain_id': 'str',
                'query': 'dict (spaceone.api.core.v1.Query)'
            }

        Returns:
            schedule_vos (object)
            total_count
        """

        query = params.get('query', {})
        return self.schedule_mgr.list_schedules(query)

    @transaction(scope="domain_owner:read")
    @check_required(['query', 'domain_id'])
    @append_query_filter(['domain_id'])
    @append_keyword_filter(['schedule_id', 'topic', 'resource_type'])
    def stat(self, params):
        """
        Args:
            params (dict): {
                'domain_id': 'str',
                'query': 'dict (spaceone.api.core.v1.StatisticsQuery)'
            }

        Returns:
            values (list) : 'list of statistics data'

        """

        query = params.get('query', {})
        return self.schedule_mgr.stat_schedules(query)

    @transaction()
    @append_query_filter([])
    def list_domains(self, params):
        """ This is used by Scheduler
        Returns:
            results (list)
            total_count (int)
        """
        mgr = self.locator.get_manager('ScheduleManager')
        query = params.get('query', {})
        result = mgr.list_domains(query)
        return result

    @staticmethod
    def _check_schedule(schedule):
        if schedule and len(schedule) > 1:
            raise ERROR_SCHEDULE_OPTION()

    def _verify_query_option(self, options, domain_id):
        aggregate = options.get('aggregate', [])
        page = options.get('page', {})

        self.resource_mgr.stat(aggregate, page, domain_id)
