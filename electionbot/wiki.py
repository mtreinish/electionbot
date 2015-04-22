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

import pywikibot
import yaml


def get_projects_list(yaml_file):
    raw_file = open(yaml_file, 'r')
    projects_list = []
    projects_dict = yaml.load(raw_file.read())
    for project in projects_dict:
        projects_list.append({'name': project, 'service': project['service']})


class ElectionWiki(object):

    def __init__(self, site):
        self.site = pywikibot.Site('en', site)
        self.pages = []

    def create_page(self, name, start, end, officials, elec_start, elec_end,
                    projects_file=None, slots=0):
        page = pywikibot.page(self.site, self.name)
        page_text = \
"""
=== %s ===

=== Officials ===
""" % name
        for official in self.officials:
            page_text += "* %s\n" % official
        page_text += \
"""

=== Election System ===
Elections will be held using CIVS and a Condorcet algorithm (Schulze/Beatpath/CSSD variant). Any tie will be broken using [[Governance/TieBreaking]].

=== Timeline ===
"""
        page_text += "* %s - %s\n" % (start, end, elec_start, elec_end)
        if projects_file:
            page_text += \
"""

=== Elected Positions ===
Every [http://governance.openstack.org/reference/projects official project team] must elect a PTL. PTLs are elected for 6 months:
"""
            projects = get_projects_list(projects_file)
            for project in projects:
                page_text += ("* %s (%s) - one position\n" % (
                    project['service'], project['name']))
        page_text += \
"""

=== Electorate ===
Except otherwise-noted in the project team description, the electorate for a
given PTL election are the Foundation individual members that are also
committers for one of the team's repositories over the Juno-Kilo timeframe
(April 9, 2014 06:00 UTC to April 9, 2015 05:59 UTC).

The electorate is requested to confirm their email address in gerrit, review.
openstack.org > Settings > Contact Information > Preferred Email, prior to
%s so that the emailed ballots are mailed to the correct email address.

There is a resolution to the governance repo that all of the electorate is
expected to follow:
http://governance.openstack.org/resolutions/20140711-election-activities.html
""" % elec_start

        self.pages.append(page_text)
        page.text = page_text
        page.save("Creating Election Wiki")
