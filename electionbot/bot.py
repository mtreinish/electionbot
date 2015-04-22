# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import argparse
import datetime
import logging
import threading

import daemon
import yaml

from electionbot import mailing_list
from electionbot import wiki

try:
    import daemon.pidlockfile
    pid_file_module = daemon.pidlockfile
except Exception:
    # as of python-daemon 1.6 it doesn't bundle pidlockfile anymore
    # instead it depends on lockfile-0.9.1
    import daemon.pidfile
    pid_file_module = daemon.pidfile


def parse_args():
    parser = argparse.ArgumentParser(
        description='Bot to handle and automate election processes')
    parser.add_argument('-f', '--foreground',
                        action='store_true',
                        help='Run in foreground')
    parser.add_argument('config_file', nargs=1, help="Configuration file")


class MailListWatch(threading.Thread):
    def __init__(self, imap_list, wiki, elections):
        self.log = logging.getLogger('electionbot')
        self.elections = elections
        self.imap_list = imap_list
        self.wiki = wiki

    def process_valid_candidate(self, election, nom_msg, msg_id,
                                confirmed_msg):
        self.wiki.update_page(election, nom_msg)
        self.imap_list.send_reply(msg_id, confirmed_msg)

    def process_invalid_candidate(self, msg_id, reason):
        msg = "Candidacy not confirmed because %s" % reason
        self.imap_list.reply_imap(msg_id, msg)

    def run(self):
        while True:
            try:
                # Process any candidacy emails
                nominations = self.imap_list.get_nominations
                if nominations:
                    for nom in nominations:
                            election_name = nominations[nom]['election']
                            election = self.elections[election_name]
                            cand_name = nominations[nom]['name']
                            cand_email = nominations[nom]['email']
                            validity = election.candidate_check(
                                cand_name, cand_email,
                                nominations[nom]['project'])
                            if validity == 'Valid':
                                msg = election.confirmed_msg
                                self.process_valid_candidate(
                                    election, nominations[nom], nom, msg)
                                break
                            # Candidate email is outside date ranges skip it
                            elif validity == 'Dates':
                                self.imap_list.clear_nomination(nom)
                                continue
                            # Candidacy is generally invalid
                            else:
                                self.process_invalid_candidate(nom, validity)
                                break

                # Process any new elections
                new_elections = self.check_elections_start()
                for election in new_elections:
                    pass

                # Process any ended elections
                end_elections = self.check_elections_stop()
                for election in end_elections:
                    pass
            except Exception:
                self.log.exception("Uncaught exception raised")


def _parse_project_file(project_file):
    project_list = []
    with open(project_file, 'r') as projects:
        for project in yaml.load(projects.read()):
            project_list.append(project)
    return project_list


def _to_datetime(date_str):
    return datetime.datetime.strptime(date_str, "%m-%d-%Y %H:%M")


def _main(args, config):
    elections = config['elections']
    election_wiki = wiki.ElectionWiki(config['wiki']['site'])
    elections_dict = {}
    mail_regexes = {}
    for election in elections:
        name = election['name']
        start = _to_datetime(election['elec_start_date'])
        stop = _to_datetime(election['elec_stop_date'])
        nom_start = _to_datetime(election['nom_start_date'])
        nom_stop = _to_datetime(election['nom_end_date'])
        contributor_cutoff = _to_datetime(election['contributor_cutoff'])
        confirmed_msg = election['confirmed_msg']
        project_dict = election.get('projects')
        mail_regexes[name] = election['email_subject']
        if project_dict:
            projects = []
            for project in project_dict:
                if isinstance(project, dict):
                    projects_from_file = _parse_project_file(
                        project['project_file'])
                    for proj in projects_from_file:
                        projects.append(proj)
                else:
                    projects.append(project)
        else:
            projects = None
        seats = election['seats']
        officials = election['officials']
        wiki.create_page(election['wikipage'], start, stop, officials)
        elections_dict[name] = elections.Election(name, start, stop, nom_start,
                                                  nom_stop, contributor_cutoff,
                                                  confirmed_msg,
                                                  projects=projects,
                                                  seats=seats)
    ml = config['mail']
    ssl = ml.get('ssl')
    imap_list = mailing_list.MailListner(ml['username'], ml['password'], ssl,
                                         config['ml'], mail_regexes,
                                         ml['bot_addr'])
    MailListWatch(imap_list, election_wiki, elections_dict).start()


def main():
    args = parse_args()
    if not args.config_file:
        config_file = open('electionbot.yaml', 'r')
    else:
        config_file = open(args.config_file, 'r')
    pid_fn = '/var/run/electionbot/electionbot.pid'
    config = yaml.load(config_file.read())
    if args.foreground:
        _main(args, config)
    else:
        pid = pid_file_module.TimeoutPIDLockFile(pid_fn, 10)
        with daemon.DaemonContext(pidfile=pid):
            _main(args, config)

if __name__ == 'main':
    main()
