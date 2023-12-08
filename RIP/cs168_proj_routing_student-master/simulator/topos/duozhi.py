import sim
def launch (switch_type = sim.config.default_switch_type, host_type = sim.config.default_host_type):

    switch_type.create('sa')
    switch_type.create('sb')
    switch_type.create('sc')
    switch_type.create('sd')

    host_type.create('h1')
    host_type.create('h2')
    host_type.create('h3')
    host_type.create('h4')

    sa.linkTo(h1, latency = 1)
    sb.linkTo(h2, latency = 1)
    sc.linkTo(h3, latency = 1)
    sd.linkTo(h4, latency = 1)

    sa.linkTo(sb, latency = 2)
    sa.linkTo(sc, latency = 7)
    sb.linkTo(sc, latency = 1)
    sb.linkTo(sd, latency = 3)
    sc.linkTo(sd, latency = 1)


