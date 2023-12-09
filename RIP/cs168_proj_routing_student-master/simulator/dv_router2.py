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

    def update_forwarding_table(self):
        for port, peer_table in self.peer_tables.items():
            for host, entry in peer_table.items():
                if not host in self.table:
                    self.table[host] = TableEntry(host, port, self.link_latency[port] + entry.latency)
                else:
                    if self.table[host].latency > self.link_latency[port] + entry.latency:
                        self.table[host] = TableEntry(host, port, self.link_latency[port] + entry.latency)


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
        # 获取主机的IP地址和子网掩码
        
        self.peer_tables[port][host] = PeerTableEntry(host, 0, PeerTableEntry.FOREVER)
        self.update_forwarding_table()
        self.send_routes()


    def handle_data_packet(self, packet, in_port):
        """
        Called when a data packet arrives at this router.

        You may want to forward the packet, drop the packet, etc. here.

        :param packet: the packet that arrived.
        :param in_port: the port from which the packet arrived.
        :return: nothing.
        """
        # TODO: fill this in!
        if packet.dst in self.table and self.table[packet.dst].latency < INFINITY and self.table[packet.dst].port != in_port:
            self.send(packet, self.table[packet.dst].port)


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
        if force == True:
            for port in self.peer_tables:
                for host, entry in self.table.items():
                    if entry.port != port:
                        if entry.latency >= INFINITY:
                            route_packet = basics.RoutePacket(host, INFINITY)
                        else:
                            route_packet = basics.RoutePacket(host, entry.latency)
                        self.send(route_packet, port)

    def expire_routes(self):
        """
        Clears out expired routes from table.
        accordingly.
        """
        # TODO: fill this in!
        for port, table in self.peer_tables.items():
            for dst, entry in table.items():
                if api.current_time() > entry.expire_time:
                    table.pop(dst)
        self.update_forwarding_table()

    def handle_route_advertisement(self, route_dst, route_latency, port):
        """
        Called when the router receives a route advertisement from a neighbor.

        :param route_dst: the destination of the advertised route.
        :param route_latency: latency from the neighbor to the destination.
        :param port: the port that the advertisement arrived on.
        :return: nothing.
        """
        # TODO: fill this in!
        self.peer_tables[port][dst] = PeerTableEntry(dst, route_latency, api.current_time()+ROUTE_TTL)
        self.update_forwarding_table()
        self.send_routes()
        
    def handle_link_up(self, port, latency):
        """
        Called by the framework when a link attached to this router goes up.

        :param port: the port that the link is attached to.
        :param latency: the link latency.
        :returns: nothing.
        """
        self.ports.add_port(port, latency)

        # TODO: fill in the rest!
        for host, entry in self.table.items():
            packet = basics.RoutePacket(host, entry.latency)
            self.send(packet, port)
        
    def handle_link_down(self, port):
        """
        Called by the framework when a link attached to this router does down.

        :param port: the port number used by the link.
        :returns: nothing.
        """
        self.ports.remove_port(port)

        # TODO: fill this in!
        for host, entry in self.table.items():
            if entry.port == port:
                del self.table[host]
        del self.peer_tables[port]
        del self.link_latency[port]
        self.update_forwarding_table()
        self.send_routes()
    # Feel free to add any helper methods!
