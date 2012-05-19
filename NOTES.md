len(t.gdb.extensions.GremlinPlugin.execute_script('g.E'))
n = t.gdb.nodes.get(0)
[(n.end['screen_name'], n.end['followers_count'] + n.end['friends_count']) for n in ref.relationships.outgoing('Contains')]
