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
            local("tar -xzf %s" % local_file)
            # delete compressed file
            local("mv -f %s /tmp" % local_file)
