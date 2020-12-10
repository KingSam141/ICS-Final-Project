"""
Created on Tue Jul 22 00:47:05 2014

@author: alina, zzhang

Introduction to Computer Science
Samuel King
12/6/20
"""

import time
import socket
import select
import sys
import string
import indexer
import json
import pickle as pkl
from chat_utils import *
import chat_group as grp


class Server:
    def __init__(self):
        self.new_clients = []  # list of new sockets of which the user id is not known
        self.logged_name2sock = {}  # dictionary mapping username to socket
        self.logged_sock2name = {}  # dict mapping socket to user name
        self.all_sockets = []
        self.group = grp.Group()
        # start server
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(SERVER)
        self.server.listen(5)
        self.all_sockets.append(self.server)
        # initialize past chat indices
        self.indices = {}
        # sonnet
        self.sonnet = indexer.PIndex("AllSonnets.txt")
        # the following seven variables are for the tic-tac-toe game
        self.game_string = ""
        self.first_row = [" ", "|", " ", "|", " "]
        self.second_row = ["-", "-", "-", "-", "-"]
        self.third_row = [" ", "|", " ", "|", " "]
        self.fourth_row = ["-", "-", "-", "-", "-"]
        self.fifth_row = [" ", "|", " ", "|", " "]
        self.turn = 0

    def new_client(self, sock):
        # add to all sockets and to new clients
        print('new client...')
        sock.setblocking(0)
        self.new_clients.append(sock)
        self.all_sockets.append(sock)

    def login(self, sock):
        # read the msg that should have login code plus username
        try:
            msg = json.loads(myrecv(sock))
            if len(msg) > 0:

                if msg["action"] == "login":
                    name = msg["name"]
                    if self.group.is_member(name) != True:
                        # move socket from new clients list to logged clients
                        self.new_clients.remove(sock)
                        # add into the name to sock mapping
                        self.logged_name2sock[name] = sock
                        self.logged_sock2name[sock] = name
                        # load chat history of that user
                        if name not in self.indices.keys():
                            try:
                                self.indices[name] = pkl.load(
                                    open(name + '.idx', 'rb'))
                            except IOError:  # chat index does not exist, then create one
                                self.indices[name] = indexer.Index(name)
                        print(name + ' logged in')
                        self.group.join(name)
                        mysend(sock, json.dumps(
                            {"action": "login", "status": "ok"}))
                    else:  # a client under this name has already logged in
                        mysend(sock, json.dumps(
                            {"action": "login", "status": "duplicate"}))
                        print(name + ' duplicate login attempt')
                else:
                    print('wrong code received')
            else:  # client died unexpectedly
                self.logout(sock)
        except:
            self.all_sockets.remove(sock)

    def logout(self, sock):
        # remove sock from all lists
        name = self.logged_sock2name[sock]
        pkl.dump(self.indices[name], open(name + '.idx', 'wb'))
        del self.indices[name]
        del self.logged_name2sock[name]
        del self.logged_sock2name[sock]
        self.all_sockets.remove(sock)
        self.group.leave(name)
        sock.close()

