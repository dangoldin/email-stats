#! /usr/bin/python3

import imaplib, pprint
import email, email.parser, email.utils
import time
import json
import mysql.connector

def get_email_stats(creds):
    imap = imaplib.IMAP4_SSL(creds['imap_host'], creds['imap_port'])
    imap.login(creds['imap_user'], creds['imap_pass'])
    imap.select('Inbox', readonly=True)
    tmp, data = imap.search(None, 'ALL')

    num_emails = len(data[0].split())

    print('Fetched', num_emails , 'emails')

    now = time.time()

    total_age_seconds = 0
    for num in data[0].split():
        tmp, msg_data = imap.fetch(num, '(RFC822)')
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                email_parser = email.parser.BytesFeedParser()
                email_parser.feed(response_part[1])
                msg = email_parser.close()
                # for header in ['subject', 'to', 'from', 'date']:
                #     print('{:^8}: {}'.format(
                #         header.upper(), msg[header]))
                t = email.utils.parsedate(msg['DATE'])
                total_age_seconds += time.mktime(t)
    imap.close()

    return {
        'num_emails': num_emails,
        'avg_age_seconds': (now * num_emails - total_age_seconds) / num_emails
    }

def save_stats(creds, account_name, num_emails, avg_age_seconds):
    mydb = mysql.connector.connect(
        host = creds['host'],
        user = creds['user'],
        passwd = creds['pass'],
        database = creds['database'],
    )
    mycursor = mydb.cursor()

    sql = "INSERT INTO email_stats (account_name, num_emails, avg_age_seconds) VALUES (%s, %s, %s)"
    val = (account_name, num_emails, avg_age_seconds)
    mycursor.execute(sql, val)
    mydb.commit()
    print(mycursor.rowcount, "record inserted.")

if __name__ == '__main__':
    with open('config.json', 'r') as f:
        config = json.load(f)

    for account_name, creds in config['imap'].items():
        email_stats = get_email_stats(creds)
        print('Fetched', email_stats['num_emails'], 'emails in', account_name)
        print('Fetched', email_stats['avg_age_seconds'], 'avg_age_seconds in', account_name)
        save_stats(config['db'], account_name, email_stats['num_emails'], email_stats['avg_age_seconds'])
