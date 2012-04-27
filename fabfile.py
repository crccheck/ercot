import os

from fabric.api import *

env.use_ssh_config = True
env.hosts = ['dh']

DATA_DIR = "download"
REMOTE_DATA_FILE = "conditions.tgz"


@task
def grab_files():
    print env

    project_root = os.path.dirname(env.real_fabfile)

    with lcd(project_root):
        local("mkdir -p %s" % DATA_DIR)

        print project_root
        with cd("ercot"):
            local_file = os.path.join(DATA_DIR, REMOTE_DATA_FILE)
            # archive remote files
            run("tar -czf %s *.html && rm *.html" % REMOTE_DATA_FILE)
            # download remote file
            get(REMOTE_DATA_FILE, local_file)
            # extract
            local("cd %s && tar -xzf %s" % (DATA_DIR, REMOTE_DATA_FILE))
            # delete compressed file
            local("mv -f %s /tmp" % local_file)


@task
def parse():
    import datetime
    import time
    from lxml.html import parse
    files = [os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR) if f[-4:] == 'html']
    outfile = open("test.csv", "w")
    for f in files:
        try:
            doc = parse(open(f, "r"))
            timestamp = doc.xpath("//span[@class='labelValueClass']")[0].text
            timestamp = timestamp.split(" ", 2)[2]
            created = datetime.datetime.strptime(timestamp, "%b %d %Y %H:%M:%S %Z")
            ctime = int(time.mktime(created.timetuple()))
            values = doc.xpath("//span[@class='labelValueClassBold']")
            demand = values[2].text
            capacity = values[3].text
            wind = values[4].text
            # TODO delete file after parsing
        except AssertionError:
            continue
        # print f, ctime
        # print timestamp, demand, capacity, wind
        outfile.write(", ".join((str(ctime), timestamp, demand, capacity, wind)))
        outfile.write("\n")
    outfile.close()
