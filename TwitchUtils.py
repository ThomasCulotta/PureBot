# True if user is a mod or the broadcaster
def CheckPriv(tags):
    return (tags["mod"] == 1 or
            tags["user-id"] == tags["room-id"])
