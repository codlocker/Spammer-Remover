import httplib2
import os
from apiclient import discovery, errors
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse

    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None


SCOPES = 'https://www.googleapis.com/auth/gmail.modify'
CLIENT_SECRET_FILE = 'client_id.json'
APPLICATION_NAME = 'Gmail API Python Quickstart'


def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def get_inbox_messages(serv, userid="me", query=None):
    inbox_label = 'INBOX'
    results = serv.users().messages().list(userId=userid, labelIds=[inbox_label], q=query).execute()
    if results["messages"]:
        return results["messages"]
    else:
        return None


def get_sender_and_content_for_each_message(msg_id, serv, user_id):
    result = serv.users().messages().get(userId=user_id, id=msg_id).execute()
    payload = result["payload"]
    sender = {}
    for h in payload['headers']:
        if h['name'] == 'From':
            sender["all"] = h['value']
    if sender["all"]:
        if "<" in sender["all"] and ">" in sender["all"]:
            splitter = str(sender["all"]).split(" ")
            sender["name"] = " ".join(splitter[0:-1])
            sender["email"] = str(splitter[-1])[1:-1]
        else:
            sender["email"] = str(sender["all"])
    return sender


def cli_part(data, service):
    count = 0
    for d in data:
        count += 1
        print(count, d["email"])
    select_id = int(input("Enter id of the email address to put in spam:\n"))
    try:
        select_email_id = data[select_id-1]["email"]
        if put_mails_in_spam(select_email_id, service):
            print("Process Successful")
        else:
            print("Process Unsuccessful")
    except IndexError as ie:
        print(str(ie))
        exit(-1)


def put_mails_in_spam(sender, serve):
    modifiers = {
        "addLabelIds": [
            "SPAM", 'UNREAD'
        ],
        "removeLabelIds": [
            "INBOX"
        ]
    }
    query = "from:" + sender
    get_all_mails_from_sender = get_inbox_messages(serve,"me", query)
    for mail in get_all_mails_from_sender:
        try:
            modify_mail = serve.users().messages().modify(userId="me", id=mail["id"], body=modifiers).execute()
            new_str = "Message {} has labels {}".format(mail["id"], modify_mail["labelIds"])
            print(new_str)
        except errors as e:
            print(str(e))
            return False
    return True


if __name__ == '__main__':
    user_name = "me"
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    message_threads = get_inbox_messages(service, user_name)
    list_of_all_senders = []
    if message_threads:
        for threads in message_threads:
            sender = get_sender_and_content_for_each_message(threads['id'], service, user_name)
            if sender not in list_of_all_senders:
                list_of_all_senders.append(sender)
    print(len(list_of_all_senders))
    cli_part(list_of_all_senders, service)
