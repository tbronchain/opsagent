#!/usr/bin/env python

import os
import hashlib

from staterunner import StateRunner

class StatePrepareExcepton(Exception):
	pass

class StatePreparation(object):

	ssh_key_type = ['ecdsa', 'ssh-rsa', 'ssh-dss']

	requisity_map = {
		'pkg' : {
			'npm' 	: 'npm',
			'pecl'	: 'php-pear',
			'pip'	: 'python-pip',
		}
	}

	def __init__(self, pre_states):

		self.pre_mapping = {
			'package.apt.package'	:	self._package_apt_package,
			'package.yum.package'	:	self._package_yum_package,
			'package.gem.package'	:	self._package_gem_package,
			'package.npm.package'	:	self._package_npm_package,
			'package.pecl.package'	:	self._package_pecl_package,
			'package.pip.package'	:	self._package_pip_package,
			'package.zypper.package':	self._package_zypper_package,
			'package.yum.repo'		:	self._package_yum_repo,
			'package.apt.repo'		:	self._package_apt_repo,
			'package.gem.source'	:	self._package_gem_source,
			'path.file'				:	self._path_file,
			'path.dir'				:	self._path_dir,
			'path.symlink'			:	self._path_symlink,
			'scm.git'				:	self._scm_git,
			'scm.svn'				:	self._scm_svn,
			'scm.hg'				:	self._scm_hg,
			'service.supervisord'	:	self._service_supervisord,
			'service.sysvinit'		:	self._service_sysvinit,
			'service.upstart'		:	self._service_upstart,
			'sys.cmd'				:	self._sys_cmd,
			'sys.script'			:	self._sys_script,
			'sys.cron'				:	self._sys_cron,
			'sys.user'				:	self._sys_user,
			'sys.group'				:	self._sys_group,
			'sys.hostname'			:	self._sys_hostname,
			'sys.hosts'				:	self._sys_hosts,
			'sys.mount'				:	self._sys_mount,
			'sys.ntp'				:	self._sys_ntp,
			'sys.selinux'			:	self._sys_selinux,
			'system.ssh.auth'		:	self._system_ssh_auth,
			'system.ssh.known.host' :	self._system_ssh_known_host,
		}

		self.pre_states = pre_states
		self.states = []

	def transfer(self):
		"""
			Transfer the agent_data to salt states.
		"""

		for uid, com in self.pre_states['component'].items():
				states = {}

				for p_state in com['state']:

					step = p_state['stateid']

					if p_state['module'] in self.pre_mapping:

						state = self.pre_mapping[p_state['module']](p_state, uid, step)

						if state:
							if isinstance(state, dict) or isinstance(state, list):
								states[step] = state

							else:
								print "invalid state"
								continue

				# order the states
				for i in range(len(states.keys())):
					step = str(i+1)

					if isinstance(states[step], dict):
						self.states.append(states[step])

					elif isinstance(states[step], list):
						self.states += states[step]

		return self.states

	## package
	def _package_yum_package(self, p_state, uid=None, step=None):
		"""
			Transfer yum package to salt state.
		"""
		return self.__package(p_state, 'pkg', uid, step)

	def _package_apt_package(self, p_state, uid=None, step=None):
		"""
			Transfer apt package to salt state.
		"""
		return self.__package(p_state, 'pkg', uid, step)

	def _package_gem_package(self, p_state, uid=None, step=None):
		"""
			Transfer gem package to salt state.
		"""
		return self.__package(p_state, 'gem', uid, step)

	def _package_npm_package(self, p_state, uid=None, step=None):
		"""
			Transfer npm package to salt state.
		"""

		return self.__package(p_state, 'npm', uid, step)

	def _package_pecl_package(self, p_state, uid=None, step=None):
		"""
			Transfer pecl package to salt state.
		"""
		return self.__package(p_state, 'pecl', uid, step)

	def _package_pip_package(self, p_state, uid=None, step=None):
		"""
			Transfer pip package to salt state.
		"""
		return self.__package(p_state, 'pip', uid, step)

	def _package_zypper_package(self, p_state, uid=None, step=None):
		"""
			Transfer zypper package to salt state.
		"""
		return self.__package(p_state, 'zypper', uid, step)

	def __package(self, p_state, type, uid=None, step=None):
		"""
			Transfer package to salt state.
		"""
		pkg_state = []

		# check
		if not isinstance(p_state, dict) or 'parameter' not in p_state or 'name' not in p_state['parameter']:
			print "invalid preparation states"
			return pkg_state

		if self.__state_check('package', type) != 0:
			print "invalid package type"
			return 2

		state_mapping = {
			'installed' : [],
			'latest'	: [],
		}
		addin = {}

		# add requisity
		req = {}
		requisities = []
		req_state = None
		req_module = 'pkg'
		if type in ['npm', 'pecl', 'pip']:
			req_state = self.__get_requisity(req_module, type)
			if req_state:
				req_tag = req_state.keys()[0]
				requisities.append({req_module:req_tag})

				pkg_state.append(req_state)

		# get package name and verson
		for attr, value in p_state['parameter'].items():
			if not value: continue

			if attr == 'name':
				for name, version in value.items():
					if version:
						state_mapping['installed'].append({name:version})
					else:
						state_mapping['latest'].append(name)

			else:

				addin[attr] = value

				if attr == 'verify_gpg':
					addin[attr] = True if value == 'True' else False

		for state, packages in state_mapping.items():
			if not packages: continue

			pkgs = {
				'pkgs' : packages
			}

			# requisity
			if requisities:
				addin['require'] = requisities

			# addin properties
			if addin:
				pkgs.update(addin)

			tag = self.__get_tag(p_state['module'], uid, step, 'pkgs', state)

			pkg_state.append(
				{
					tag : {
						'pkg' : [
							pkgs,
							state,
						]
					}
				}
			)

		return pkg_state

	## repo, source
	def _package_yum_repo(self, p_state, uid=None, step=None):
		"""
			Transfer yum repository to salt state.
		"""
		return self.__repo(p_state, 'yum', uid, step)

	def _package_apt_repo(self, p_state, uid=None, step=None):
		"""
			Transfer apt repository to salt state.
		"""
		return self.__repo(p_state, 'apt', step)

	def _package_gem_source(self, p_state, uid=None, step=None):
		"""
			Transfer gem source to salt state.
		"""
		return self.__repo(p_state, 'gem', step)

	def __repo(self, p_state, type, uid=None, step=None):
		"""
			Transfer repository to salt state.
		"""

		# check
		if not isinstance(p_state, dict) or 'parameter' not in p_state or 'name' not in p_state['parameter']:
			print "invalid preparation states"
			return 1

		if self.__state_check('repository', type) != 0:
			print "invalid repository type"
			return 2

		repo_state = None
		state = None

		# file
		if type in ['apt', 'yum']:
			filename = p_state['parameter']['name']
			content  = p_state['parameter']['content']
			if type == 'apt':
				if not filename.endswith('.list'):
					filename += '.list'
				path = '/etc/apt/sources.list.d/' + filename
			else:
				if not filename.endswith('repo'):
					filename += '.repo'
				path = '/etc/yum.repos.d/' + filename

			state = 'managed'

			tag = self.__get_tag('path.file', uid, step, path, state)

			repo_state = {
				path	:	{
					'file'	:	[
						state,
						{
							'user'		:	'root',
							'group'		:	'root',
							'mode'		:	'644',
							'content'	:	content,
						}
					]
				}
			}

		##elif type == 'gem':
		##elif type == 'zypper'

		return repo_state

	## file, directory, symlink
	def _path_file(self, p_state, uid=None, step=None):
		"""
			Transfer file to salt state.
		"""
		return self.__file(p_state, 'file', uid, step)

	def _path_dir(self, p_state, uid=None, step=None):
		"""
			Transfer directory to salt state.
		"""
		return self.__file(p_state, 'directory', uid, step)

	def _path_symlink(self, p_state, uid=None, step=None):
		"""
			Transfer symlink to salt state.
		"""
		return self.__file(p_state, 'symlink', uid, step)

	def __file(self, p_state, type, uid=None, step=None):
		# check
		if not isinstance(p_state, dict) or 'parameter' not in p_state:
			print "invalid preparation states"
			return 1

		if self.__state_check('file', type) != 0:
			print "invalid file type"
			return 2

		## file path check

		addin = {}
		filename = None

		for attr, value in p_state['parameter'].items():
			if not value: continue

			if attr == 'path':
				addin['name'] = filename = value

			else:
				if type == 'symlink' and attr == 'source':
					attr = 'name'

				addin[attr] = value

		if not addin or not filename:
			print "invalid parameters"
			return 3

		state = type
		if type == 'file':
			state = 'managed'

		tag = self.__get_tag(p_state['module'], uid, step, filename, state)

		file_state = {
			tag : {
				'file' : [
					state,
					addin,
				]
			}
		}

		return file_state

	## scm
	def __scm(self, p_state, type, uid=None, step=None):
		"""
			Transfer scm to salt state.
		"""
		# check
		if not isinstance(p_state, dict) or 'parameter' not in p_state:
			print "invalid preparation states"
			return 1

		if self.__state_check('scm', type) != 0:
			print "invalid scm type"
			return 2

		state = 'latest'

		addin = {}
		scm_dir_addin = {}
		repo = None

		for attr, value in p_state['parameter'].items():
			if not value:	continue

			if attr == 'repo':
				addin['name'] = repo = value.split('-')[1].strip()

			elif attr == 'branch':
				if type == 'git':
					addin['rev'] = value

			elif attr == 'revision':
				addin['rev'] = value

			elif attr == 'path':
				addin['target'] = value

			elif attr == 'user':
				addin['user'] = value
				scm_dir_addin['user'] = value

			elif attr == 'force':
				addin['force_checkout'] = True if value == 'True' else False

			elif attr == 'group':
				scm_dir_addin['group'] = value

			elif attr == 'mode':
				scm_dir_addin['mode'] = value

			else:
				if type == 'git':
					if attr == 'version':
						addin['rev'] = value
					elif attr == 'ssh-key':
						addin['identity'] = value
					#else:
						## invalid attributes

				elif type == 'svn':
					if attr in ['username', 'password']:
						addin[attr] = value
					#else:
						## invalid attributes

				#elif type == 'hg':
					## invalid attributes

		if not addin or not repo:
			print "invalid parameters"
			return 3

		scm_states = []

		# add directory state
		scm_dir_state = 'file'
		requisities = []
		if addin['target'] and scm_dir_addin:
			scm_dir_addin['recurse'] = scm_dir_addin.keys()
			scm_dir_addin['name'] = addin['target']
			dir_state = 'directory'

			scm_dir_tag = self.__get_tag('path.dir', uid, step, addin['target'], dir_state)

			dir_scm_state = {
				scm_dir_tag : {
					scm_dir_state : [
						dir_state,
						scm_dir_addin,
					]
				}
			}

			scm_states.append(dir_scm_state)

			requisities.append({scm_dir_state:scm_dir_tag})

		# add requirity
		if requisities:
			addin['require_in'] = requisities

		tag = self.__get_tag(p_state['module'], uid, step, repo, state)
		scm_state =	{
			tag : {
				type : [
					state,
					addin,
				]
			}
		}

		scm_states.append(scm_state)

		return scm_states

	def _scm_git(self, p_state, uid=None, step=None):
		"""
			Transfer git repo to salt state.
		"""
		return self.__scm(p_state, 'git', uid, step)

	def _scm_svn(self, p_state, uid=None, step=None):
		"""
			Transfer svn repo to salt state.
		"""
		return self.__scm(p_state, 'svn', uid, step)

	def _scm_hg(self, p_state, uid=None, step=None):
		"""
			Transfer hg repo to salt state.
		"""
		return self.__scm(p_state, 'hg', uid, step)

	## service
	def __service(self, p_state, type):
		"""
			Transfer service to salt state.
		"""

		# check
		if not isinstance(p_state, dict) or 'parameter' not in p_state:
			print "invalid preparation states"
			return 1

		if self.__state_check('service', type) != 0:
			print "invalid service state"
			return 2

		state = 'running'
		if type in ['sysvinit', 'upstart']:
			type = 'service'

		addin = {}
		srv_name = None
		for attr, value in p_state['parameter'].items():
			if not value: continue

			if attr == 'name':
				addin['name'] = srv_name = value

			elif attr == 'username':
				if type == 'supervisord':
					addin['user'] = username

			else:
				if attr == 'config':
					addin['conf_file'] = value
				elif attr == 'watch':
					if isinstance(value, list):
						addin['watch'] = value

		if not addin or not srv_name:
			print "invalid parameters"
			return 3

		tag = self.__get_tag(p_state['module'], uid, step, srv_name, state)
		srv_state = {
			tag : [
				state,
				addin
			]
		}

		return srv_state

	def _service_supervisord(self, p_state, uid=None, step=None):
		"""
			Transfer supervisord service to salt state.
		"""
		return self.__service(p_state, 'supervisord', uid, step)

	def _service_sysvinit(self, p_state, uid=None, step=None):
		"""
			Transfer sysvinit service to salt state.
		"""
		return self.__service(p_state, 'service', uid, step)

	def _service_upstart(self, p_state, uid=None, step=None):
		"""
			Transfer upstart service to salt state.
		"""
		return self.__service(p_state, 'service', uid, step)

	## sys
	def _sys_cmd(self, p_state, uid=None, step=None):
		"""
			Transfer system cmd to salt state.
		"""

		# check
		if not isinstance(p_state, dict) or 'parameter' not in p_state:
			print "invalid preparation states"
			return 1

		if self.__state_check('sys', 'cmd') != 0:
			print "invalid system command state"
			return 2

		addin = {}
		cmd = None
		for attr, value in p_state['parameter'].items():
			if not value: continue

			if attr == 'name' or attr == 'cmd':
				addin['name'] = cmd = value

			elif attr == 'bin':
				addin['shell'] = value

			elif attr in ['cwd', 'user', 'group', 'env', 'timeout']:
				addin[attr] = value

			#elif attr == 'with_path':
				##addin['onlyif'] = '' # only when path existed

			#elif attr == 'without_path':
				##addin['unless'] = '' # only when path not existed

		if not addin or not cmd:
			print "invalid parameters"
			return 3

		cmd_state = []
		# deal content
		if 'content' in p_state['parameter'] and p_state['parameter']['content']:
			cmd_file_addin = {'mode':'0755'}

			if 'user' in addin:
				cmd_file_addin['user'] = addin['user']

			if 'group' in addin:
				cmd_file_addin['group'] = addin['group']

			cmd_file_state = 'managed'
			cmd_file_tag = self.__get_tag('path.file', uid, step, addin['name'], cmd_file_state)

			file_cmd_state = {
				cmd_file_tag : {
					'file' : [
						cmd_file_state,
						cmd_file_addin,
					]
				}
			}

			cmd_state.append(file_cmd_state)

		# add require
		if cmd_state:
			addin['require'] = [ { 'file' : addin['name'] } ]

		# deal args
		if 'args' in p_state['parameter'] and p_state['parameter']['args']:
			addin['name'] += ' ' + p_state['parameter']['args']

		state = 'run'
		tag = self.__get_tag(p_state['module'], uid, step, cmd, state)

		cmd_state.append({
			tag : {
				'cmd' : [
					state,
					addin
				]
			}
		})

		return cmd_state

	def _sys_script(self, p_state, uid=None, step=None):
		"""
			Transfer system script to salt state.
		"""

		return self._sys_cmd(p_state, uid, step)

	def _sys_cron(self, p_state, uid=None, step=None):
		"""
			Transfer system cron to salt state.
		"""

		# check
		if not isinstance(p_state, dict) or 'parameter' not in p_state:
			print "invalid preparation states"
			return 1

		if self.__state_check('sys', 'cron') != 0:
			print "invalid system cron state"
			return 2

		addin = {}
		cron = None

		for attr, value in p_state['parameter'].items():
			if not value: continue

			if attr == 'cmd':
				addin['name'] = cron = value

			elif attr in ['minute', 'hour', 'month']:
				addin[attr] = value

			elif attr == 'day of month':
				addin['daymonth'] = value

			elif attr == 'day of week':
				addin['dayweek'] = value

			elif attr == 'username':
				addin['user'] = value

			#else:
				## invalid attributes

		if not addin or not cron:
			print "invalid parameters"
			return 3

		state = 'present'
		tag = self.__get_tag(p_state['module'], uid, step, cron, state)

		return {
			tag : {
				'cron' : [
					state,
					addin,
				]
			}
		}

	def _sys_user(self, p_state, uid=None, step=None):
		"""
			Transfer system username to salt state.
		"""

		# check
		if not isinstance(p_state, dict) or 'parameter' not in p_state:
			print "invalid preparation states"
			return 1

		if self.__state_check('sys', 'mount') != 0:
			print "invalid system state"
			return 2

		addin = {}
		user = None

		for attr, value in p_state['parameter'].items():
			if not value: continue

			if attr == 'username':
				addin['name'] = user = value

			elif attr == 'password':
				addin['password'] = value

			elif attr in ['fullname', 'uid', 'gid', 'shell', 'home', 'groups']:
				addin[attr] = value

			##elif attr == 'nologin':

		if not addin or not user:
			print "invalid parameters"
			return 3

		state = 'present'
		tag = self.__get_tag(p_state['module'], uid, step, user, state)

		return {
			tag : {
				'user' : [
					state,
					addin
				]
			}
		}

	def _sys_group(self, p_state, uid=None, step=None):
		"""
			Transfer system group to salt state.
		"""

		# check
		if not isinstance(p_state, dict) or 'parameter' not in p_state:
			print "invalid preparation states"
			return 1

		if self.__state_check('sys', 'group') != 0:
			print "invalid system group state"
			return 2

		addin = {}
		group = None

		for attr, value in p_state['parameter'].items():
			if not value: continue

			if attr == 'groupname':
				addin['name'] = group = value

			elif attr == 'gid':
				addin[attr] = value

			elif attr == 'system group':
				addin['system'] = True if value == 'True' else False

			#else:
				## invalid attributes

		if not addin or not group:
			print "invalid parameters"
			return 3

		state = 'present'
		tag = self.__get_tag(p_state['module'], uid, step, group, state)

		return {
			tag : {
				'group' : [
					state,
					addin
				]
			}
		}

	def _sys_hostname(self, p_state, uid=None, step=None):
		"""
			Transfer system hostname to salt state.
		"""

		# check
		if not isinstance(p_state, dict) or 'parameter' not in p_state:
			print "invalid preparation states"
			return 1

		if self.__state_check('sys', 'host') != 0:
			print "invalid system hostname state"
			return 2

		addin = {}
		host = p_state['parameter']['hostname']
		ip = p_state['']

		for attr, value in p_state['parameter'].items():
			if not value: continue

			if attr == 'hostname':
				host = value

			elif attr == 'ip':
				addin['ip'] = value

			#else:
				## invalid attributes

		if not addin or not host:
			print "invalid parameters"
			return 3

		return {
			host : {
				'host' : [
					'present',
					addin
				]
			}
		}

	def _sys_hosts(self, p_state, uid=None, step=None):
		"""
			Transfer system hosts to salt state.
		"""

		# check
		if not isinstance(p_state, dict) or 'parameter' not in p_state:
			print "invalid preparation states"
			return 1

		if self.__state_check('sys', 'host') != 0:
			print "invalid system hostname state"
			return 2

		if not p_state['parameter']['content']:
			print "invalid parameters"
			return 3

		name = '/etc/hosts'
		state = 'managed'
		tag = self.__get_tag('path.file', uid, step, name, state)

		hosts_state = {
			tag	:	{
				'file'	: [
					state,
					{
						'name'		:	name,
						'user'		:	'root',
						'group'		:	'root',
						'mode'		:	'0644',
						'contents'	:	p_state['parameter']['content'],
					}
				]
			}
		}

		return hosts_state

	def _sys_mount(self, p_state, uid=None, step=None):
		"""
			Transfer system mount to salt state.
		"""

		# check
		if not isinstance(p_state, dict) or 'parameter' not in p_state:
			print "invalid preparation states"
			return 1

		if self.__state_check('sys', 'mount') != 0:
			print "invalid system state"
			return 2

		addin = {}
		mount = None

		for attr, value in p_state['parameter'].items():
			if not value: continue

			if attr == 'path':
				addin['name'] = mount = value

			elif attr == 'dev':
				addin['device'] = value

			elif attr == 'filesystem':
				addin['fstype'] = value

			elif attr == 'dump':
				addin['dump'] = atoi(value)

			elif attr == 'passno':
				addin['pass_num'] = atoi(value)

			elif attr == 'args':
				addin['opts'] = value

		if not addin or not mount:
			print "invalid parameters"
			return 3

		state = 'mounted'
		tag = self.__get_tag(p_state['module'], uid, step, mount, state)

		return {
			tag : {
				'mount' : [
					state,
					addin
				]
			}
		}

	def _sys_ntp(self, p_state, uid=None, step=None):
		"""
			Transfer system ntp to salt state.
		"""
		# check
		if not isinstance(p_state, dict) or 'parameter' not in p_state:
			print "invalid preparation states"
			return 1

		if self.__state_check('sys', 'ntp') != 0:
			print "invalid system state"
			return 2

		addin = {}
		ntp = None

	def _sys_selinux(self, p_state, uid=None, step=None):
		"""
			Transfer system selinux to salt state.
		"""

		# check
		if not isinstance(p_state, dict) or 'parameter' not in p_state:
			print "invalid preparation states"
			return 1

		if self.__state_check('sys', 'selinux') != 0:
			print "invalid system state"
			return 2

		selinuxname = None

		if selinuxname:

			return {
				selinuxname : {
					'selinux' : [
						'boolean',
						{
							'value' : True if p_stata['parameter']['on'] == 'True' else False
						}
					]
				}
			}

	## ssh
	def _system_ssh_auth(self, p_state, uid=None, step=None):
		"""
			Transfer SSH authorized_key to salt state.
		"""

		# check
		if not isinstance(p_state, dict) or 'parameter' not in p_state:
			print "invalid preparation states"
			return 1

		if self.__state_check('sys', 'ssh_auth') != 0:
			print "invalid system SSH authorized_key state"
			return 2

		addin = {}
		authname = None

		for attr, value in p_state['parameter'].items():
			if not value: continue

			if attr == 'authname':
				addin['name'] = authname = value

			elif attr == 'username':
				addin['user'] = value

			elif attr == 'filename':
				addin['config'] = value

			elif attr == 'encrypt_algorithm':
				if value in ssh_key_type:
					addin['enc'] = value

			#elif attr == 'content':
				## generate the source file with content
				# salt://ssh_keys/<authname>.id_rsa.pub
				#addin['source'] = 'salt://ssh_keys/' + authname + '.id_rsa.pub'

		if not addin or not authname:
			print "invalid parameters"
			return 3

		state = 'present'
		tag = self.__get_tag(p_state['module'], uid, step, authname, state)

		return {
			tag : {
				'ssh_auth' : [
					state,
					addin,
				]
			}
		}

	def _system_ssh_known_host(self, p_state, uid=None, step=None):
		"""
			Transfer system SSH known_hosts to salt state.
		"""

		# check
		if not isinstance(p_state, dict) or 'parameter' not in p_state:
			print "invalid preparation states"
			return 1

		if self.__state_check('sys', 'ssh_known_hosts') != 0:
			print "invalid system SSH known_hosts state"
			return 2

		addin = {}
		known_hosts = None

		for attr, value in p_state['parameter'].items():
			if not value: continue

			if attr == 'hostname':
				addin['name'] = known_hosts = value

			elif attr == 'username':
				addin['user'] = value

			elif attr == 'filename':
				addin['config'] = value

			elif attr == 'fingerprint':
				addin[attr] = value

			elif attr == 'encrypt_algorithm':
				if value in ssh_key_type:
					addin[enc] = value

		if not addin or not known_hosts:
			print "invalid parameters"
			return 3

		state = 'present'
		tag = self.__get_tag(p_state['module'], uid, step, known_hosts, state)

		return {
			tag : {
				'ssh_known_hosts' : [
					state,
					addin,
				]
			}
		}

	def __get_tag(self, module, uid=None, step=None, name=None, state=None):
		"""
			generate state identify tag.
		"""

		if not isinstance(module, basestring):
			module = str(module)

		tag = module.replace('.', '_')

		if step:
			if not isinstance(step, basestring):
				step = str(step)
			tag = step + '_' + tag

		if uid:
			if not isinstance(step, basestring):
				uid = str(uid)
			tag = uid + '_' + tag

		if name:
			if not isinstance(name, basestring):
				name = str(name)
			tag += '_' + name

		if state:
			if not isinstance(state, basestring):
				state = str(state)
			tag += '_' + state

		tag = '_' + tag

		#return hashlib.md5(tag).hexdigest()
		return tag

	def __get_requisity(self, module, type):
		"""
			Generate requisity state.
		"""

		name = state = None

		if module == 'pkg':
			name = self.requisity_map[state][type]

			state = 'installed'

		if name and state:
			tag = self.__get_tag('base.'+module, None, None, name, state)

			return {
				tag : {
					module : [
						{
							'name' : name
						},
						state,
					]
				}
			}

	def __state_check(self, state, type):
		"""
			Check state type.
		"""
		type_map = {
			'package'		: ['pkg', 'gem', 'npm', 'pecl', 'pip'],
			'repository'	: ['apt', 'yum', 'gem', 'zypper'],
			'file'			: ['file', 'directory', 'symlink'],
			'scm' 			: ['git', 'svn', 'hg'],
			'service'		: ['supervisord', 'sysvinit', 'upstart'],
			'sys'			: ['cmd', 'cron', 'group', 'host', 'mount', 'ntp', 'selinux', 'user', 'ssh_auth', 'ssh_known_hosts']
		}

		if state not in type_map.keys() or type not in type_map[state]:
			print "not supported type %s in %s state" % (type, state)
			return 2

		return 0

# codes for test
def main():

	import json

	pre_states = json.loads(open('api.json').read())

	salt_opts = {
		'file_client':       'local',
		'renderer':          'yaml_jinja',
		'failhard':          False,
		'state_top':         'salt://top.sls',
		'nodegroups':        {},
		'file_roots':        {'base': ['/srv/salt']},
		'state_auto_order':  False,
		'extension_modules': '/var/cache/salt/minion/extmods',
		'id':                '',
		'pillar_roots':      '',
		'cachedir':          '/code/OpsAgent/cache',
		'test':              False,
	}

	sp = StatePreparation(pre_states)
	states = sp.transfer()

	print json.dumps(states)

	runner = StateRunner(salt_opts, states)
	print json.dumps(runner.get_opts(), sort_keys=True,
		  indent=4, separators=(',', ': '))

	ret = runner.run()
	if ret:
		print json.dumps(ret, sort_keys=True,
			  indent=4, separators=(',', ': '))
	else:
		print "wait failed"

if __name__ == '__main__':
	main()