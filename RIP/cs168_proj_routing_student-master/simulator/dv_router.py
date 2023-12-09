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
        self.last_table = Table()
        self.last_table.owner = self

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

    def send_single(self, force=False, port=None):
        """
        Send route advertisements for a single port in the table
        Do NOT update last_table.
        """
        assert port is not None

        for destination, current_entry in self.table.items():
            # Calculate current latency based on the conditions
            if (current_entry.port != port) or (not self.POISON_REVERSE):
                current_latency = current_entry.latency
            else:
                current_latency = INFINITY

            # Check if force is not True and there's a previous entry for the destination
            if not force and destination in self.last_table:
                last_entry = self.last_table[destination]
                # Calculate last latency based on the conditions
                if (last_entry.port != port) or (not self.POISON_REVERSE):
                    last_latency = last_entry.latency
                else:
                    last_latency = INFINITY

                # Skip if last latency is the same as current latency
                if last_latency == current_latency:
                    continue

            # Check if SPLIT_HORIZON is not enabled or the port is different from the current entry's port
            if (not self.SPLIT_HORIZON) or (port != current_entry.port):
                # Send route advertisement
                self.send_route(port=port, dst=destination, latency=current_latency)
        
    def send_routes(self, force=False, single_port=None):
        """
        Send route advertisements for all routes in the table and update last_table

        :param force: if True, advertises ALL routes in the table;
                      otherwise, advertises only those routes that have
                      changed since the last advertisement.
               single_port: if not None, sends updates only to that port; to
                            be used in conjunction with handle_link_up.
        :return: nothing.
        """
        if single_port:
            print("Single Port not Yet.")
        else:
            for port in self.ports.get_all_ports():
                # self.send_single(force, port)
                for destination, current_entry in self.table.items():
                    # Calculate current latency based on the conditions
                    if (current_entry.port != port) or (not self.POISON_REVERSE):
                        current_latency = current_entry.latency
                    else:
                        current_latency = INFINITY

                    # Check if force is not True and there's a previous entry for the destination
                    if (not force) and (destination in self.last_table):
                        last_entry = self.last_table[destination]
                        # Calculate last latency based on the conditions
                        if (last_entry.port != port) or (not self.POISON_REVERSE):
                            last_latency = last_entry.latency
                        else:
                            last_latency = INFINITY

                        # Skip if last latency is the same as current latency
                        if last_latency == current_latency:
                            continue

                    # Check if SPLIT_HORIZON is not enabled or the port is different from the current entry's port
                    if (not self.SPLIT_HORIZON) or (port != current_entry.port):
                        # Send route advertisement
                        self.send_route(port=port, dst=destination, latency=current_latency)    
                        
        self.last_table = self.table
        self.table = Table(self.last_table)
        assert id(self.last_table) != id(self.table)
        

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

            # route is poison and expired
            if self.POISON_EXPIRED and api.current_time() > table_entry.expire_time:
                current_route = self.table[host]
                poison_route = TableEntry(host, current_route.port, latency=INFINITY, expire_time=self.ROUTE_TTL)
                self.table[host] = poison_route

            # route is expired
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
        # Add the port to the router's list of ports with its associated latency.
        self.ports.add_port(port, latency)

        # If SEND_ON_LINK_UP flag is enabled, send all routes to the new neighbor on the specified port.
        if self.SEND_ON_LINK_UP:
            self.send_routes(force=True, single_port=port)

    def handle_link_down(self, port):
        """
        Called by the framework when a link attached to this router goes down.

        :param port: the port number used by the link.
        :returns: nothing.
        """
        # Iterate over all destinations in the routing table.
        for host in list(self.table.keys()):
            # Check if the route goes through the link that went down (matching port).
            if self.table[host].port == port:
                # If POISON_ON_LINK_DOWN flag is enabled, poison and immediately send updates for affected routes.
                if self.POISON_ON_LINK_DOWN:
                    # Create a poison route and replace it in the routing table for the specific destination.
                    poison_route = TableEntry(host, port, latency=INFINITY, expire_time=self.table[host].expire_time)
                    self.table[host] = poison_route
                    # Send the poisoned routes to notify other routers of the changes.
                    self.send_routes(force=False)

                # Remove any routes that go through the link that went down.
                del self.table[host]