"""
Created on Sun Apr  5 00:00:32 2015

@author: zhengzhang

Introduction to Computer Science
Samuel King
12/6/20
"""
from chat_utils import *
import json

class ClientSM:
    def __init__(self, s):
        self.state = S_OFFLINE
        self.peer = ''
        self.me = ''
        self.out_msg = ''
        self.s = s

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def set_myname(self, name):
        self.me = name

    def get_myname(self):
        return self.me

    def connect_to(self, peer):
        msg = json.dumps({"action":"connect", "target":peer})
        mysend(self.s, msg)
        response = json.loads(myrecv(self.s))
        if response["status"] == "success":
            self.peer = peer
            self.out_msg += 'You are connected with '+ self.peer + '\n'
            return (True)
        elif response["status"] == "busy":
            self.out_msg += 'User is busy. Please try again later\n'
        elif response["status"] == "self":
            self.out_msg += 'Cannot talk to yourself (sick)\n'
        else:
            self.out_msg += 'User is not online, try again later\n'
        return(False)

    def play_with(self, peer):
        msg = json.dumps({"action":"game", "target":peer})
        mysend(self.s, msg)
        response = json.loads(myrecv(self.s))
        if response["status"] == "success":
            self.peer = peer
            self.out_msg += 'You are connected with '+ self.peer + '\n'
            return (True)
        elif response["status"] == "busy":
            self.out_msg += 'User is busy. Please try again later\n'
        elif response["status"] == "self":
            self.out_msg += 'Cannot talk to yourself (sick)\n'
        else:
            self.out_msg += 'User is not online, try again later\n'
        return(False)

    def disconnect(self):
        msg = json.dumps({"action":"disconnect"})
        mysend(self.s, msg)
        self.out_msg += 'You are disconnected from ' + self.peer + '\n'
        self.peer = ''

    def proc(self, my_msg, peer_msg):
        self.out_msg = ''
#==============================================================================
# Once logged in, do a few things: get peer listing, connect, search
# And, of course, if you are so bored, just go
# This is event handling instate "S_LOGGEDIN"
#==============================================================================
        if self.state == S_LOGGEDIN:
            # todo: can't deal with multiple lines yet
            if len(my_msg) > 0:

                if my_msg == 'q':
                    self.out_msg += 'See you next time!\n'
                    self.state = S_OFFLINE

                elif my_msg == 'time':
                    mysend(self.s, json.dumps({"action":"time"}))
                    time_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += "Time is: " + time_in

                elif my_msg == 'who':
                    mysend(self.s, json.dumps({"action":"list"}))
                    logged_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += 'Here are all the users in the system:\n'
                    self.out_msg += logged_in

                elif my_msg[0] == 'c':
                    peer = my_msg[1:]
                    peer = peer.strip()
                    if self.connect_to(peer) == True:
                        self.state = S_CHATTING
                        self.out_msg += 'Connect to ' + peer + '. Chat away!\n\n'
                        self.out_msg += '-----------------------------------\n'
                    else:
                        self.out_msg += 'Connection unsuccessful\n'

                elif my_msg[0] == '?':
                    term = my_msg[1:].strip()
                    mysend(self.s, json.dumps({"action":"search", "target":term}))
                    search_rslt = json.loads(myrecv(self.s))["results"].strip()
                    if (len(search_rslt)) > 0:
                        self.out_msg += search_rslt + '\n\n'
                    else:
                        self.out_msg += '\'' + term + '\'' + ' not found\n\n'

                elif my_msg[0] == 'p' and my_msg[1:].isdigit():
                    poem_idx = my_msg[1:].strip()
                    mysend(self.s, json.dumps({"action":"poem", "target":poem_idx}))
                    poem = json.loads(myrecv(self.s))["results"]
                    if (len(poem) > 0):
                        self.out_msg += poem + '\n\n'
                    else:
                        self.out_msg += 'Sonnet ' + poem_idx + ' not found\n\n'

                elif my_msg[0] == "g":
                    peer = my_msg[1:]
                    peer = peer.strip()
                    if self.play_with(peer) == True:
                        self.out_msg += 'Connected to ' + peer + '!\n\n'
                        self.out_msg += "Let's play tic-tac-toe.\n"
                        self.out_msg += '-----------------------------------\n'
                        self.out_msg += "Commands:\n"
                        self.out_msg += "Press b to see the board.\n"
                        self.out_msg += "Each number represents a move on the board:\n" + "1. Upper Left\n" + "2. Upper Center\n" + "3. Upper Right\n" \
                               + "4. Middle Left\n" + "5. Middle Center\n" +  "6. Middle Right\n" + "7. Lower Left\n" \
                               + "8. Lower Center\n" + "9. Lower Right\n"
                        self.out_msg += "Enter a number when it's your turn to make a move. The board will appear after you make a move.\n"
                        self.out_msg += "------------------------------------\n"
                        self.state = S_PLAYING
                    else:
                        self.out_msg += 'Connection unsuccessful\n'

                else:
                    self.out_msg += menu

            if len(peer_msg) > 0:
                try:
                    peer_msg = json.loads(peer_msg)
                except Exception as err :
                    self.out_msg += " json.loads failed " + str(err)
                    return self.out_msg
         
                if peer_msg["action"] == "connect":
                    # ----------your code here------#
                    self.peer = peer_msg["from"]
                    self.out_msg += "Request from " + self.peer + "\n"
                    self.out_msg += "You are connected with " + self.peer
                    self.out_msg += ". Chat away!\n\n"
                    self.out_msg += "------------------------------------\n"
                    self.state = S_CHATTING
                    # ----------end of your code----#

                elif peer_msg["action"] == "game":
                    self.peer = peer_msg["from"]
                    self.out_msg += "Request from " + self.peer + "\n"
                    self.out_msg += "You are connected with " + self.peer + "\n"
                    self.out_msg += "Let's play tic-tac-toe.\n"
                    self.out_msg += "------------------------------------\n"
                    self.out_msg += "Commands:\n"
                    self.out_msg += "Press b to see the board.\n"
                    self.out_msg += "Each number represents a move on the board:\n" + "1. Upper Left\n" + "2. Upper Center\n" + "3. Upper Right\n" \
                               + "4. Middle Left\n" + "5. Middle Center\n" +  "6. Middle Right\n" + "7. Lower Left\n" \
                               + "8. Lower Center\n" + "9. Lower Right\n"
                    self.out_msg += "Enter a number when it's your turn to make a move. The board will appear after you make a move.\n"
                    self.out_msg += "------------------------------------\n"
                    self.state = S_PLAYING
                    
