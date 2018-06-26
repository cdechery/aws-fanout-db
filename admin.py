from db import DBConnection
import menu
import fanout
import users
import servers

dbconn = DBConnection()
conn,result = dbconn.connect()

if result != "OK":
    print('>> Error while connecting to the database\n>> {}'.format(result))
    exit(1)

def import_users():
    print('Under construction')
    input()

# setting the global vars so the imported functions can work
users.conn = conn
fanout.conn = conn

main_menu = menu.Menu(title="FanoutDB v1.0 (Christian Dechery)",
    message="> Select an option below")

update_menu = menu.Menu(title="FanoutDB v1.0 (Christian Dechery)",
    message="Modify User > Select an option below")

main_options = [("Add new user",users.add_user),
           ("View user data",users.show_user),
           ("Delete user",users.delete_user),
           ("Modify user",update_menu.open),
           ("Import Users (csv)",import_users),
           ("Run Fanout!",fanout.run_fanout),
           ("[Quit]", exit)]

update_options = [("Add server",servers.add_server),
           ("Remove server",servers.remove_server),
           ("Update key",users.update_key),
           ("Add group(s) to server",servers.add_groups),
           ("Clear all groups from server",servers.clear_groups),
           ("[Return]", update_menu.close)]

main_menu.set_options(main_options)
update_menu.set_options(update_options)

main_menu.open()
