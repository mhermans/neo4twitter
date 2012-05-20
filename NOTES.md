len(t.gdb.extensions.GremlinPlugin.execute_script('g.E'))
n = t.gdb.nodes.get(0)
[(n.end['screen_name'], n.end['followers_count'] + n.end['friends_count']) for n in ref.relationships.outgoing('Contains')]

'START seed=node(0) 
 MATCH seed -[:Contains]-> seeds -[:Follows]-> user  
 RETURN user.followers_count?, user.friends_count?, user.screen_name? '

'START seed=node(0) MATCH seed -[:Contains]-> seeds -[:Follows]-> user 
 WHERE ( user.detail = "full" ) 
 RETURN user.followers_count?, user.friends_count?, user.screen_name?'

# total number of followers, friends
'START seeds=node(1117, 998, 818, 364, 1) 
 MATCH seeds <-[:Follows]-> users 
 RETURN seeds.screen_name, count(users)'

'START irail = node:users(screen_name = "iRail"), pc = node:users(screen_name = "pietercolpaert") 
 MATCH pc <-[r]-> irail RETURN type(r), count(r)'


# detect duplicate node twitter ids:
 "START user = node(*) RETURN count(user.id) AS all, count(distinct user.id) AS distinct"

 # summarize order of crawl:
 "START n = node:users(structure='crawled') RETURN n.screen_name"
