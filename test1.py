import socket
import sys
import threading 
import re 
import logging
from sys import argv
from sys import stdout
from threading import Thread, Timer
import datetime 
import os
import os.path

logging.basicConfig(level=logging.INFO, filename='chatserver.log', format='[%(levelname)s] %(asctime)s %(threadName)s %(message)s', ) 

buffer_size = 8192

WHO_ELSE = 'whoelse'
BROADCAST = 'broadcast' 
MESSAGE = 'message'
LOGOUT = 'logout' 

commands_dict = {
    WHO_ELSE : 'Display all chat members online ',
    BROADCAST : 'sendall a message to the entire chat room. Type \'3 <content>\'',
    MESSAGE : 'sendall a private message to someone. Type \'1 <destination peername> <content>\' ',             
    LOGOUT : 'Disconnect this session.'
}                               

user_logins = {}
logged_on_users = []
connections = []

    
servsoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servsoc.connect(("www.google.com",80))
host = servsoc.getsockname()[0]
servsoc.close()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )

def login(peer_sock):
    logged_on = True
    username = ""
    passwd = ""
    while (logged_on):
        old_user = input('Please enter a valid username :')
        username = old_user
        password = input('Please enter your password: ')
        passwd = password
        if (username in user_logins) and (passwd == user_logins[username]):
            print('\nLogin successful. Welcome to WhatDeWordChat network!')
            logged_on = False
        else:                                     
            print('Wrong Username or Password. Please try again. ')
            logged_on = True             

def prompt_create_username(peer_sock): 
    created_username = True
    new_user = ""
    while (created_username):
        user =  input('Please create your username: ')
        new_user = user
        if (new_user in user_logins):
            print('This username already exists! Please LOG IN!')
            login(s)
            created_username = False
        else:
            created_username = False
    
    new_pass = ""
    created_password = True
    while (created_password):
        pswd = input('Please type in a secure password: ')
        new_pass = pswd 
        
        if (len(new_pass) < 4 or len(new_pass) > 8):
            print( 'Passwords must be between 4 and 8 characters long. Please choose another password')
            created_password = True
        else:
            created_password = False

    outfile = open('user_pass.txt', 'a')
    outfile.write(new_user + ',' + new_pass + '\n')  
    outfile.flush()                                  
    
    #user_logins[new_user] = new_pass
    
    print('New user connected.\n')
     
def who_else(peer, myname):
    other_users = 'Users currently logged in:\n ' 
    
    for user in connections:
        if (user[0] != myname):
            other_users += user[0] + ' \n'
    
    if (len(logged_on_users) < 1):     #If no peer is online 
        other_users += '[none] '
    
    print(other_users)

    
def broadcast(username, command):
    message = 'Broadcast message from ' + myname + '\n: '
    
    for word in command[1:]:
        message += word + ' '        

    for user in connections:
        if (user[0] != myname):            
            user[1].sendall(message.encode())
      
def private_message(username, peer, command):
    message = 'Private message from ' + myname + ':'    
    receiver = command[1]
    print("Receiver "+receiver)    
    for word in command[2:]:
        message += word + ' '
    
    receiver_is_logged_in = True
    for connect_tuple in connections:
        if (connect_tuple[0] == receiver):            
            peer.send(message.encode())         
            receiver_is_logged_in = False
    
    if (receiver_is_logged_in):
        message = receiver + ' is not logged in. '
        print(message)   

"""def sendallfile(username, peer, command):
    message = 'File from ' + myname + ': '   

    receiver = command[1]                         
    path = command[2]                              
    receiver_is_logged_in = False
    print(path)
    if os.path.isfile(path):
        a = path.split("\\")
        k = len(a)
        b = a[k-1]
        #print b
        logging.info("File {} Sent".format(b))
        

        rd = file(path, "r")
        data = rd.read(2048)
        #print data
        for user_tuple in connections:
            if user_tuple[0] == receiver:
                #user_tuple[1].sendall(message)           
                peer.send(data.encode())
                receiver_is_logged_in = True

    else:
        error ='File does not exists.\n'
        for  user_tuple in connections:
            if (user_tuple[0] == myname):
                user_tuple[1].send(error.encode())"""   
               
        
def logout(peer):
    message ='Good bye!'
    peer.send(message.encode())
    peer.close() 

def prompt_commands(peer, peer_ip_and_port, username):
    command =[]    
    while 1:
        try:
            message = '\nEnter the number command:\n 1. Whoelse(1)\n 2. Broadcast(2 <content>)\n 3. Message (3 <username> <content>)\n 4. Logout(4)\n:  '
            print(message)
            
            command = input(">>>").split()
            
        except:                                                     
            sys.exit()
        
        if (command[0] == "1"):
            who_else(peer, myname)
              
        elif (command[0] == "2"):                                  
            broadcast(username, command)

        elif (command[0] == "3"):
            private_message(username, peer, command)
            
        elif (command[0] == "4"):
            logout(peer)
            
        else:           
            print('Command not found')
            
def readSocketAndOutput(s):
    global byeFlag
    print("Enter 'bye' to quit chat")
    
    while True:
        if byeFlag:
            try:
                str = s.recv(buffer_size).decode()
                #logged_in_users.append((str, s))
                print("\r>>> " + str)
                stdout.flush()
                #inputs = input( "<<<")
                #s.sendall(inputs) 
            except:
                print("Connection closed")
                break

            if str == "bye":
                byeFlag = 0;
                break
        
    print("Remote user disconnected!!!")
    s.close()
    sys.exit()
    
def readSTDINandWriteSocket(s,peer_ip_and_port):
    global byeFlag   
    while True:
        prompt_commands(s, peer_ip_and_port,"")

        
aFile = open('user_pass.txt', 'r')
for line in aFile:
    (key, val) = line.split(',')
    user_logins[key] = val
    
prompt_create_username(s)
myname = input("Enter your prefered peer name: ")
logged_on_users.append(myname)
connections.append((myname, None))

byeFlag = 1;
ch = input("Connect[1] to peer or wait[2] for peer connection. Enter choice:")

if ch == "1":
    """host = input("Enter peer IP:")"""    
    port = 54321
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1 )
    s.connect((host, port))
    s.sendto(myname.encode(),(host,port))
    peerName = s.recv(buffer_size).decode() 
    stdout.flush()   
    print(peerName)
    connections.append((peerName, s))       
    threading.Thread(target=readSocketAndOutput, args=(s,)).start()
    threading.Thread(target=readSTDINandWriteSocket,args =(s,(host,host))).start() 

elif ch == "2":
    host = ''
    port = 54321
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1 )
    s.bind((host, port))
    s.listen(10)         
    print("Waiting for connection...")
    while True:
        c, addr = s.accept()     
        peerName = c.recv(buffer_size).decode() 
        stdout.flush()   
        print(peerName)
        connections.append((peerName, c))
        c.send(myname.encode())      
        threading.Thread(target=readSocketAndOutput, args=(c,)).start()
        threading.Thread(target=readSTDINandWriteSocket,args =(c,addr)).start()

else:
    print("Incorrect choice")
    sys.exit()




