# -*- coding: utf-8 -*-
from contextlib import contextmanager
import StringIO
import collections
import itertools

import lxml.etree as et
from decorator import decorator


SECOND = 'second'
MINUTE = 'minute'


def nested(method):
	@contextmanager
	def _nested (method, instance, *args, **kw):
		element = method(instance, *args, **kw)

		instance._element_stack.append(element)
		try:
			yield element
		finally:
			instance._element_stack.pop()

	return decorator(_nested, method)


def simple_element(tag):
	@nested
	def method (self):
		return et.SubElement(self._cur_element(), tag)

	return method

class XMLBuilder (object):
	def __init__ (self, xml_encoding='utf-8'):
		self._xml_encoding = xml_encoding
		self._xml_tree = None

		self._element_stack = collections.deque()

		self._arrivalphase_id_gen = itertools.count(start=1)

	def _cur_element (self):
		return self._element_stack[-1]

	def _subelement (self, *args, **kwargs):
		return et.SubElement(self._cur_element(), *args, **kwargs)

	def render (self, pretty_print=True):
		return et.tostring(self._xml_tree, xml_declaration=True, encoding=self._xml_encoding, pretty_print=pretty_print)

	@nested
	def init (self, loglevel='notice', dumptraffic=None, dtd_path="/usr/share/tsung/tsung-1.0.dtd"):
		base_xml = '<?xml version="1.0" encoding="%s"?><!DOCTYPE tsung SYSTEM "%s"><tsung></tsung>' % (self._xml_encoding, dtd_path)
		self._xml_tree = et.parse(StringIO.StringIO(base_xml))

		e_tsung = self._xml_tree.getroot()
		e_tsung.set('loglevel', loglevel)
		if dumptraffic:
			e_tsung.set('dumptraffic', dumptraffic)

		return e_tsung

	@nested
	def arrivalphase (self, duration, duration_unit):
		return self._subelement('arrivalphase', phase=str(self._arrivalphase_id_gen.next()), duration=str(duration), unit=duration_unit)

	request = simple_element('request')

	clients = simple_element('clients')

	def client (self, host="localhost", use_controller_vm='true', maxusers=60000, cpu=None, weight=None):
		e_client = self._subelement('client', host=host, use_controller_vm=use_controller_vm, maxusers=str(maxusers))
		if cpu:
			e_client.set('cpu', str(cpu))
		if weight:
			e_client.set('weight', str(weight))
		return e_client

	servers = simple_element('servers')

	def server (self, host, port=80, type='tcp'):
		return self._subelement('server', host=host, port=str(port), type=type)

	def thinktime (self, value, random=False):
		return self._subelement('thinktime', value=str(value), random=('true' if random else 'false'))

	@nested
	def load (self, duration=None, unit=None):
		element = self._subelement('load')
		if duration:
			element.set('duration', str(duration))
			element.set('unit', unit)
		return element

	def users (self, **kwargs):
		return self._subelement('users', **kwargs)

	def dyn_variable (self, **kwargs):
		return self._subelement('dyn_variable', **kwargs)


	def setdynvars (self, var_names, **kwargs):
		@nested
		def _setdynvars (self):
			return self._subelement('setdynvars', **kwargs)

		with _setdynvars(self) as el:
			for var_name in var_names:
				self._subelement('var', name=var_name)
		return el
	#~
	#~ def setdynvars (self, var_names, **kwargs):
		#~ with self._subelement('setdynvars', **kwargs) as el:
			#~ for var_name in var_names:
				#~ self._subelement('var', name=name)
		#~ return el

	options = simple_element('options')

	def set_default_options (self):
		e_option_user_agent = self._subelement('option', type='ts_http', name='user_agent')
		e_user_agent = et.SubElement(e_option_user_agent, 'user_agent', probability="100")
		e_user_agent.text = "tsung"

		# global thinktime between requests
		self._subelement('option', name='thinktime', value="0", random='false', override='false')

		self._subelement('option', name='hibernate', value='5')
		#~ self._subelement('option', name='hibernate', value='infinity')

	sessions = simple_element('sessions')

	@nested
	def session (self, name, probability=100, type='ts_http'):
		return self._subelement('session', name=name, probability=str(probability), type=type)

	@nested
	def transaction (self, name):
		return self._subelement('transaction', name=name)

	@nested
	def for_ (self, from_, to, incr=1, var="counter"):
		return self._subelement('for', to=str(to), incr=str(incr), var=var, **{'from': str(from_)})

	@nested
	def request (self, subst=False):
		return self._subelement('request', subst=('true' if subst else 'false'))

	@nested
	def http (self, url, method='GET', version='1.1'):
		return self._subelement('http', url=url, method=method, version=version)

	def http_header (self, name, value):
		return self._subelement('http_header', name=name, value=value)

	def www_authenticate (self, username, password):
		return self._subelement('www_authenticate', userid=username, passwd=password)

	def eval_into_dynvar (self, var_name, code):
		self.setdynvars([var_name], sourcetype='eval', code=code)

	@nested
	def foreach (self, name, in_):
		return self._subelement('foreach', name=name, **{'in': in_})
