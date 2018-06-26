import users
import menu
import copy

new_server_template = {
    "servername": None,
    "groups": [],
    "action": "add",
    "authuser": None,
    "authkey": None,
    "lastrun": {
        "action": None,
        "date": None,
        "status": None
    }
}

def add_server():

    user,err = users.get_user()
    if not user.exists:
        print('User [{}] does not exist'.format(user.username))
        input()
        return

    server = get_server()
    get_groups(server)

    ret,err = user.add_server(server)
    if not ret:
        print(err)
        input()
        return

    ret,err = user.write_to_db()
    if err:
        print('Error adding server: {}'.format(err))
    else:
        print('Server '+\
            '[{}] was successfully added!'.format(server["servername"]))

    input()


def add_groups():
    user,err = users.get_user()
    if not user.exists:
        print('User [{}] does not exist'.format(user.username))
        input()
        return

    servers = user.get_servers()
    if len(servers) == 0:
        print('User has no servers, nothing to do.')
        input()
        return

    remove_menu = menu.Menu(title="FanoutDB v1.0 (Christian Dechery)",
        message="Add Groups > Select a server below")

    menu_options = []
    for i in range(0, len(servers)):
        s = servers[i]
        def func(s=s):
            print('Current groups: {}'.format(s['groups']))

            get_groups(s)

            user.write_to_db()
            if err:
                print('Error adding group(s): {}'.format(err))
            else:
                print('Group(s) was/were successfully added!')

            input()

        menu_options.append( (servers[i]['servername'],func) )

    menu_options.append( ('[Return]', remove_menu.close) )
    remove_menu.set_options(menu_options)
    remove_menu.open()
    

def get_server():
    server = copy.deepcopy(new_server_template)
    servername = input('  Please provide the server (blank to finish): ')
    if len(servername.strip()) == 0:
        return False

    authuser = input('  Please provide the username to login to the server (blank is Ok): ')
    authkey = input('  Please provide the private key to login to the server (blank is Ok): ')

    server["servername"] = servername
    server["authuser"] = authuser if authuser else None
    server["authkey"] = authkey if authkey else None

    return server

def get_groups(server):
    groups = server['groups']
    while True:
        group = input('    Please provide the group (blank to finish/skip): ')
        if len(group.strip()) == 0:
            break

        if group in groups:
            print('Group [{}] already exists, ignored!'.format(group))
            continue

        groups.append(group)

    if len(groups) > 0:
        server["groups"] = groups

def remove_server():
    user,err = users.get_user()
    if not user.exists:
        print('User [{}] does not exist'.format(user.username))
        input()
        return

    servers = user.get_servers()
    if len(servers) == 0:
        print('User has no servers, nothing to do.')
        input()
        return

    remove_menu = menu.Menu(title="FanoutDB v1.0 (Christian Dechery)",
        message="Remover Server > Select a server below")

    menu_options = []
    for i in range(0, len(servers)):

        if servers[i]['action'] == 'del':
            continue

        s = servers[i]['servername']
        def func(s=s):
            nonlocal menu_options
            user.remove_server(s)

            res, err = user.write_to_db()
            if err:
                print('Error removing server: {}'.format(err))
            else:
                print('Server '+\
                    '[{}] sucessfully marked for deletion.'.format(s))
                menu_options = [x for x in menu_options if x[0]!=s]
                remove_menu.set_options(menu_options)

            input()

        menu_options.append( (servers[i]['servername'],func) )

    menu_options.append( ('[Return]',remove_menu.close) )
    remove_menu.set_options(menu_options)
    remove_menu.open()


def clear_groups():
    user,err = users.get_user()
    if not user.exists:
        print('User [{}] does not exist'.format(user.username))
        input()
        return

    servers = user.get_servers()
    if len(servers) == 0:
        print('User has no servers, nothing to do.')
        input()
        return

    remove_menu = menu.Menu(title="FanoutDB v1.0 (Christian Dechery)",
        message="Clear Groups from Server > Select a server below")

    nogroups = []

    menu_options = []
    for i in range(0, len(servers)):

        if servers[i]['action'] == 'del':
            continue

        s = servers[i]['servername']
        def func(s=s):
            user.set_groups(s, nogroups)

            res, err = user.write_to_db()
            if err:
                print('Error clearing groups: {}'.format(err))
            else:
                print('Groups from server '+\
                    '[{}] sucessfully cleared.'.format(s))

            input()

        menu_options.append( (servers[i]['servername'],func) )

    menu_options.append( ('[Return]',remove_menu.close) )
    remove_menu.set_options(menu_options)
    remove_menu.open()

