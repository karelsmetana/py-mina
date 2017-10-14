"""
Setup tasks
"""


from __future__ import with_statement
import timeit
import os
import re
from py_mina.config import fetch, ensure, check_config
from fabric.api import run, settings, env, cd, hide
from py_mina.echo import *


################################################################################
# Check
################################################################################


def check_setup_config():
	"""
	Checks required config settings for setup task
	"""

	check_config(['user', 'hosts', 'deploy_to'])


################################################################################
# Create required and shared 
################################################################################


def create_required_structure():
	"""
	Creates required folders (tmp, releases, shared) in `deploy_to` path
	"""

	ensure('deploy_to')

	echo_subtask('Creating required structure')

	run('mkdir -p %s' % fetch('deploy_to'))

	for required_path in ['shared', 'releases', 'tmp']:
		run('mkdir -p %s' % os.path.join(fetch('deploy_to'), required_path))


def create_shared_paths():
	"""
	Creates shared dirs and touches shared files
	"""
	
	ensure('shared_path')
	ensure('shared_dirs')
	ensure('shared_files')

	echo_subtask('Creating shared paths')

	shared_path = fetch('shared_path')

	with cd(shared_path):
		for sdir in fetch('shared_dirs'):
			run('mkdir -p %s' % sdir)

		for sfile in fetch('shared_files'):
			directory, filename_ = os.path.split(sfile)

			if directory: 
				run('mkdir -p %s' % directory)

			run('touch ' + sfile)
			run('chmod g+rx,u+rwx ' + sfile)

			recommendation_tuple = (env.host_string, os.path.join(shared_path, sfile))
			echo_status('\n=====> Don\'t forget to update shared file \n[%s] %s\n' % recommendation_tuple , error=True)


################################################################################
# SSH known hosts
################################################################################


def add_repo_to_known_hosts():
	"""
	Adds repository host to known hosts if possible
	"""

	maybe_repository = fetch('repository', default_value='')

	if maybe_repository and len(maybe_repository) > 0:
		# Parse repo host
		repo_host_array = re.compile('(@|://)').split(maybe_repository)
		repo_host_part = repo_host_array[-1] if len(repo_host_array) > 0 else ''
		repo_host_match = re.compile(':|\/').split(repo_host_part)
		repo_host = repo_host_match[0] if len(repo_host_match) > 0 else ''

		# Exit if no host
		if repo_host == '': return

		# Parse port
		repo_port_match = re.search(r':([0-9]+)', maybe_repository)
		repo_port = repo_port_match.group(1) if bool(repo_port_match) == True else 22

		echo_subtask('Adding repository to known hosts')

		add_to_known_hosts(repo_host, repo_port)


def add_host_to_known_hosts():
	"""
	Adds current host to the known hosts

	`fabric3` library sets to `env.host_string` current host where task is executed
	"""

	ensure('hosts')

	echo_subtask('Adding current host to known hosts')

	add_to_known_hosts(env.host_string, env.port)


def add_to_known_hosts(host, port):
	cmd = '''
if ! ssh-keygen -H -F {0} &>/dev/null; then
	ssh-keyscan -t rsa -p {1} -H {0} >> ~/.ssh/known_hosts
fi'''.format(host, port)

	with settings(hide('everything'), warn_only=True):
		run(cmd)


################################################################################
# Print
################################################################################


def print_verbose():
	"""
	TODO:

	=> what to show?

	"""

	pass


def print_setup_stats(task_name, **kwargs):
	if 'start_time' in kwargs:
		stop_time = timeit.default_timer()
		delta_time = stop_time - kwargs.get('start_time')
	else:
		delta_time = 0

	time_string = '(time: %s seconds)' % delta_time
	status_tuple = (task_name, time_string)

	if fetch('verbose') == True:
		print_verbose()

	if 'error' in kwargs:
		echo_comment(('\n[FATAL ERROR]\n\n%s' % kwargs.get('error')), error=True)
		echo_status(('\n=====> Task "%s" failed %s \n' % status_tuple), error=True)
	else:
		echo_status('\n=====> Task "%s" finished %s \n' % status_tuple)
	
