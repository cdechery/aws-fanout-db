import sys
import shlex
from threading import Timer
from subprocess import Popen
from subprocess import PIPE

import time

create_script = "create_usr.sh"
delete_script = "delete_usr.sh"

script_timeout_secs = 30

time_format = "%Y-%m-%d %H:%M:%S"

# the database connection
conn = None

def run_shell(cmd):

    global script_timeout_secs, testrun

    if testrun:
        print(cmd)
        return ("","",0)

    proc = Popen(shlex.split(cmd), stdout=PIPE,\
        stderr=PIPE)

    kill_proc = lambda p: p.kill()
    timer = Timer(script_timeout_secs, kill_proc, [proc])

    try:
        timer.start()
        stdout,stderr = proc.communicate()
        return (stdout,stderr,proc.returncode)
    finally:
        timer.cancel()

def create_local_user(user, comment, updatekey=False):

    out,err,ret = run_shell('chmod 750 ./create_usr.sh')
    if ret != 0:
        print_log('Error setting permissions for create_usr.sh on local server')
        sys.exit(1)

    if updatekey:
        updatekey = " --updatekey"
    else:
        updatekey = ""

    out,err,ret = run_shell('sudo ./create_usr.sh {} "{}"{}'.format(user, comment, updatekey))

    return ret==0


def delete_local_user(user):

    out,err,ret = run_shell('chmod 750 ./delete_usr.sh')
    if ret != 0:
        print_log('Error setting permissions for delete_usr.sh')
        sys.exit(1)

    out,err,ret = run_shell('sudo ./delete_usr.sh {}'.format(user))

    return ret==0

def create_remote_user(user, comment, server, updatekey):

    global create_script

    servername = server['servername']
    authuser = server['authuser']
    authkey = server['authkey']

    if authuser:
        servername = "{}@{}".format(authuser, servername)

    authkey = "-i {} ".format(authkey) if authkey else ""    

    upload_script = 'scp {}{} {}:~'.format(authkey, create_script, servername)

    out,err,ret = run_shell(upload_script)
    if ret != 0:
        print_log('Error uploading the create_usr.sh to {}'
            .format(servername))
        sys.exit(1)

    out,err,ret = run_shell('ssh {}{} "chmod 750 ~/create_usr.sh"'
        .format(authkey, servername))
    if ret != 0:
        print_log('Error setting permissions for create_usr.sh on {}'
            .format(servername))
        sys.exit(1)

    if updatekey:
        updatekey = " --updatekey"
    else:
        updatekey = ""

    out,err,ret = run_shell('ssh {}{} "sudo ~/create_usr.sh {} \'{}\'{}"'
        .format(authkey, servername, user, comment, updatekey))

    return ret==0

def delete_remote_user(server, user):

    global delete_script

    servername = server['servername']
    authuser = server['authuser']
    authkey = server['authkey']

    if authuser:
        servername = "{}@{}".format(authuser, servername)

    authkey = "-i {} ".format(authkey) if authkey else ""    

    upload_script = 'scp {}{} {}:~'.format(authkey, delete_script, servername)

    out,err,ret = run_shell(upload_script)
    if ret != 0:
        print_log('Error uploading the delete_usr.sh to {}'.format(servername))
        sys.exit(1)

    out,err,ret = run_shell('ssh {}{} "chmod 750 ~/delete_usr.sh"'
        .format(authkey, servername))
    if ret != 0:
        print_log('Error setting permissions for delete_usr.sh on {}'
            .format(servername))
        sys.exit(1)

    out,err,ret = run_shell('ssh {}{} "sudo ~/delete_usr.sh {}"'
        .format(authkey,servername,user))

    return ret == 0


def clear_groups(server, user):

    servername = server['servername']
    authuser = server['authuser']
    authkey = server['authkey']

    if authuser:
        servername = "{}@{}".format(authuser, servername)

    authkey = "-i {} ".format(authkey) if authkey else ""    

    out,err,ret = run_shell('ssh {}{} \'sudo su - '.format(authkey, servername) +\
        '-c "for G in \$(groups {} | cut -d\\" \\" -f4-); '.format(user)+\
        'do gpasswd -d {} \$G; done"\''
        .format(user))

    return ret == 0

