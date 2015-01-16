""" Provides helpful stuff for discoverables. """


class BaseDiscoverable(object):
    """ Base class for discoverable services or device types. """

    def is_discovered(self):
        """ Returns True if it is discovered. """
        return len(self.get_entries()) > 0

    def get_info(self):
        """
        Return a list with the important info for each item.
        Uses self.info_from_entry internally.
        """
        return [self.info_from_entry(entry) for entry in self.get_entries()]

    # pylint: disable=no-self-use
    def info_from_entry(self, entry):
        """ Return an object with important info from the entry. """
        return entry

    # pylint: disable=no-self-use
    def get_entries(self):
        """ Returns all the discovered entries. """
        return []


class SSDPDiscoverable(BaseDiscoverable):
    """ uPnP discoverable base class. """

    def __init__(self, netdis):
        self.netdis = netdis

    def get_info(self):
        """ Gets most important info, by default the description location. """
        return list(set(
            entry.values['location'] for entry in self.get_entries()))

    # Helper functions

    # pylint: disable=invalid-name
    def find_by_st(self, st):
        """ Find entries by ST (the device identifier). """
        return self.netdis.ssdp.find_by_st(st)

    def find_by_device_description(self, values):
        """ Find entries based on values from their description. """
        return self.netdis.ssdp.find_by_device_description(values)


class MDNSDiscoverable(BaseDiscoverable):
    """ mDNS Discoverable base class. """

    def __init__(self, netdis, typ):
        self.netdis = netdis
        self.typ = typ
        self.services = {}

        netdis.mdns.register_service(self)

    def reset(self):
        """ Reset found services. """
        self.services.clear()

    def is_discovered(self):
        """ Returns True if any device has been discovered. """
        return len(self.services) > 0

    # pylint: disable=unused-argument
    def remove_service(self, zconf, typ, name):
        """ Callback when a service is removed. """
        self.services.pop(name, None)

    def add_service(self, zconf, typ, name):
        """ Callback when a service is found. """
        service = None
        tries = 0
        while service is None and tries < 3:
            service = zconf.get_service_info(typ, name)
            tries += 1

        if service is not None:
            self.services[name] = service

    def get_entries(self):
        """ Return all found services. """
        return self.services.values()

    def info_from_entry(self, entry):
        """ Returns most important info from mDNS entries. """
        return (self.ip_from_host(entry.server), entry.port)

    def ip_from_host(self, host):
        """
        Attempts to return the ip address from an mDNS host.
        Returns host if failed.
        """
        ips = self.netdis.mdns.zeroconf.cache.entries_with_name(host.lower())

        return repr(ips[0]) if ips else host
