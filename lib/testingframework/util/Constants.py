class Constants(object):

    TestConstants = {
        'SLAVE': 'slave',
        'MASTER': 'captain',
        'ADHOC': 'adhoc',
        'AUTO_PORTS': ' --auto-ports',
        'DFLT_BRNCH': 'current',
        'RUN_LOCAL': 'local',
        'RUN_REMOTE': 'remote',
        'SSH_PORT': '22',
        'SPLUNK_START': 'splunkd start',
        'SPLUNK_STOP': 'splunkd stop',
        'SPLUNK_RESTART': 'splunkd restart',
        'SHP_CONFIG_PEER': '/services/shpool/config/config',
        'SHP_MEMBER_INFO': '/services/shpool/{0}/info',
        'SHP_ARTIFACT':'/services/shpool/{0}/artifacts',
        'APP_INSTALL': '/servicesNS/{0}/{1}/apps/appinstall',
        'SAVED_SEARCH':'/servicesNS/{0}/{1}/saved/searches', #{0} is the user and {1} is the app
        'FIRED_ALERT':'/servicesNS/admin/search/alerts/fired_alerts',
        'FIRED_ALERT_DETAILS':'/servicesNS/admin/search/admin/savedsearch/{0}',
        'SAVED_SEARCH_NAME':'/servicesNS/admin/search/alerts/fired_alerts/{0}',
        'EMAIL_SETTINGS':'/servicesNS/nobody/system/admin/alert_actions/email',
        'SMTP_GMAIL_SERVER':'smtp.gmail.com:{0}',
        'SPLUNK_MAIL_HOST':'mail.sv.splunk.com',
        'PAPER_ORIENTATION':'/servicesNS/admin/search/saved/searches/{0}',
        'PAPER_SIZE':'/servicesNS/admin/search/saved/searches/{0}',
        'APP_LOCAL':'/servicesNS/{0}/{1}/apps/local',
        'ONE_SHOT':'/servicesNS/{0}/{1}/data/inputs/oneshot',
        'ADD_TAG' :'/servicesNS/nobody/search/search/fields/{0}/tags', #0 is fieldname
        'GET_TAG' :'/servicesNS/nodody/search/search/tags',
        'EDIT_EVENTTYPE' :'/servicesNS/nobody/search/saved/eventtypes',
        'GET_EVENTTYPE' :'/servicesNS/nobody/search/saved/eventtypes',
        'EDIT_IFX':'/servicesNS/nobody/search/data/props/extractions',
        'SOURCE_TYPE_RENAME':'/servicesNS/nobody/search/data/props/sourcetype-rename',
        'ADD_DIST_PEER':'/servicesNS/nobody/search/search/distributed/peers'
    }
