import logging
import os
import platform

from uaclient import apt
from uaclient.entitlements import base
from uaclient import status
from uaclient import util


class RepoEntitlement(base.UAEntitlement):

    repo_list_file_tmpl = '/etc/apt/sources.list.d/ubuntu-{name}-{series}.list'
    repo_pref_file_tmpl = '/etc/apt/prefrences.d/ubuntu-{name}-{series}'
    repo_pref_origin_tmpl = '/etc/apt/prefrences.d/ubuntu-{name}-{series}'

    # TODO(Get repo_url from Contract service's Entitlements response)
    # https://github.com/CanonicalLtd/ua-service/issues/7
    # Set by subclasses
    repo_url = 'UNSET'
    repo_key_file = 'UNSET'  # keyfile delivered by ubuntu-cloudimage-keyring
    repo_pin_priority = None      # Optional repo pin priority in subclass

    def enable(self):
        """Enable specific entitlement.

        @return: True on success, False otherwise.
        """
        if not self.can_enable():
            return False
        series = platform.dist()[2]
        repo_filename = self.repo_list_file_tmpl.format(
            name=self.name, series=series)
        # TODO(Contract service needs to commit to a token directive)
        access_directives = self.cfg.read_cache(
            'machine-access-%s' % self.name).get('directives', {})
        token = access_directives.get('token')
        if not token:
            logging.debug(
                'No specific entitlement token present. Using machine token'
                ' as %s credentials', self.title)
            token = self.cfg.read_cache('machine-token')['machineSecret']
        ppa_fingerprint = access_directives.get('repo_key')
        if ppa_fingerprint:
            keyring_file = None
        else:
            keyring_file = os.path.join(apt.KEYRINGS_DIR, self.repo_key_file)
        apt.add_auth_apt_repo(
            repo_filename, self.repo_url, token, keyring_file, ppa_fingerprint)
        if self.repo_pin_priority:
            repo_pref_file = self.repo_pref_file_tmpl.format(
                name=self.name, series=series)
            apt.add_repo_pinning(
                repo_pref_file, 'LP-PPA-ubuntu-advantage-fips',
                self.repo_pin_priority)
        if not os.path.exists(apt.APT_METHOD_HTTPS_FILE):
            util.subp(['apt-get', 'install', 'apt-transport-https'])
        if not os.path.exists(apt.CA_CERTIFICATES_FILE):
            util.subp(['apt-get', 'install', 'ca-certificates'])
        util.subp(['apt-get', 'update'])
        print(status.MESSAGE_ENABLED_TMPL.format(title=self.title))
        return True

    def operational_status(self):
        """Return operational status of RepoEntitlement."""
        passed_affordances, details = self.check_affordances()
        if not passed_affordances:
            return status.INAPPLICABLE, details
        apt_policy = util.subp(['apt-cache', 'policy'])
        if ' %s ' % self.repo_url in apt_policy:
            return status.ACTIVE, '%s PPA is active' % self.title
        return status.INACTIVE, '%s PPA is not configured' % self.title