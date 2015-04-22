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

import copy
import email
import imaplib
import re
import smtplib

from emailbot import exceptions


class MailListner(object):

    def __init__(self, username, password, host, ssl, mail_list, regexes,
                 bot_addr):
        if ssl:
            self.imap = imaplib.IMAP4_SSL(host)
        else:
            self.imap = imaplib.IMAP4(host)
        self.smtp = smtplib.SMTP()
        self.imap.login(username, password)
        self.mail_list = mail_list
        self.regex = {}
        for regex in regexes:
            self.regex[regex] = re.compile(regexes[regex])
        self.bot_addr = bot_addr
        self.messages = {}

    def reset_regexes(self, new_regexes):
        self.regex = {}
        for regex in new_regexes:
            self.regex[regex] = re.compile(new_regexes[regex])

    def get_new_nominations(self):
        messages_dict = {}
        ret_code, messages = self.imap.search(None, '(UNSEEN)')
        if ret_code == 'OK':
            for num in messages[0].split(' '):
                typ, data = self.imap.fetch(num, '(RFC822)')
                msg = email.message_from_string(data[0][1])
                for regex in self.regex:
                    project = self.regex[regex].match(msg['Subject'])
                    if project:
                        message_id = msg['Message-ID']
                        email_from = email.utils.parseaddr(msg['From'])
                        name = email_from[0]
                        email_addr = email_from[1]
                        messages_dict[message_id] = {
                            'orig_msg': copy.deepcopy(msg),
                            'from': msg['From'],
                            'name': name,
                            'email': email_addr,
                            'project': project,
                            'election': regex,
                        }
        else:
            raise exceptions.IMAPError('Bad return code %s' % ret_code)
        self.messages.update(messages_dict)
        return messages_dict

    def clear_nomination(self, message_id):
        self.message_dict.pop(message_id)

    def send_reply(self, message_id, reply_body):
        original_msg = email.message_from_string(
            self.messages[message_id]['orig_msg'])
        # Construct Reply message
        new_message = email.mime.multipart.MIMEMultipart("mixed")
        body = email.mime.multipart.MIMEMultipart("alternative")
        body.attach(email.mime.text.MIMEText(reply_body, "plain"))
        new_message.attach(body)
        new_message["Message-ID"] = email.utils.make_msgid()
        new_message["In-Reply-To"] = original_msg["Message-ID"]
        new_message["References"] = original_msg["Message-ID"]
        new_message["Subject"] = "Re: " + original_msg["Subject"]
        new_message["To"] = self.mail_list
        new_message["From"] = self.address
        # Send constructed message
        self.smtp(self.address, [new_message['To']], new_message.as_string())
        self.clear_nomination(message_id)
