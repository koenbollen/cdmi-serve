# Koen Bollen <meneer koenbollen nl>
# 2010 GPL

system = {

        # These features lay outside the scope of this
        # project:
        "domains": False,
        "notification": False,
        "query": False,
        "queue": False,

        # Random choices, just for testing and the set
        # a bound:
        "metadata_maxitems": 4096,
        "metadata_maxsize": 1024,

        # Really only supporting CDMI:
        "export_webdav": False,

        # Got these:
        "size": True,
        "ctime": True,
        "atime": True,
        "mtime": True,
        "hash": False, # not yet
        "acl": False,
    }

dataobject = {

        # Support of most common operations
        # including random access IO:
        "read_value": True,
        "read_value_range": True,
        "read_metadata": True,
        "modify_value": True,
        "modify_value_range": True,
        "modify_metadata": True,
        "delete_dataobject": True,
        "serialize_dataobject": False,
        "deserialize_dataobject": False,
    }

container = {
        "list_children": True,
        "list_children_range": True,
        "read_metadata": True,
        "modify_metadata": True,
        "snapshot": False,
        "create_dataobject": True,
        "post_dataobject": False, # not yet
        "create_container": True,
        "delete_container": True,
        "move_container": True,
        "copy_container": True,
    }


# These paths aren't dynamic, if they change the
# method get_capabilities should be updated aswell.
paths = {
        "/": dict([("cdmi_"+k,v) for k,v in system.items()]),
        "/dataobject": dict([("cdmi_"+k,v) for k,v in dataobject.items()]),
        "/container": dict([("cdmi_"+k,v) for k,v in container.items()]),
    }



# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=79:

