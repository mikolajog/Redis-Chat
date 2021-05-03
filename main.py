import redis


class RedisChat:
    def __init__(self, host, port, password, db):
        self.r_connector = redis.Redis(host=host, port=port,
                                       password=password, db=db)
        self.login = ""
        self.pubsub = self.r_connector.pubsub()
        self.login_or_register()
        self.chat_loop()

    def login_or_register(self):

        check = False
        while not check:
            print("Login or register user: ")
            login = input("Login: ")
            password = input("Password: ")

            check = self.check_if_correct_user(login, password)
            if not check:
                print("User with such login exists / You have provided wrong password! ")
            else:
                self.login = login
                self.add_login_to_loggedin_set(login)
                self.add_user_to_users_hash(login, password)
                self.subscribe_to_allchat()
                print("Successfully logged in!")

    def check_if_correct_user(self, login, password):
        exists = self.r_connector.hexists('users', login)
        if exists:
            if password == self.r_connector.hget('users', login).decode("utf-8"):
                return True
            else:
                return False
        else:
            return True

    def add_login_to_loggedin_set(self, login):
        self.r_connector.sadd('loggedin', login)

    def remove_login_from_loggedin_set(self, login):
        self.unsubscribe_allchat()
        self.r_connector.srem('loggedin', login)

    def add_user_to_users_hash(self, login, password):
        self.r_connector.hset('users', login, password)

    def chat_loop(self):
        LOGOUT = "1"
        PUBLISH_TO_CHANNEL = "2"
        PRINT_ALL_CHANNELS = "3"
        SUBSCRIBE_TO_CHANNEL = "4"
        GET_MESSAGES = "5"
        UNSUBSCRIBE_CHANNEL = "6"
        GET_LOGGED_IN_TO_CHANNEL = "7"
        ADD_FRIEND = "8"
        SHOW_FRIENDS = "9"
        REMOVE_FRIEND = "10"
        SHOW_FRIENDS_ON_CHAT = "11"
        SUBSCRIBE_TO_CHANNELS_BY = "12"
        UNSUBSCRIBE_TO_CHANNELS_BY = "13"
        POSSIBILITIES = [LOGOUT, PUBLISH_TO_CHANNEL, PRINT_ALL_CHANNELS, SUBSCRIBE_TO_CHANNEL, GET_MESSAGES,
                         UNSUBSCRIBE_CHANNEL, GET_LOGGED_IN_TO_CHANNEL, ADD_FRIEND, SHOW_FRIENDS, REMOVE_FRIEND,
                         SHOW_FRIENDS_ON_CHAT, SUBSCRIBE_TO_CHANNELS_BY, UNSUBSCRIBE_TO_CHANNELS_BY]
        decision = ""
        while decision != LOGOUT:
            decision = input(
                "Pick option:\n1 - LOGOUT |"
                "\n2 - PUBLISH TO CHAT |"
                "\n3 - PRINT ALL CHATS |"
                "\n4 - SUBSCRIBE TO CHAT |"
                "\n5 - GET MESSAGES |"
                "\n6 - UNSUBSCRIBE CHAT |"
                "\n7 - GET LOGGED IN TO CHAT |"
                "\n8 - ADD FRIEND |"
                "\n9 - SHOW FRIENDS |"
                "\n10 - REMOVE FRIEND |"
                "\n11 - SHOW FRIENDS ON CHAT |"
                "\n12 - SUBSCRIBE TO CHAT BY |"
                "\n13 - UNSUBSCRIBE TO CHAT BY |"
                "\nchoice: ")

            if decision not in POSSIBILITIES:
                print("Pick proper option!")

            if decision == LOGOUT:
                self.remove_login_from_loggedin_set(self.login)
                self.logoff_from_all_channels()
                self.login = ""
                print("Successfully logged out!")

            if decision == PUBLISH_TO_CHANNEL:
                channel = input("Chat: ")
                message = input("Message: ")
                self.publish_to_channel(channel, message)

            if decision == PRINT_ALL_CHANNELS:
                self.print_all_channels()

            if decision == SUBSCRIBE_TO_CHANNEL:
                channel = input("Chat: ")
                self.subscribe_to_channel(channel)

            if decision == GET_MESSAGES:
                msg = self.pubsub.get_message()
                while msg is not None:
                    print(msg)
                    msg = self.pubsub.get_message()
                print("No more messages!")

            if decision == UNSUBSCRIBE_CHANNEL:
                channel = input("Chat: ")
                self.unsubscribe_channel(channel)

            if decision == GET_LOGGED_IN_TO_CHANNEL:
                channel = input("Chat: ")
                self.get_logged_in_to_channel(channel)

            if decision == ADD_FRIEND:
                friend = input("Friend login: ")
                self.add_friend(friend)

            if decision == REMOVE_FRIEND:
                friend = input("Friend login: ")
                self.remove_friend(friend)

            if decision == SHOW_FRIENDS:
                self.show_friends()

            if decision == SHOW_FRIENDS_ON_CHAT:
                chat = input("Chat: ")
                self.show_friends_on_chat(chat)

            if decision == SUBSCRIBE_TO_CHANNELS_BY:
                pattern = input("Give lang or category: ")
                self.subscribe_to_channels_by(pattern)

            if decision == UNSUBSCRIBE_TO_CHANNELS_BY:
                pattern = input("Give lang or category: ")
                self.unsubscribe_to_channels_by(pattern)

    def logoff_from_all_channels(self):
        list_of_channels = self.r_connector.pubsub_channels()
        for channel in list_of_channels:
            self.remove_login_from_channel_logged_in(channel.decode("utf-8"))

    def publish_to_channel(self, channel, message):
        self.r_connector.publish(channel, message)

    def print_all_channels(self):
        list_of_channels = self.r_connector.pubsub_channels()
        print("Chats: ")
        for channel in list_of_channels:
            print(" - ", channel.decode("utf-8"), " ", "numOfLoggedIn: ",
                  self.get_number_of_subscribers_for_channel(channel.decode("utf-8")))

    def get_number_of_subscribers_for_channel(self, channel):
        return self.r_connector.scard("channel:" + channel)

    def subscribe_to_channel(self, channel):
        self.add_login_to_channel_logged_in(channel)
        self.pubsub.subscribe(channel)

    def unsubscribe_channel(self, channel):
        self.remove_login_from_channel_logged_in(channel)
        self.pubsub.unsubscribe(channel)

    def subscribe_to_allchat(self):
        self.add_login_to_channel_logged_in("allchat")
        self.pubsub.subscribe("allchat")

    def unsubscribe_allchat(self):
        self.remove_login_from_channel_logged_in("allchat")
        self.pubsub.unsubscribe("allchat")

    def publish_to_allchat(self, message):
        self.r_connector.publish("allchat", message)

    def add_login_to_channel_logged_in(self, channel):
        self.r_connector.sadd("channel:" + channel, self.login)

    def remove_login_from_channel_logged_in(self, channel):
        self.r_connector.srem("channel:" + channel, self.login)

    def get_logged_in_to_channel(self, channel):
        print("Logged in to chat ", channel, " :")
        for l in self.r_connector.smembers("channel:" + channel):
            print(" - ", l.decode("utf-8"))

    def add_friend(self, friend_login):
        self.r_connector.sadd("friends:" + self.login, friend_login)

    def remove_friend(self, friend_login):
        self.r_connector.srem("friends:" + self.login, friend_login)

    def show_friends(self):
        print("My friends: ")
        for f in self.r_connector.smembers("friends:" + self.login):
            print(" - ", f.decode("utf-8"))

    def show_friends_on_chat(self, channel):
        print("My friends: ")
        for f in self.r_connector.smembers("friends:" + self.login):
            if self.r_connector.sismember("channel:" + channel, f.decode("utf-8")):
                status = "Logged"
            else:
                status = "Not Logged"
            print(" - ", f.decode("utf-8"), " status:", status)

    def subscribe_to_channels_by(self, pattern):
        for ch in self.r_connector.pubsub_channels("*" + pattern + "*"):
            print(ch.decode("utf-8"))
            self.add_login_to_channel_logged_in(ch.decode("utf-8"))
        self.pubsub.psubscribe("*" + pattern + "*")

    def unsubscribe_to_channels_by(self, pattern):
        for ch in self.r_connector.pubsub_channels("*" + pattern + "*"):
            print(ch.decode("utf-8"))
            self.remove_login_from_channel_logged_in(ch.decode("utf-8"))
        self.pubsub.punsubscribe("*" + pattern + "*")


if __name__ == '__main__':
    chat = RedisChat(host='***************', port=0,
                     password='***************', db='*********')