def add_user_to_group(server, user, group):

    servername = server['servername']
    authuser = server['authuser']
    authkey = server['authkey']

    if authuser:
        servername = "{}@{}".format(authuser, servername)

    authkey = "-i {} ".format(authkey) if authkey else ""    

    out,err,ret = run_shell('ssh {}{} \'sudo su - '.format(authkey, servername) +\
        '-c "usermod -G {} {}"\''.format(group, user))

    return ret==0


def print_log(line):
    global time_format

    print('{} {}'.format( time.strftime(time_format), line) )


def update_last_run(server,action,status):
    server['lastrun']['action'] = action
    server['lastrun']['status'] = status
    server['lastrun']['date'] = time.strftime(time_format)


def run_fanout(interactive=False):
    global conn, create_script, delete_script

    print_log('Starting fanout')

    print_log('Checking for valid database connection')
    if conn == None:
        print_log('ERROR: Database connection not set')
        input()
        return

    try:
        cursor = conn.Users.find(modifiers={"$snapshot": True})
    except Exception as e:
        print_log('ERROR: There was an error loading the data from the db: {}'.format(e))
        input()
        return

    print_log('All set, let\'s do this')
    for doc in cursor:

        objid = doc['_id']

        user = None

        try:
            user = doc['username']
            updatekey = doc['updatekey']
            comment = doc['comment']

            comment = comment if len(comment) > 0 else user

            servers = doc['servers']
            server_count = len(servers)

            print_log('Processing user: '+user)

            deleted_servers = 0
            for i in range(0, len(servers)):
                if servers[i]['lastrun']['action'] == 'del' and \
                    servers[i]['lastrun']['status'] == 'ok':
                    deleted_servers += 1

            if deleted_servers == server_count:
                print_log(' - all servers for this user were deleted, skipping')
                continue

            if create_local_user(user, comment, updatekey):
                print_log(' - local user created')
            else:
                print_log(' - error creating local user')
                continue

            for server in servers:
                servername = server['servername']
                groups = server['groups']
                action = server['action']

                action_status = None

                if action == 'del':
                    if delete_remote_user(server, user):
                        print_log(' - deleted (or non existent) from server '+servername)
                        action_status = "ok"
                    else:
                        print_log(' - error deleting remote user on '+servername)
                        action_status = "error"
                elif action=='add':
                    if create_remote_user(user, comment, server, updatekey):
                        print_log(' - granted access to server '+servername)
                        action_status = "ok"
                    else:
                        print_log(' - error granting access to server '+servername)
                        action_status = "error"

                    if len(groups) > 0:
                        clear_groups(server, user)
                        for group in groups:
                            if add_user_to_group(server,user,group):
                                print_log('   + group: '+group)
                                action_status = "ok"
                            else:
                                print_log('   - could not add user to group '+group)
                                action_status = "error (groups)"
                    else:
                        print_log('   (no groups)')

                update_last_run(server, action, action_status)
                conn.Users.replace_one({'_id': doc['_id']}, doc)

            if len(servers) == 0:
                print_log(' - user has no servers or was removed from all')
                if delete_local_user(user):
                    print_log(' - deleted (or non existent) local user')
                else:
                    print_log(' - error deleting local user')
                    continue

        except KeyError as e:
            print_log('ERROR: Invalid document, key not found {} [ObjectId: {}]'.format(e, objid))
        except Exception as e:
            print_log('ERROR: Cannot process user [{}]'.format(user)+\
                '\nDetails: {} [ObjectId: {}]'.format(e, objid))
    
    if cursor.count() == 0:
        print_log('No documents to process, nothing to do')

    print_log('All done. Bye.')

    if not interactive:
        input()

debug = False
testrun = False

if __name__ == '__main__':
    from db import DBConnection

    debug = '--debug' in sys.argv
    testrun = '--testrun' in sys.argv

    dbconn = DBConnection()
    conn,result = dbconn.connect()

    if result != "OK":
        print('>> Error while connecting to the database\n>> {}'.format(result))
        exit(1)

    run_fanout(True)
