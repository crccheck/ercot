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


# DEPRECATED
@task
def parse(days=None):
    import datetime
    from dateutil import parser
    import time
    from lxml.html import parse
    files = [os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR) if f[-4:] == 'html']
    outfile = open("test.csv", "w")
    header_written = False
    if days is not None:
        start = datetime.datetime.now() - datetime.timedelta(days=int(days))
    else:
        start = datetime.datetime.utcfromtimestamp(0)
    for f in files:
        try:
            doc = parse(open(f, "r"))
            timestamp = doc.xpath("//span[@class='labelValueClass']")[0].text
            timestamp = timestamp.split(" ", 2)[2]
            created = parser.parse(timestamp)
            if created < start:
                continue
            ctime = int(time.mktime(created.timetuple()))
            labels = [x.text for x in doc.xpath("//span[@class='labelValueClass']")[1:]]
            values = [x.text for x in doc.xpath("//span[@class='labelValueClassBold']")]
            data = zip(labels, values)
            # TODO delete file after parsing
        except AssertionError:
            continue
        #import ipdb; ipdb.set_trace()
        #break
        # print f, ctime
        if header_written is False:
            outfile.write("ctime,date," + ",".join(labels))
            outfile.write("\n")
            header_written = True
        outfile.write(",".join([str(ctime), timestamp] + values))
        outfile.write("\n")
    outfile.close()
