"""
Your awesome Distance Vector router for CS 168

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
        self.table = Table()
        self.table.owner = self
        self.history = {}  # {(host, port) : RoutePacket} or RoutePackets contain [destination, latency]


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
        # TODO: fill this in!
        latency = self.ports.get_latency(port)
        self.table[host] = TableEntry(host, port, latency, expire_time=FOREVER)  # add to table


    def handle_data_packet(self, packet, in_port):
        """
        Called when a data packet arrives at this router.
        You may want to forward the packet, drop the packet, etc. here.
        :param packet: the packet that arrived.
        :param in_port: the port from which the packet arrived.
        :return: nothing.
        """
        # TODO: fill this in!
        # If no route exists for a packet’s destination, your router should drop the packet (do nothing).
        pack_dest = packet.dst
        if not self.table.get(pack_dest):
            return

        # if the latency is greater than or equal to INFINITY you should also drop the packet
        table_entry = self.table.get(pack_dest)
        latency = table_entry.latency
        if latency >= INFINITY:
            return

        out_port = table_entry.port
        if out_port == in_port:
            return

        self.send(packet, out_port, flood=False)


    def send_routes(self, force=False, single_port=None):
        """Send route advertisements for all routes in the table.
        :param force: if True, advertises ALL routes in the table;
                      otherwise, advertises only those routes that have
                      changed since the last advertisement.
        single_port: if not None, sends updates only to that port; to
                            be used in conjunction with handle_link_up.
        :return: nothing."""
        # TODO: fill this in!
        ports_dict = self.ports.get_underlying_dict();
        ports_keys_list = list(ports_dict.keys())

        # 向所有端口发送新的RoutePacket
        for port in ports_keys_list:
            for host, entry in self.table.items():

                port_packet_came_from = entry.port
                # 检查历史记录中是否有该主机和端口的表项
                table_entry = (host, port) in self.history.keys()
                if table_entry:
                    old_ad = self.history[(host, port)]

                if single_port is not None:
                    print("Single Port not None! ")

                if self.SPLIT_HORIZON:
                    if port != port_packet_came_from:
                        new_ad = RoutePacket(host, entry.latency)
                        self.send(new_ad, port, flood=False)

                elif self.POISON_REVERSE:
                    if port == port_packet_came_from:
                        if not force:
                            if not table_entry or old_ad.destination != host or old_ad.latency != INFINITY:
                                new_ad = RoutePacket(host, INFINITY)  # advertise as unreachable
                                self.send(new_ad, port, flood=False)
                                self.history[(host, port)] = new_ad
                        else:
                            new_ad = RoutePacket(host, INFINITY)  # advertise as unreachable
                            self.send(new_ad, port, flood=False)
                            self.history[(host, port)] = new_ad
                    else:
                        if not force:
                            if not table_entry or old_ad.destination != host or old_ad.latency != entry.latency:
                                new_ad = RoutePacket(host, entry.latency)
                                self.send(new_ad, port, flood=False)
                                self.history[(host, port)] = new_ad
                        else:
                            new_ad = RoutePacket(host, entry.latency)
                            self.send(new_ad, port, flood=False)
                            self.history[(host, port)] = new_ad

                # business as usual
                else:
                    # 创建一个新的ad，包含主机和延迟
                    new_ad = RoutePacket(host, entry.latency)
                    self.send(new_ad, port, flood=False)


    def expire_routes(self):
        """
        Clears out expired routes from table.
        accordingly.
        """
        # TODO: fill this in!
        hosts = list(self.table.keys())
        for host in hosts:
            table_entry = self.table[host]
            # print(table_entry.expire_time)
            if table_entry.expire_time == FOREVER:
                continue

            # route is poison and expired
            if self.POISON_EXPIRED and api.current_time() > table_entry.expire_time:
                current_route = self.table[host]
                poison_route = TableEntry(host, current_route.port, latency=INFINITY, expire_time=self.ROUTE_TTL)
                self.table[host] = poison_route

            # route is expired
            elif api.current_time() > table_entry.expire_time:
                del self.table[host]


    def handle_route_advertisement(self, route_dst, route_latency, port):
        """Called when the router receives a route advertisement from a neighbor.
        :param route_dst: the destination of the advertised route.
        :param route_latency: latency from the neighbor to the destination.
        :param port: the port that the advertisement arrived on.
        :return: nothing."""
        # TODO: fill this in!
        port_latency = self.ports.get_latency(port)
        new_latency = port_latency + route_latency
        new_expire_time = api.current_time() + self.ROUTE_TTL
        current_route = self.table.get(route_dst)
        new_route = TableEntry(dst=route_dst, port=port, latency=new_latency, expire_time=new_expire_time)

        # poison advertisement
        if route_latency >= INFINITY and current_route.port == port:
            current_expire_time = current_route.expire_time
            poison_route = TableEntry(dst=route_dst, port=port, latency=INFINITY, expire_time=current_expire_time)
            self.table[route_dst] = poison_route
            self.send_routes(force=False)
            return

        # if NO route currently exists, add/update the new route
        if not current_route:
            self.table[route_dst] = new_route
            self.send_routes(force=False)
            return

        # found a better route
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
        self.ports.add_port(port, latency)
        # TODO: fill in the rest!

        for host in self.table.keys():
            if self.SEND_ON_LINK_UP:
                new_ad = RoutePacket(host, self.table[host].latency)
                self.send(new_ad, port, flood=False)


    def handle_link_down(self, port):
        """
        Called by the framework when a link attached to this router does down.
        :param port: the port number used by the link.
        :returns: nothing.
        """
        self.ports.remove_port(port)
        # TODO: fill this in!
        for host in list(self.table.keys()):
            if self.table[host].port == port:
                if self.POISON_ON_LINK_DOWN:
                    # poison and immediately send any routes that need to be updated
                    poison_route = TableEntry(host, port, latency=INFINITY, expire_time=self.table[host].expire_time)
                    self.table[host] = poison_route
                    self.send_routes(force=False)

                # remove any routes that go through that link
                del self.table[host]










# Feel free to add any helper methods!
