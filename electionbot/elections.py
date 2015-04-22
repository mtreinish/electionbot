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

import datetime


class Election(object):

    def __init__(self, name, start_date, end_date, nom_start, nom_end,
                 contributor_cutoff, confirmed_msg, projects=None, seats=0):
        super(Election, self).__init__()
        self.name = name
        self.start_date = start_date
        self.end_date = end_date
        self.nom_start = nom_start
        self.nom_end = nom_end
        self.projects = projects
        self.contributor_cutoff = contributor_cutoff
        self.confirmed_msg = confirmed_msg
        if projects:
            self.projects = projects
            self.elec_type = 'project'
        elif seats:
            self.seats = int(seats)
            self.elec_type = 'seats'
        else:
            self.elec_type = 'dicator'

    def _is_valid_project(self, project):
        if self.elec_type == 'project':
            return project in self.projects
        else:
            return True

    def check_commit(self, name, email, project=None):
        """Check for a valid commit after the cutoff date from the yaml

        :param str name: The name of the contributor from the email
        :param str email: The email addr for the contributor to check
        :param str project: an optional project name to limit the scope of the
                            query
        """
        pass

    def _is_in_electorate(self, name, email, project=None):
        if self.elec_type == 'project':
            return self.check_commit(name, email, project)
        else:
            return self.check_commit(name, email)

    def candidate_check(self, name, email, project=None):
        now = datetime.datetime.utcnow()
        if self.elec_type == 'project':
            if project:
                if not self._is_valid_project(project):
                    return "%s is not a valid project for election" % project
                if not self._is_in_electorate(name, project):
                    return "you are not a valid member of the electorate"
        if self.nom_start > now or self.nom_end < now:
            return "Dates"
        return "Valid"

    def start_elections(self):
        pass

    def stop_election(self):
        pass
