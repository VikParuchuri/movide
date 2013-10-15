Movide
====================

Overview
---------------------
Movide is a student-centric learning platform.  Movide allows teachers to define skills for students to master, and then allows students and teachers to both create content and problems.  A built-in discussion system allows students and teachers to interact around the class materials.  Movide helps transition learning to a multi-party interaction where content can come from anywhere.  You can see it running at www.movide.com.

Movide was made with a few key design/architecture principles in mind.  Some of these have been adhered to a large degree, and others are still works in progress.

### Existing features
* Ease of use.
* Mobile friendliness.
* Ease of installation/development.
* Ease of deployment.  Included scripts can get you deployed in minutes.

### Works in progress
* Full testing.  Test coverage is at around 60% on the Python code, but Javascript tests need to be written.
* Ease of integrating new modules.  The pattern to add a new module needs to be regularized.
* Third party module integration.  There is no LTI support yet.
* Full documentation.  Documentation, both high level and inline comments, is still a work in progress.
* Full API.  The API is there (through `django-rest-framework`), and works, but it needs to be made more consistent.

A lot of this work in progress has been deferred up to now due to the newness of Movide.

Movide is currently offered under the AGPL license.  If you have a need for an alternate license, please contact vik@equirio.com.

Installation
---------------------

Installation is a very straightforward process:

```
git clone git@github.com:equirio/movide.git
cd movide
sudo xargs -a apt-packages.txt apt-get install

# Activate your virtualenv at this point if you are using one.
pip install -r requirements.txt

# Run database migrations.
python manage.py syncdb --settings=movide.settings --pythonpath=`pwd`
python manage.py migrate --settings=movide.settings --pythonpath=`pwd`
```

Usage
----------------------

In order to use movide, you need to run:

```
python manage.py runserver 127.0.0.1:8000 --settings=movide.settings --pythonpath=`pwd`
```

After starting up the server, you can visit `http://127.0.0.1:8000` in your browser to start using movide.

If you want to run background tasks, which include grade calculation and processing @ mentions in discussions, you need to run:

```
python manage.py celeryd -B --settings=movide.settings --pythonpath=`pwd`
```

You don't have to run celery if you don't want to, but you will be unable to use certain features.

Contributing
------------------------

Contributions are very welcome.  Please contact vik@equirio.com if you have any questions about how to contribute.

Deployment
------------------------

Deployment scripts for movide can be found in the `deployment` directory.

### Create the movide stack
1.  Register for an AWS Account if you don't have one already.
2.  Select cloudformation in the AWS console, and load the `deployment/cloudformation/movide.json` template.  This template will create a web server to run movide, and a load balancer.  Choose a keypair that you have access to.
3.  A database is not included in the stack.  You can either create one separately, or opt to use a local database later on.

### Setup deployment
1.  Install the ansible requirements in `deployment/requirements.txt`.
2.  Edit `deployment/secrets/files/movide_deploy.template` to contain an SSH private key that can access your github, and rename it to `movide_depoy`.
3.  Edit `deployment/secrets/files/jim.key` to contain your public key, and rename it to `[YOUR NAME].key`.
4.  Edit `deployment/secrets/users/users.template` to have the right user, email, and key location, and rename it `users.yml`.
5.  Edit `deployment/secrets/users/movide_prod_vars.template` to point to your database.  If you want to use a local mysql database, edit database_host to point to the right spot.  Ensure that your auth config matches in terms of database name and password.  Rename it to `movide_prod_vars.yml`.
6.  Put a `.boto` file in your home directory (~) and make it look like the following:
````
[Credentials]
aws_access_key_id = [YOUR KEY]
aws_secret_access_key = [YOUR SECRET KEY]
```

### Deploy stack
1.  Go to `deployment/playbooks`.
2.  Do `ansible-playbook -vvv --user=[YOUR_USER]  mo_prod.yml -i ./ec2.py  -c ssh`
3.  If everything was setup properly, this should deploy your stack.  Visiting the `ELBAddress` from your cloudformation template outputs should now show you movide.