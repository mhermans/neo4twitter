from neo4jrestclient.client import GraphDatabase, NotFoundError
import tweepy, datetime, logging

logging.basicConfig()
log = logging.getLogger("Main")
log.setLevel(logging.INFO)

class TwitterGraph(object):

    def _init_twitter_api(self, auth_dict, cachedir=None):

        # Twitter API authentication

        auth = tweepy.OAuthHandler(
                auth_dict['consumer_key'], 
                auth_dict['consumer_secret'])
        auth.set_access_token(
                auth_dict['access_token'], 
                auth_dict['access_token_secret'])

        self.TWEEPY_CACHE = tweepy.cache.FileCache(cachedir, 0)
        self.api = tweepy.API(auth, cache=self.TWEEPY_CACHE)

        log.info('Authenticated with Twitter')


    def __init__(self, auth_dict, 
            dburl="http://localhost:7474/db/data/",  
            cachedir='.cache'):
        """Initialize Twitter API and Neo4j-link."""

        self._init_twitter_api(auth_dict, cachedir)
        self.gdb = GraphDatabase(dburl)

        # check if indexes are ok
        try:
            self.gdb.nodes.indexes.get('users')
            log.info('users-index OK')
        except NotFoundError:
            self.gdb.nodes.indexes.create('users')
            log.info('users-index created')


    @property
    def limit(self):
        return self.api.rate_limit_status()['remaining_hits']


    def fetch_user_data(self, user_id):
        """Fetch user data for a given ID, return dictionary."""

        log.info('Fetching user data from Twitter for ID %s' % user_id)
        user = self.api.get_user(user_id)
        props = user.__dict__ # user properties

        del props['_api'], props['status'] # no embedded objects

        props['accessed'] = datetime.datetime.now()
        props['detail'] = 'full'
        props['type'] = 'user'

        return props


    def get_user(self, user_id):
        """Get user node from graph if existing, based on ID."""

        i = self.gdb.nodes.indexes.get('users')
        results = i.get('user_id', user_id) # always iterable

        if len(results) == 1:
            log.info('Found existing users, ID %s' % user_id)
            return results[0]
        else:
            log.info('No user in graph with ID %s' % user_id)
            return None

    def add_subscriptions(self, user_node):

        try:
            user_label = user_node.get('screen_name') 
        except NotFoundError:
            user_label = str(user_node.get('id'))

        # add followers
        followers = self.api.followers_ids(user_node['id'])
        log.info('Found %s followers for %s' % (str(len(followers)), user_label))

        for follower_id in followers:
            follower_node = self.get_or_create_user(follower_id)
           
            try:
                follower_label = follower_node.get('screen_name')
            except NotFoundError:
                follower_label = str(follower_node.get('id'))
            
            log.info('Adding follower %s for user %s' % (follower_label, user_label))
            follower_node.relationships.create('Follows', user_node,
                    on=datetime.datetime.now())

        # add friends
        friends = self.api.friends_ids(user_node['id'])
        log.info('Found %s friends for %s' % (str(len(friends)), user_node['id']))

        for friend_id in friends:
            friend_node = self.get_or_create_user(friend_id)

            try:
                friend_label = friend_node.get('screen_name')
            except NotFoundError:
                friend_label = str(friend_node.get('id'))

            log.info('Adding friend %s for user %s' % (friend_label, user_label))
            user_node.relationships.create('Follows', friend_node,
                    on=datetime.datetime.now())


    def add_user(self, identifier, overwrite = False):
        """Adds user to graph, based on ID or screen name."""

        if not identifier.isalnum():
            return None
            #identifier = identifier # TODO screen name -> user id

        # skip adding user if existing & detailed
        existing_user = self.get_user(identifier)
        if existing_user:
            if existing_user.get('detail') == 'full':
                log.info('Not adding user %s, already (full) in graph' % identifier)
                return existing_user
            if existing_user.get('detail') == 'basic':
                log.info('Not adding user %s, already (basic) in graph: updating' % identifier)
                return self.update_user(existing_user)


        log.info('Adding user %s to graph' % identifier)
        # get and assign user data to node
        props = self.fetch_user_data(identifier)
        user_node = self.gdb.node(**props)

        # add user node to indexes
        users = self.gdb.nodes.indexes.get('users')
        users['user_id'][props.get('id_str')] = user_node
        users['screen_name'][props.get('screen_name')] = user_node

        # add followers/following
        
        self.add_subscriptions(user_node)

        return user_node

    def update_user(self, user_node):

        if user_node.get('detail') == 'full':
            log.info('Not updating user %s, already fully detailed' % user_node['screen_name'])
            return user_node

        if user_node.get('detail') == 'basic':
            log.info('Updating user %s' % str(user_node['id']))
            props = self.fetch_user_data(user_node['id'])
            user_node.properties = props
            self.add_subscriptions(user_node)

            users = self.gdb.nodes.indexes.get('users')
            users['screen_name'][user_node['screen_name']] = user_node

            return user_node


    def get_or_create_user(self, user_id):
        user = self.get_user(user_id)

        if not user:
            log.info('User %s not found, creating user with basic info' % user_id)
            user = self.gdb.node(id = user_id, detail='basic', 
                    accessed = datetime.datetime.now(),
                    type='user')

            users = self.gdb.nodes.indexes.get('users')
            users['user_id'][user_id] = user

        return user


if __name__ == '__main__':
    from config import AUTH
    t = TwitterGraph(AUTH)
    mh_id = '231959424'
    rid = 216027858
    #mh = t.add_user('231959424')