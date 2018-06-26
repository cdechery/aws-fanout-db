import json
import servers

# a database connection
conn = None

class User:

    exists = False
    username = None
    updatekey = False

    def __init__(self, username, connection=None):
        self.username = username
        self.servers = []
        self.conn = connection

    def __str__(self):
        userdata = { "username":self.username, 
            "comment": self.comment,
            "updatekey": self.updatekey, 
            "servers": self.servers }

        return json.dumps(userdata, indent=2)

    def load_from_db(self, connection=None):

        self.conn = connection if connection else self.conn
        self.exists = False

        if self.conn == None:
            return (False, 'Database connection not set')
        else:
            try:
                userdata = self.conn.Users.find_one({"username":self.username})

                if userdata != None:
                    self.username = userdata['username']
                    self.servers = userdata['servers']
                    self.updatekey = userdata['updatekey']
                    self.comment = userdata['comment']
                    self.exists = True
            except Exception as e:
                return (False, e)

            return (userdata != None, None)


    def add_server(self, newserver):

        for i in range(0, len(self.servers)):
            if self.servers[i]['servername'] == newserver['servername']:
                return (False, "Server already exists for this user!")

        self.servers.append(newserver)
        return (True, None)

    def remove_server(self, servername):
        found = None 
        for i in range(0, len(self.servers)):
            if self.servers[i]['servername'] == servername:
                found = i

        if found is not None:
            self.servers[found]["action"] = "del"

    def get_servers(self):
        return self.servers

    def get_groups(self, servername):
        for server in self.servers:
            if server[servername] == servername:
                return server['groups']
        else:
            return []

    def set_groups(self, servername, groups):
        found = None 
        for i in range(0, len(self.servers)):
            if self.servers[i]['servername'] == servername:
                found = i

        if found is not None:
            self.servers[found]["groups"] = groups

    def set_comment(self, comment):
        self.comment = comment

    def update_key(self):
        self.updatekey = True

    def write_to_db(self,connection=None):

        self.conn = connection if connection else self.conn

        if self.conn == None:
            return (False, 'Database connection not set')
        else:
            try:
                if not self.exists:
                    self.conn.Users.insert_one({
                            "username": self.username,
                            "servers": self.servers,
                            "updatekey": self.updatekey,
                            "comment": self.comment
                        })
                else:
                    self.conn.Users.update_one({
                            "username": self.username,
                        }, {
                            "$set": {
                                "servers": self.servers,
                                "updatekey": self.updatekey,
                                "comment": self.comment
                            }
                        })
            except Exception as e:
                return (False, e)

            return (True, None)

    def mark_for_deletion(self, servername='All'):
        if servername=='All':
            for server in self.servers:
                server['action'] = 'del'
        else:
            server = self.servers[servername]
            server.action = 'del'


def show_user():
    user,err = get_user()
    if not user.exists:
        print('User [{}] was not found!'.format(user.username))
        input()
    else:
        print(user)

    input()

def get_user():
    while True:
        username = input('Please provide the username: ')
        if len(username.strip())==0:
            continue
        else:
            break

    user = User(username, conn)
    exists,err = user.load_from_db()

    return (user, err)

def add_user():
    global conn

    user,err = get_user()
    if not err and user.exists:
        print('User already exists!')
        input()
        return

    comment = input('Please provide a comment for this user (blank is Ok): ')
    user.set_comment(comment)

    server_added = False
    while True:
        server = servers.get_server()
        if not server:
            break

        servers.get_groups(server)

        ret,err = user.add_server(server)
        if err:
            print(err)
        else:
            server_added = True

    if not server_added:
        print('No servers. User creation aborted.')
    else:
        ret,err = user.write_to_db()
        if err:
            print('Error adding user: {}'.format(err))
        else:
            print('New user [{}] was successfully added!'.format(user.username))

    input()


def delete_user():

    user,err = get_user()
    if err == None:
        if user.exists:
            resp = input('Confirm marked-for-deletion for ' + \
                'user [{}]'.format(user.username) + ' on all its servers? [Y\\N] ')

            if resp.upper() != 'Y':
                return
            else:
                user.mark_for_deletion()
                ret,err = user.write_to_db()
                if err:
                    print('Error updating user: {}'.format(err))
                else:
                    print('User [{}] successfully marked '.format(user.username) + \
                        'for deletion. Now run Fanout to update!')
        else:
            print('User [{}] not found in database'.format(user.username))
    else:
        print('Error loading user [{}]: {}'.format(user.username, err))

    input()

def update_key():

    user,err = get_user()
    if err == None:
        if user.exists:
            resp = input('Confirm Key Update for ' + \
                'user [{}]'.format(user.username) + ' on all its servers? [Y\\N] ')

            if resp.upper() != 'Y':
                return
            else:
                user.update_key()
                ret,err = user.write_to_db()
                if err:
                    print('Error updating user: {}'.format(err))
                else:
                    print('User [{}] successfully marked '.format(user.username) + \
                        'for key update. Now run Fanout!')
        else:
            print('User [{}] not found in database'.format(user.username))
    else:
        print('Error loading user [{}]: {}'.format(user.username, err))

    input()
