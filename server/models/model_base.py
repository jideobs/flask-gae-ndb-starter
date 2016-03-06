from google.appengine.ext import ndb
from google.appengine.datastore.datastore_query import Cursor
from google.appengine.api.datastore_errors import BadArgumentError, BadValueError
from flask import request
from flask_restful import abort
import datetime as main_datetime
import functools

DATE_FORMAT = '%Y-%m-%d'
DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
TIME_FORMAT = '%H:%M:%S'
DEFAULT_FETCH_LIMIT = 10

QUERY_FIELDS = 'query_fields'


class _EndpointsQueryInfo(object):
	"""A custom container for query information.

This will be set on an EndpointsModel (or subclass) instance, and can be used
in conjunction with alias properties to store query information, simple
filters, ordering and ancestor.

Uses an entity to construct simple filters, to validate ordering, to validate
ancestor and finally to construct a query from these filters, ordering and/or
ancestor.

Attributes:
	_entity: An instance of EndpointsModel or a subclass. The values from this
			will be used to create filters for a query.
	_filters: A set of simple equality filters (ndb.FilterNode). Utilizes the
			fact that FilterNodes are hashable and respect equality.
	_ancestor: An ndb Key to be used as an ancestor for a query.
	_cursor: A datastore_query.Cursor, to be used for resuming a query.
	_limit: A positive integer, to be used in a fetch.
	_order: String; comma separated list of property names or property names
			preceded by a minus sign. Used to define an order of query results.
	_order_attrs: The attributes (or negation of attributes) parsed from
			_order. If these can't be parsed from the attributes in _entity, will
			throw an exception.
	_query_final: A final query created using the orders (_order_attrs), filters
			(_filters) and class definition (_entity) in the query info. If this is
			not null, setting attributes on the query info object will fail.
"""

	def __init__(self, entity):
		"""Sets all internal variables to the default values and verifies entity.

Args:
	entity: An instance of EndpointsModel or a subclass.

Raises:
	TypeError: if entity is not an instance of EndpointsModel or a subclass.
"""
		if not isinstance(entity, EndpointsModel):
			raise TypeError('Query info can only be used with an instance of an '
			                'EndpointsModel subclass. Received: instance of %s.' %
			                (entity.__class__.__name__,))
		self._entity = entity

		self._filters = set()
		self._ancestor = None
		self._cursor = None
		self._limit = None
		self._order = None
		self._order_attrs = ()

		self._query_final = None

	def _PopulateFilters(self):
		"""Populates filters in query info by using values set on the entity."""
		entity = self._entity
		for prop in entity._properties.itervalues():
			current_value = prop._retrieve_value(entity)

			if prop._repeated:
				if current_value is not None:
					raise ValueError('No queries on repeated values are allowed.')
				continue

			# Only filter for non-null values
			if current_value is not None:
				self._AddFilter(prop == current_value)

	def SetQuery(self):
		"""Sets the final query on the query info object.

Uses the filters and orders in the query info to refine the query. If the
final query is already set, does nothing.
"""
		if self._query_final is not None:
			return

		self._PopulateFilters()

		# _entity.query calls the classmethod for the entity
		if self.ancestor is not None:
			query = self._entity.query(ancestor=self.ancestor)
		else:
			query = self._entity.query()

		for simple_filter in self._filters:
			query = query.filter(simple_filter)
		for order_attr in self._order_attrs:
			query = query.order(order_attr)

		self._query_final = query

	def _AddFilter(self, candidate_filter):
		"""Checks a filter and sets it in the filter set.

Args:
	candidate_filter: An NDB filter which may be added to the query info.

Raises:
	AttributeError: if query on the object is already final.
	TypeError: if the filter is not a simple filter (FilterNode).
	ValueError: if the operator symbol in the filter is not equality.
"""
		if self._query_final is not None:
			raise AttributeError('Can\'t add more filters. Query info is final.')

		if not isinstance(candidate_filter, ndb.FilterNode):
			raise TypeError('Only simple filters can be used. Received: %s.' %
			                (candidate_filter,))
		opsymbol = candidate_filter._FilterNode__opsymbol
		if opsymbol != '=':
			raise ValueError('Only equality filters allowed. Received: %s.' %
			                 (opsymbol,))

		self._filters.add(candidate_filter)

	@property
	def query(self):
		"""Public getter for the final query on query info."""
		return self._query_final

	def _GetAncestor(self):
		"""Getter to be used for public ancestor property on query info."""
		return self._ancestor

	def _SetAncestor(self, value):
		"""Setter to be used for public ancestor property on query info.

Args:
	value: A potential value for an ancestor.

Raises:
	AttributeError: if query on the object is already final.
	AttributeError: if the ancestor has already been set.
	TypeError: if the value to be set is not an instance of ndb.Key.
"""
		if self._query_final is not None:
			raise AttributeError('Can\'t set ancestor. Query info is final.')

		if self._ancestor is not None:
			raise AttributeError('Ancestor can\'t be set twice.')
		if not isinstance(value, ndb.Key):
			raise TypeError('Ancestor must be an instance of ndb.Key.')
		self._ancestor = value

	ancestor = property(fget=_GetAncestor, fset=_SetAncestor)

	def _GetCursor(self):
		"""Getter to be used for public cursor property on query info."""
		return self._cursor

	def _SetCursor(self, value):
		"""Setter to be used for public cursor property on query info.

Args:
	value: A potential value for a cursor.

Raises:
	AttributeError: if query on the object is already final.
	AttributeError: if the cursor has already been set.
	TypeError: if the value to be set is not an instance of
			datastore_query.Cursor.
"""
		if self._query_final is not None:
			raise AttributeError('Can\'t set cursor. Query info is final.')

		if self._cursor is not None:
			raise AttributeError('Cursor can\'t be set twice.')
		if not isinstance(value, datastore_query.Cursor):
			raise TypeError('Cursor must be an instance of datastore_query.Cursor.')
		self._cursor = value

	cursor = property(fget=_GetCursor, fset=_SetCursor)

	def _GetLimit(self):
		"""Getter to be used for public limit property on query info."""
		return self._limit

	def _SetLimit(self, value):
		"""Setter to be used for public limit property on query info.

Args:
	value: A potential value for a limit.

Raises:
	AttributeError: if query on the object is already final.
	AttributeError: if the limit has already been set.
	TypeError: if the value to be set is not a positive integer.
"""
		if self._query_final is not None:
			raise AttributeError('Can\'t set limit. Query info is final.')

		if self._limit is not None:
			raise AttributeError('Limit can\'t be set twice.')
		if not isinstance(value, (int, long)) or value < 1:
			raise TypeError('Limit must be a positive integer.')
		self._limit = value

	limit = property(fget=_GetLimit, fset=_SetLimit)

	def _GetOrder(self):
		"""Getter to be used for public order property on query info."""
		return self._order

	def _SetOrderAttrs(self):
		"""Helper method to set _order_attrs using the value of _order.

If _order is not set, simply returns, else splits _order by commas and then
looks up each value (or its negation) in the _properties of the entity on
the query info object.

We look up directly in _properties rather than using the attribute names
on the object since only NDB property names will be used for field names.

Raises:
	AttributeError: if one of the attributes in the order is not a property
			on the entity.
"""
		if self._order is None:
			return

		unclean_attr_names = self._order.strip().split(',')
		result = []
		for attr_name in unclean_attr_names:
			ascending = True
			if attr_name.startswith('-'):
				ascending = False
				attr_name = attr_name[1:]

			attr = self._entity._properties.get(attr_name)
			if attr is None:
				raise AttributeError('Order attribute %s not defined.' % (attr_name,))

			if ascending:
				result.append(+attr)
			else:
				result.append(-attr)

		self._order_attrs = tuple(result)

	def _SetOrder(self, value):
		"""Setter to be used for public order property on query info.

Sets the value of _order and attempts to set _order_attrs as well
by valling _SetOrderAttrs, which uses the value of _order.

If the passed in value is None, but the query is not final and the
order has not already been set, the method will return without any
errors or data changed.

Args:
	value: A potential value for an order.

Raises:
	AttributeError: if query on the object is already final.
	AttributeError: if the order has already been set.
	TypeError: if the order to be set is not a string.
"""
		if self._query_final is not None:
			raise AttributeError('Can\'t set order. Query info is final.')

		if self._order is not None:
			raise AttributeError('Order can\'t be set twice.')

		if value is None:
			return
		elif not isinstance(value, basestring):
			raise TypeError('Order must be a string.')

		self._order = value
		self._SetOrderAttrs()

	order = property(fget=_GetOrder, fset=_SetOrder)


class ModelBase(ndb.Model):
	def __init__(self, *args, **kwargs):
		super(ModelBase, self).__init__(*args, **kwargs)
		self._endpoints_query_info = _EndpointsQueryInfo(self)
		self._from_datastore = False

	@property
	def from_datastore(self):
		return self._from_datastore

	@classmethod
	def method(cls,
	           transform_request=False,
	           transform_fields=None,
	           user_required=False,
	           **kwargs):
		"""Creates an API method decorator.
		:param transform_request: Boolean; indicates whether or not
				a response data's ndb.Key value are to be returned,
				if True all ndb.Key values are used to get respective entity data,
				if False all ndb.Key are returned as urlsafe strings.
		:param transform_fields: An (optional) list or tuple that defines
				returned fields for ndb.Key value type in response data.
		:param user_required: Boolean; indicates whether or not a user is required on any incoming request.
		:return: A decorator that takes the metadata passed in and augments an API method.
		"""

		def request_to_entity_decorator(api_method):
			@functools.wraps(api_method)
			def entity_to_request_method(service_method, request):
				if user_required and utils.get_current_user() is None:
					abort(401, message='Invalid user.')
