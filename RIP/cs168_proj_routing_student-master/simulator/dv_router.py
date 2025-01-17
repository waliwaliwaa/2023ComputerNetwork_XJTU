"""
Duozhi's Distance Vector router for CS 168

Based on skeleton code by:
  MurphyMc, zhangwen0411, lab352
"""

import sim.api as api
from cs168.dv import RoutePacket, \
                     Table, TableEntry, \
                     DVRouterBase, Ports, \
                     FOREVER, INFINITY

class DVRouter(DVRouterBase):

    # A route should time out after this interval
    ROUTE_TTL = 15

    # Dead entries should time out after this interval
    GARBAGE_TTL = 10

    # -----------------------------------------------
    # At most one of these should ever be on at once
    SPLIT_HORIZON = False
    POISON_REVERSE = False
    # -----------------------------------------------
    
    # Determines if you send poison for expired routes
    POISON_EXPIRED = False

    # Determines if you send updates when a link comes up
    SEND_ON_LINK_UP = False

    # Determines if you send poison when a link goes down
    POISON_ON_LINK_DOWN = False

    def __init__(self):
        """
        Called when the instance is initialized.
        DO NOT remove any existing code from this method.
        However, feel free to add to it for memory purposes in the final stage!
        """
        assert not (self.SPLIT_HORIZON and self.POISON_REVERSE), \
                    "Split horizon and poison reverse can't both be on"
        
        self.start_timer()  # Starts signaling the timer at correct rate.

        # Contains all current ports and their latencies.
        # See the write-up for documentation.
        self.ports = Ports()
        
        # This is the table that contains all current routes
        # last = history in stage 10
        self.table = Table()
        self.table.owner = self
        self.history = {}
        # self.history.owner = self

    def add_static_route(self, host, port):
        """
        Adds a static route to this router's table.

        Called automatically by the framework whenever a host is connected
        to this router.

        :param host: the host.
        :param port: the port that the host is attached to.
        :returns: nothing.
        """
        # `port` should have been added to `peer_tables` by `handle_link_up`
        # when the link came up.
        assert port in self.ports.get_all_ports(), "Link should be up, but is not."
        self.table[host] = TableEntry(dst=host, port=port, latency=self.ports.get_latency(port), expire_time=FOREVER)
        self.send_routes(force=False)

    def handle_data_packet(self, packet, in_port):
        """
        Called when a data packet arrives at this router.

        You may want to forward the packet, drop the packet, etc. here.

        :param packet: the packet that arrived.
        :param in_port: the port from which the packet arrived.
        :return: nothing.
        """
        if packet.dst not in self.table:
            return
        entry = self.table[packet.dst]
        if entry.latency >= INFINITY:
            return
        self.send(packet, entry.port)
        
    def send_routes(self, force=False, single_port=None):
        """
        Send route advertisements for all routes in the table.

        :param force: if True, advertises ALL routes in the table;
                      otherwise, advertises only those routes that have
                      changed since the last advertisement.
               single_port: if not None, sends updates only to that port; to
                            be used in conjunction with handle_link_up.
        :return: nothing.
        """
        # TODO: fill this in!
        for host, tableEntry in self.table.items():
            port = tableEntry.port
            if single_port is None:
                for out_port in self.ports.get_all_ports():
                    # split_horizon，从一端收到的路由信息，不能再从原路被发送回去
                    if self.SPLIT_HORIZON:
                        if out_port != port:
                            latency = tableEntry.latency
                            newPacket = RoutePacket(host, latency)
                            # force = false, search history
                            if not force:
                                if (out_port,host) not in self.history.keys() or self.history[(out_port,host)].latency != newPacket.latency:
                                    self.send(newPacket, out_port)
                                    # 发出路由之后便更新history
                                    self.history[(out_port,host)] = newPacket
                            else:
                                self.send(newPacket, out_port)
                                self.history[(out_port, host)] = newPacket
                    # split_horizon的改进，发一个坏消息比不发要好，接收方路由器会立刻抛弃坏消息路由
                    elif self.POISON_REVERSE:
                        if out_port != port:
                            latency = tableEntry.latency
                        else:
                            latency = INFINITY
                        newPacket = RoutePacket(host, latency)
                        if not force:
                            if (out_port, host) not in self.history.keys() or self.history[(out_port,host)].latency != newPacket.latency:
                                self.send(newPacket, out_port)
                                self.history[(out_port, host)] = newPacket
                        else:
                            self.send(newPacket, out_port)
                            self.history[(out_port, host)] = newPacket
                    #最普通的什么都不做
                    else:
                        latency = tableEntry.latency
                        newPacket = RoutePacket(host, latency)
                        if not force:
                            if (out_port, host) not in self.history.keys() or self.history[(out_port,host)].latency != newPacket.latency:
                                self.send(newPacket, out_port)
                                self.history[(out_port, host)] = newPacket
                        else:
                            self.send(newPacket, out_port)
                            self.history[(out_port, host)] = newPacket

            else:
                print("没写")
                
    def expire_routes(self):
        """
        Clears out expired routes from table.
        accordingly.
        """
        hosts = list(self.table.keys())
        for host in hosts:
            table_entry = self.table[host]
            # print(table_entry.expire_time)
            if table_entry.expire_time == FOREVER:
                continue
            
            # 当expired时不仅删除该信息，并且向其他路由表发送该路由不可达，加速收敛
            if self.POISON_EXPIRED and api.current_time() > table_entry.expire_time:
                current_route = self.table[host]
                poison_route = TableEntry(host, current_route.port, latency=INFINITY, expire_time=self.ROUTE_TTL)
                self.table[host] = poison_route

            # simple expired
            elif api.current_time() > table_entry.expire_time:
                del self.table[host]

    def handle_route_advertisement(self, route_dst, route_latency, port):
        """
        Called when the router receives a route advertisement from a neighbor.

        :param route_dst: the destination of the advertised route.
        :param route_latency: latency from the neighbor to the destination.
        :param port: the port that the advertisement arrived on.
        :return: nothing.
        """
        port_latency = self.ports.get_latency(port)
        new_latency = port_latency + route_latency
        new_expire_time = api.current_time() + self.ROUTE_TTL
        current_route = self.table.get(route_dst)
        new_route = TableEntry(dst=route_dst, port=port, latency=new_latency, expire_time=new_expire_time)

        # poison advertisement
        if route_latency >= INFINITY and current_route.port == port:
            # current_expire_time = current_route.expire_time
            poison_route = TableEntry(dst=route_dst, port=port, latency=INFINITY, expire_time=current_route.expire_time)
            self.table[route_dst] = poison_route
            self.send_routes(force=False)
            return

        # 当前路由表为空
        if not current_route:
            self.table[route_dst] = new_route
            self.send_routes(force=False)
            return

        # 更好的路由
        if new_latency < current_route.latency:
            self.table[route_dst] = new_route
            self.send_routes(force=False)
            return

        if current_route.port == port:
            self.table[route_dst] = new_route
            self.send_routes(force=False)
            return

    def handle_link_up(self, port, latency):
        """
        Called by the framework when a link attached to this router goes up.

        :param port: the port that the link is attached to.
        :param latency: the link latency.
        :returns: nothing.
        """
        # Add the port to the router's list of ports with its associated latency.
        self.ports.add_port(port, latency)


    def handle_link_down(self, port):
        """
        Called by the framework when a link attached to this router goes down.

        :param port: the port number used by the link.
        :returns: nothing.
        """
