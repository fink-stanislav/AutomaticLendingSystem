
def list_from_file(filename):
    try:
        with open(filename) as f:
            lines = f.read().splitlines()
            return lines
    except Exception as e:
        print "Error: {}".format(e)
        return []