# ==============================================================================
# main command switchboard
# ==============================================================================
    def handle_msg(self, from_sock):
        # read msg code
        msg = myrecv(from_sock)
        if len(msg) > 0:
            # ==============================================================================
            # handle connect request this is implemented for you
            # ==============================================================================
            msg = json.loads(msg)
            if msg["action"] == "game":
                to_name = msg["target"]
                from_name = self.logged_sock2name[from_sock]
                if to_name == from_name:
                    msg = json.dumps({"action": "game", "status": "self"})
                # connect to the peer
                elif self.group.is_member(to_name):
                    to_sock = self.logged_name2sock[to_name]
                    self.group.connect(from_name, to_name)
                    the_guys = self.group.list_me(from_name)
                    msg = json.dumps(
                        {"action": "game", "status": "success"})
                    for g in the_guys[1:]:
                        to_sock = self.logged_name2sock[g]
                        mysend(to_sock, json.dumps(
                            {"action": "game", "status": "request", "from": from_name}))
                else:
                    msg = json.dumps(
                        {"action": "game", "status": "no-user"})
                mysend(from_sock, msg)
            elif msg["action"] == "connect":
                to_name = msg["target"]
                from_name = self.logged_sock2name[from_sock]
                if to_name == from_name:
                    msg = json.dumps({"action": "connect", "status": "self"})
                # connect to the peer
                elif self.group.is_member(to_name):
                    to_sock = self.logged_name2sock[to_name]
                    self.group.connect(from_name, to_name)
                    the_guys = self.group.list_me(from_name)
                    msg = json.dumps(
                        {"action": "connect", "status": "success"})
                    for g in the_guys[1:]:
                        to_sock = self.logged_name2sock[g]
                        mysend(to_sock, json.dumps(
                            {"action": "connect", "status": "request", "from": from_name}))
                else:
                    msg = json.dumps(
                        {"action": "connect", "status": "no-user"})
                mysend(from_sock, msg)
# ==============================================================================
# handle messeage exchange: IMPLEMENT THIS
# ==============================================================================
            elif msg["action"] == "exchange":
                from_name = self.logged_sock2name[from_sock]
                """
                Finding the list of people to send to and index message
                """
                # IMPLEMENTATION
                # ---- start your code ---- #
                everyone = self.group.list_me(from_name)
                text = text_proc(msg["message"], from_name)
                self.indices[from_name].add_msg_and_index(text)
                # ---- end of your code --- #

                the_guys = self.group.list_me(from_name)[1:]
                for g in the_guys:
                    to_sock = self.logged_name2sock[g]

                    # IMPLEMENTATION
                    # ---- start your code ---- #
                    self.indices[g].add_msg_and_index(text)
                    mysend(to_sock, json.dumps({"action": "exchange", "from": msg["from"], "message": msg["message"]}))
                    # ---- end of your code --- #

# ==============================================================================
# the "from" guy has had enough (talking to "to")!
# ==============================================================================
            elif msg["action"] == "disconnect":
                from_name = self.logged_sock2name[from_sock]
                the_guys = self.group.list_me(from_name)
                self.group.disconnect(from_name)
                the_guys.remove(from_name)
                if len(the_guys) == 1:  # only one left
                    g = the_guys.pop()
                    to_sock = self.logged_name2sock[g]
                    mysend(to_sock, json.dumps(
                        {"action": "disconnect", "msg": "everyone left, you are alone"}))
# ==============================================================================
#                 listing available peers: IMPLEMENT THIS
# ==============================================================================
            elif msg["action"] == "list":

                # IMPLEMENTATION
                # ---- start your code ---- #
                msg = ""
                
                for guy in self.logged_name2sock:
                    print([guy])
                    msg += guy
                    msg += " "

                # ---- end of your code --- #
                mysend(from_sock, json.dumps(
                    {"action": "list", "results": msg}))
# ==============================================================================
#             retrieve a sonnet : IMPLEMENT THIS
# ==============================================================================
            elif msg["action"] == "poem":

                # IMPLEMENTATION
                # ---- start your code ---- #
                
                number_string = msg["target"]
                num = int(number_string)
                print(num)
                poem_list = []
                for i in self.sonnet.get_poem(num):
                    poem_list += [i]
                print('here:\n', poem_list)

                poem = ""
                for i in poem_list:
                    poem += i
                
                # ---- end of your code --- #

                mysend(from_sock, json.dumps(
                    {"action": "poem", "results": poem}))
# ==============================================================================
#                 time
# ==============================================================================
            elif msg["action"] == "time":
                ctime = time.strftime('%d.%m.%y,%H:%M', time.localtime())
                mysend(from_sock, json.dumps(
                    {"action": "time", "results": ctime}))