#==============================================================================
# Start chatting, 'bye' for quit
# This is event handling instate "S_CHATTING"
#==============================================================================
        elif self.state == S_CHATTING:
            if len(my_msg) > 0:     # my stuff going out
                mysend(self.s, json.dumps({"action":"exchange", "from":"[" + self.me + "]", "message":my_msg}))
                if my_msg == 'bye':
                    self.disconnect()
                    self.state = S_LOGGEDIN
                    self.peer = ''
            if len(peer_msg) > 0:    # peer's stuff, coming in
                peer_msg = json.loads(peer_msg)

                # ----------your code here------#
                if peer_msg["action"] == "connect":
                    self.out_msg += peer_msg["from"] + " has joined."
                elif peer_msg["action"] == "disconnect":
                    self.state = S_LOGGEDIN
                else:
                    self.out_msg += peer_msg["from"] + peer_msg["message"]
                # ----------end of your code----#
                
            # Display the menu again
            if self.state == S_LOGGEDIN:
                self.out_msg += menu
#==============================================================================
# handles state S_PLAYING
#==============================================================================

        elif self.state == S_PLAYING:
            if len(my_msg) > 0:
                if my_msg == "b":
                    mysend(self.s, json.dumps({"action":"exchange", "from":"[" + self.me + "]", "message":my_msg}))
                    mysend(self.s, json.dumps({"action":"screen_update"}))
                    response = json.loads(myrecv(self.s))
                    self.out_msg += "\n"
                    self.out_msg += response["game_board"]
                    self.out_msg += "\n"
                elif my_msg == "1" or my_msg == "2" or my_msg == "3" or my_msg == "4" or my_msg == "5" or my_msg == "6" or my_msg == "7" or my_msg == "8" or my_msg == "9":
                    mysend(self.s, json.dumps({"action":"exchange", "from":"[" + self.me + "]", "message":my_msg}))
                    mysend(self.s, json.dumps({"action":"move", "selected_move":my_msg}))
                    response = json.loads(myrecv(self.s))
                    self.out_msg += response["message"]
                    self.out_msg += "\n"
                    mysend(self.s, json.dumps({"action":"screen_update"}))
                    response = json.loads(myrecv(self.s))
                    self.out_msg += "\n"
                    self.out_msg += response["game_board"]
                    self.out_msg += "\n"
                elif my_msg == 'bye':
                    self.disconnect()
                    self.state = S_LOGGEDIN
                    self.peer = ''
            if len(peer_msg) > 0:
                peer_msg = json.loads(peer_msg)
                if peer_msg["action"] == "disconnect":
                    self.state = S_LOGGEDIN
                else:
                    self.out_msg += peer_msg["from"] + peer_msg["message"]
                    mysend(self.s, json.dumps({"action":"screen_update"}))
                    response = json.loads(myrecv(self.s))
                    self.out_msg += "\n"
                    self.out_msg += response["game_board"]
                    self.out_msg += "\n"

            # Display the menu again
            if self.state == S_LOGGEDIN:
                self.out_msg += menu
            
#==============================================================================
# invalid state
#==============================================================================
        else:
            self.out_msg += 'How did you wind up here??\n'
            print_state(self.state)

        return self.out_msg