# ==============================================================================
#                 search: : IMPLEMENT THIS
# ==============================================================================
            elif msg["action"] == "search":

                # IMPLEMENTATION
                # ---- start your code ---- #
                search_term = msg["target"]
                from_name = self.logged_sock2name[from_sock]
                print('Search for ' + from_name + ' for ' + search_term)
                search_rslt = '\n'.join([x[-1] for x in self.indices[from_name].search(search_term)])
                print('Server side search: ' + search_rslt)
                # ---- end of your code --- #
                mysend(from_sock, json.dumps(
                    {"action": "search", "results": search_rslt}))

# ==============================================================================
#                 Tic-Tac-Toe Game
# ==============================================================================

            elif msg["action"] == "game":
                players = []
                names = self.logged_name2sock
                for name in names:
                    players += [name]
                print(players)
                
                mysend(from_sock, json.dumps({"action": "game", "time_to_start": "y"}))

            elif msg["action"] == "screen_update":
                game_board = [self.first_row, "\n", self.second_row, "\n", self.third_row, "\n", self.fourth_row, "\n", self.fifth_row, "\n"]

                self.game_string = ""

                for i in game_board:
                    for x in i:
                        self.game_string += x
                        
                move_message = "Each number represents a move on the board:\n" + "1. Upper Left\n" + "2. Upper Center\n" + "3. Upper Right\n" \
                               + "4. Middle Left\n" + "5. Middle Center\n" +  "6. Middle Right\n" + "7. Lower Left\n" \
                               + "8. Lower Center\n" + "9. Lower Right\n"
                mysend(from_sock, json.dumps({"action": "move_initiation", "message": move_message, "game_board": self.game_string}))

            elif msg["action"] == "move":
                # for reference:
                """
                first_row = [" ", "|", " ", "|", " "]
                second_row = ["-", "-", "-", "-", "-"]
                third_row = [" ", "|", " ", "|", " "]
                fourth_row = ["-", "-", "-", "-", "-"]
                fifth_row = [" ", "|", " ", "|", " "]
                """
                if len(msg["selected_move"]) > 0:
                    if msg["selected_move"] == "1":
                        mysend(from_sock, json.dumps({"action": "making_a_move", "message": "You made a move in the Upper Left spot.", "game_board": self.game_string}))
                        self.turn += 1
                        if self.turn % 2 != 0:
                            self.first_row[0] = "X"
                        elif self.turn % 2 == 0:
                            self.first_row[0] = "0"
                    if msg["selected_move"] == "2":
                        mysend(from_sock, json.dumps({"action": "making_a_move", "message": "You made a move in the Upper Center spot.", "game_board": self.game_string}))
                        self.turn += 1
                        if self.turn % 2 != 0:
                            self.first_row[2] = "X"
                        elif self.turn % 2 == 0:
                            self.first_row[2] = "0"
                    if msg["selected_move"] == "3":
                        mysend(from_sock, json.dumps({"action": "making_a_move", "message": "You made a move in the Upper Right spot.", "game_board": self.game_string}))
                        self.turn += 1
                        if self.turn % 2 != 0:
                            self.first_row[4] = "X"
                        elif self.turn % 2 == 0:
                            self.first_row[4] = "0"
                    if msg["selected_move"] == "4":
                        mysend(from_sock, json.dumps({"action": "making_a_move", "message": "You made a move in the Middle Left spot.", "game_board": self.game_string}))
                        self.turn += 1
                        if self.turn % 2 != 0:
                            self.third_row[0] = "X"
                        elif self.turn % 2 == 0:
                            self.third_row[0] = "0"
                    if msg["selected_move"] == "5":
                        mysend(from_sock, json.dumps({"action": "making_a_move", "message": "You made a move in the Middle Center spot.", "game_board": self.game_string}))
                        self.turn += 1
                        if self.turn % 2 != 0:
                            self.third_row[2] = "X"
                        elif self.turn % 2 == 0:
                            self.third_row[2] = "0"
                    if msg["selected_move"] == "6":
                        mysend(from_sock, json.dumps({"action": "making_a_move", "message": "You made a move in the Middle Right spot.", "game_board": self.game_string}))
                        self.turn += 1
                        if self.turn % 2 != 0:
                            self.third_row[4] = "X"
                        elif self.turn % 2 == 0:
                            self.third_row[4] = "0"
                    if msg["selected_move"] == "7":
                        mysend(from_sock, json.dumps({"action": "making_a_move", "message": "You made a move in the Lower Left spot.", "game_board": self.game_string}))
                        self.turn += 1
                        if self.turn % 2 != 0:
                            self.fifth_row[0] = "X"
                        elif self.turn % 2 == 0:
                            self.fifth_row[0] = "0"
                    if msg["selected_move"] == "8":
                        mysend(from_sock, json.dumps({"action": "making_a_move", "message": "You made a move in the Lower Center spot.", "game_board": self.game_string}))
                        if self.turn % 2 != 0:
                            self.fifth_row[2] = "X"
                        elif self.turn % 2 == 0:
                            self.fifth_row[2] = "0"
                    if msg["selected_move"] == "9":
                        mysend(from_sock, json.dumps({"action": "making_a_move", "message": "You made a move in the Lower Right spot.", "game_board": self.game_string}))
                        self.turn += 1
                        if self.turn % 2 != 0:
                            self.fifth_row[4] = "X"
                        elif self.turn % 2 == 0:
                            self.fifth_row[4] = "0"

            elif msg["action"] == "check_for_winner":
                """
                first_row = [" ", "|", " ", "|", " "]
                second_row = ["-", "-", "-", "-", "-"]
                third_row = [" ", "|", " ", "|", " "]
                fourth_row = ["-", "-", "-", "-", "-"]
                fifth_row = [" ", "|", " ", "|", " "]
                """
                players = []
                names = self.logged_name2sock
                for name in names:
                    players += [name]

                def winning_line(line):
                    return all(x == line[0] for x in line)

                every_combination = {}
                
                every_combination["column_one"] = [self.first_row[0], self.third_row[0], self.fifth_row[0]]
                every_combination["column_two"] = [self.first_row[2], self.third_row[2], self.fifth_row[2]]
                every_combination["column_three"] = [self.first_row[4], self.third_row[4], self.fifth_row[4]]
                every_combination["row_one"] = [self.first_row[0], self.first_row[2], self.first_row[4]]
                every_combination["row_two"] = [self.third_row[0], self.third_row[2], self.third_row[4]]
                every_combination["row_three"] = [self.fifth_row[0], self.fifth_row[2], self.fifth_row[4]]
                every_combination["diagonal_tlbr"] = [self.first_row[0], self.third_row[2], self.fifth_row[4]]
                every_combination["diagonal_trbl"] = [self.first_row[4], self.third_row[2], self.fifth_row[0]]
                
                print(every_combination)

                for line in every_combination.values():
                    if line[0] == "X" and winning_line(line) == True:
                        mysend(from_sock, json.dumps({"action": "declaring_winner", "from": players[0], "message": " has won!\n"}))
                    elif line[0] == "O" and winning_line(line) == True:
                        mysend(from_sock, json.dumps({"action": "declaring_winner", "from": players[1], "message": " has won!\n"}))
                
                    
# ==============================================================================
#                 the "from" guy really, really has had enough
# ==============================================================================

        else:
            # client died unexpectedly
            self.logout(from_sock)

# ==============================================================================
# main loop, loops *forever*
# ==============================================================================
    def run(self):
        print('starting server...')
        while(1):
            read, write, error = select.select(self.all_sockets, [], [])
            print('checking logged clients..')
            for logc in list(self.logged_name2sock.values()):
                if logc in read:
                    self.handle_msg(logc)
            print('checking new clients..')
            for newc in self.new_clients[:]:
                if newc in read:
                    self.login(newc)
            print('checking for new connections..')
            if self.server in read:
                # new client request
                sock, address = self.server.accept()
                self.new_client(sock)


def main():
    server = Server()
    server.run()


if __name__ == '__main__':
    main()
