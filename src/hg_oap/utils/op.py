import inspect
import itertools
import operator
from collections import defaultdict
from typing import Callable, Union, Sequence, Mapping, Any

__all__ = ('lazy', 'calc', 'ParameterOp', 'Expression', 'is_op')


def is_op(obj):
    return isinstance(obj, Op)


def make_op(obj):
    if isinstance(obj, Op):
        return obj
    if isinstance(obj, Item) and obj.__expression__ is not None:
        return obj.__expression__
    if isinstance(obj, (tuple, list, dict)):
        if len(obj) == 1 and find_op(item := next(iter(obj)), IterOp):
            return ComprehensionOp(type(obj),
                                   item if not isinstance(obj, dict) else KeyValueOp(next(iter(obj.items()))))
        else:
            return SequenceOp(obj)

    return ConstOp(obj)


def lazy(obj):
    return make_op(obj)


COMPARISON_OPERATOR_PRIORITY = 6


class Op:
    """
    Base class for an AST tree, representing an operation that can be performed.
    Exposes ability to "perform actions" that instead build an AST tree.
    Error reporting does not capture call stack when the node is originally evaluated.

    The idea is to allow the user to write behavior as though it were actually writing Python code, but
    instead we are building the tree of actions (AST) for later evaluation. The intention is that the ast will
    eventually be re-written into code that does in fact perform the intended operation.

    The AST can be stringify'd back into correct Python, then using eval the string would produce valid Python
    code representing the Python mirrors for the ``Op`` nodes.
    """

    def __init__(self, _priority: int):
        """
        Takes a ``_priority`` parameter that allows us to define the relative order of operations.
        This will be used to ensure that brackets are placed in the correct locations to ensure the correct
        order of evaluation of the operators defined priority.
        """
        self._priority: int = _priority
        # This is used to track when an operator has been involved in a chain boolean comparison, i.e.
        # are we in the state of ``a < op < b``, where the ``__compared__`` flags will be set on the a and op in this
        # scenario.
        self.__compared__: Op | None = None

    def __priority__(self):
        """The priority of this Op instance"""
        return self._priority

    def __is_const__(self):
        """Does this represent a constant value, i.e. has no computational element to it."""
        return False

    def __visit_operands__(self, fn: Callable[["Op"], tuple[Any, bool]]) -> Any:
        """
        This will visit the operands of this operator (the things that are associated to the Op, for example
        if the Op is ``+`` and the expression was ``a + b ``, then this will call the fn with ``a`` and then ``b``.
        The function (``fn``) will return the tuple of ``object`` and ``bool``, if the ``bool`` element is ``True``
        then the visit will continue on to the next operand, if ``False`` the ``object`` value will be returned
        and no further operands will be visited. If we run out of operands, and the function is still indicating
        continue, then the last result is returned. It is good practice to ensure the ``object`` returned when
        continuing is suitable to indicate that the visit failed to terminate.

        The ``object`` value is user defined (i.e. the responsibility of the ``fn``) and can return whatever the
        appropriate result would be (including None).

        For example: When trying to find an element in the AST, the ``__visit_operands__`` will be called with a ``fn``
        that returns the operator that is being searched for or ``None``.
        """
        raise NotImplementedError()

    def __transform__(self, fn=lambda x: x):
        """
        Supports transforming an ``Op`` instance from its current type to some other type as defined by the ``fn``.
        This is performed by applying the function to the same elements that would be visited in the
        ``__visit_operands__`` methods.

        This supports operations such as converting a tree of operands into say a single value. For example, if
        we had:

        a + lazy(1) + lazy(2)  ->   +(a, +(1, 2))

        We could convert the resultant Op hierarch with a + lazy(3)  -> +(a, 3)
        """
        raise NotImplementedError()

    def __getattr__(self, item: str):
        """
        If we are not accessing internal state (indicated with the __ prefix and suffix) we can then assume
        we are building the GetattrOp AST element.
        """
        if item.startswith('__') and item.endswith('__'):
            raise AttributeError

        return GetattrOp(self, item)

    def __getitem__(self, item):
        """This will construct the GetitemOp AST element."""
        return GetitemOp(self, item)

    def __call__(self, *args, **kwargs):
        """This will construct the CallOp AST element."""
        return CallOp(self, args, kwargs)

    def __reversed__(self):
        """This is not currently implemented"""
        return NotImplemented

    def __round__(self, n):
        """
        This will construct the BinaryOpSpecial AST element with a priority of 20 and supplying round as the
        standard python implementation.
        """
        return BinaryOpSpecial(20, self, n, round, _format="round({}, {})")

    # if sys.hexversion >= 0x03070000:
    #     def __mro_entries__(self, bases):
    #         return (self.__wrapped__,)

    def __lt__(self, other):
        """
        This will construct the BinaryOpReversible AST element, with a priority of 6 and self with the other as the
        binary parameters. The operator.lt is the standard Python implementation.
        To reverse this, we use the rhs > lhs lambda.
        """
        o = BinaryOpReversible(COMPARISON_OPERATOR_PRIORITY, self, other, operator.lt, '<',
                               lambda x: x._rhs > x._lhs)

        if lhs := self.__compared__:
            return ChainCompareOp(self, lhs, o)
        else:
            return o

    def __le__(self, other):
        o = BinaryOpReversible(COMPARISON_OPERATOR_PRIORITY, self, other, operator.le, '<=',
                               lambda x: x._rhs >= x._lhs)

        if lhs := self.__compared__:
            return ChainCompareOp(self, lhs, o)
        else:
            return o

    def __eq__(self, other):
        return BinaryOp(COMPARISON_OPERATOR_PRIORITY, self, other, operator.eq, '==')

    def __ne__(self, other):
        return BinaryOp(COMPARISON_OPERATOR_PRIORITY, self, other, operator.ne, '!=')

    def __gt__(self, other):
        return BinaryOpReversible(COMPARISON_OPERATOR_PRIORITY, self, other, operator.gt, '>',
                                  lambda x: x._rhs < x._lhs)

    def __ge__(self, other):
        return BinaryOpReversible(COMPARISON_OPERATOR_PRIORITY, self, other, operator.ge, '>=',
                                  lambda x: x._rhs <= x._lhs)

    def __hash__(self):
        return id(self)

    def __bool__(self):
        return FailedOp("Op is not booleanable")

    def __add__(self, other):
        return BinaryOp(11, self, other, operator.add, '+')

    def __sub__(self, other):
        return BinaryOp(11, self, other, operator.sub, '-')

    def __mul__(self, other):
        return BinaryOp(12, self, other, operator.mul, '*')

    def __truediv__(self, other):
        return BinaryOp(12, self, other, operator.truediv, '/')

    def __floordiv__(self, other):
        return BinaryOp(12, self, other, operator.floordiv, '//')

    def __mod__(self, other):
        return BinaryOp(12, self, other, operator.mod, '%')

    def __divmod__(self, other):
        return BinaryOpSpecial(-1, self, other, divmod, "divmod({}, {})")

    def __pow__(self, other, *args):
        return BinaryOp(14, self, other, operator.pow, '**')

    def __lshift__(self, other):
        return BinaryOp(10, self, other, operator.lshift, '<<')

    def __rshift__(self, other):
        return BinaryOp(10, self, other, operator.rshift, '>>')

    def __and__(self, other):
        return BinaryOp(9, self, other, operator.and_, '&')

    def __xor__(self, other):
        return BinaryOp(8, self, other, operator.xor, '^')

    def __or__(self, other):
        return BinaryOp(7, self, other, operator.or_, '|')

    def __radd__(self, other):
        return BinaryOp(11, other, self, operator.add, '+')

    def __rsub__(self, other):
        return BinaryOp(11, other, self, operator.sub, '-')

    def __rmul__(self, other):
        return BinaryOp(12, other, self, operator.mul, '*')

    def __rtruediv__(self, other):
        return BinaryOp(12, other, self, operator.truediv, '/')

    def __rfloordiv__(self, other):
        return BinaryOp(12, other, self, operator.floordiv, '//')

    def __rmod__(self, other):
        return BinaryOp(12, other, self, operator.mod, '%')

    def __rdivmod__(self, other):
        return BinaryOpSpecial(-1, other, self, divmod, "divmod({}, {})")

    def __rpow__(self, other, *args):
        return BinaryOp(14, other, self, operator.pow, '**')

    def __rlshift__(self, other):
        return BinaryOp(10, other, self, operator.lshift, '<<')

    def __rrshift__(self, other):
        return BinaryOp(10, other, self, operator.rshift, '>>')

    def __rand__(self, other):
        return BinaryOp(9, other, self, operator.and_, '&')

    def __rxor__(self, other):
        return BinaryOp(8, other, self, operator.xor, '^')

    def __ror__(self, other):
        return BinaryOp(7, other, self, operator.or_, '|')

    def __neg__(self):
        return UnaryOp(13, self, operator.neg, '-{}')

    def __pos__(self):
        return UnaryOp(13, self, operator.pos, '+{}')

    def __abs__(self):
        return UnaryOp(20, self, operator.abs, 'abs{}')

    def __invert__(self):
        return UnaryOp(13, self, operator.invert, '~{}')

    # def __contains__(self, value):  # converts any non-False return to True
    #     return BinaryOp(COMPARISON_OPERATOR_PRIORITY, self, value, operator.contains, '{1} in {0}')

    # def __enter__(self):
    # def __exit__(self, *args, **kwargs):

    def __iter__(self):
        return IterOp(self)

    def __copy__(self):
        raise NotImplementedError()

    def __deepcopy__(self, memo):
        raise NotImplementedError()

    def __reduce__(self):
        raise NotImplementedError()

    def __reduce_ex__(self, protocol):
        raise NotImplementedError()


class ConstOp(Op):

    def __init__(self, _value):
        super().__init__(_priority=18)
        self._value = _value
        if isinstance(_value, Item):
            _value.__expression__ = self

    def __is_const__(self):
        return True

    def __repr__(self):
        if isinstance(self._value, type):
            return self._value.__qualname__
        return repr(self._value) if not isinstance(self._value, str) else f"'{self._value}'"

    def __invoke__(self, *args, **kwargs):
        if isinstance(self._value, Item):
            self._value.__expression__ = None

        return self._value

    def __visit_operands__(self, fn):
        return fn(self._value)[0]

    def __transform__(self, fn=lambda x: x):
        return ConstOp(self._value)


class GetattrOp(Op):
    def __init__(self, _obj, _attr):
        super().__init__(16)
        self._obj = _obj
        self._attr = _attr

    def __repr__(self):
        return f"{repr_inner(self, self._obj)}.{self._attr}"

    def __invoke__(self, *args, **kwargs):
        obj = self._obj.__invoke__(*args, **kwargs)
        if isinstance(obj, FailedOp):
            return obj

        try:
            obj = getattr(obj, self._attr)
        except AttributeError as e:
            return FailedOp(f"{obj} does not have an attribute named {self._attr}", _cause=e)

        return obj

    def __visit_operands__(self, fn):
        r, c = fn(self._obj)
        return r

    def __transform__(self, fn=lambda x: x):
        return self.__class__(fn(self._obj), self._attr)


class UnaryOp(Op):
    def __init__(self, _priority, _obj, _op, _format):
        super().__init__(_priority=_priority)
        self._obj: Op = _obj
        self._op: Callable = _op
        self._format: str = _format

    def __repr__(self):
        if self._format:
            return self._format.format(repr_inner(self, self._obj))
        else:
            return f"{self._op.__name__}{repr_inner(self, self._obj)}"

    def __invoke__(self, *args, **kwargs):
        obj = self._obj.__invoke__(*args, **kwargs)
        if isinstance(obj, FailedOp):
            return obj

        return self._op(obj)

    def __visit_operands__(self, fn):
        r, c = fn(self._obj)
        return r

    def __transform__(self, fn=lambda x: x):
        return self.__class__(self._priority, fn(self._obj), self._op, self._format)


class BinaryOp(Op):
    """
    A binary operation takes a lhs and rhs operand as argument. These args are themselves Op instances or are
    convertable to Op instances using the ``make_op`` function.
    The ``_op`` parameter represent the standard python operator to execute when invoking the ``Op``.
    The ``_format`` string is used to depict the textual representation of this operator.
    """

    def __init__(self, _priority, _lhs, _rhs, _op, _format=None):
        super().__init__(_priority=_priority)
        self._lhs: Op = make_op(_lhs)
        self._rhs: Op = make_op(_rhs)
        self._op: Callable = _op
        self._format: str = _format

    def __repr__(self):
        if self._format:
            return f"{repr_inner(self, self._lhs)} {self._format} {repr_inner(self, self._rhs)}"
        else:
            return f"{repr_inner(self, self._lhs)} {self._op.__name__} {repr_inner(self, self._rhs)}"

    def __invoke__(self, *args, **kwargs):
        """
        First invokes the lhs operator, then the rhs operator, return the failure if either evaluation fails (using
        short-circuit logic). Finally, if both evaluate successfully the _op is called to evaluate the results.
        """
        lhs = self._lhs.__invoke__(*args, **kwargs)
        if isinstance(lhs, FailedOp):
            return lhs
        rhs = self._rhs.__invoke__(*args, **kwargs)
        if isinstance(rhs, FailedOp):
            return rhs

        return self._op(lhs, rhs)

    def __visit_operands__(self, fn):
        """Vist lhs, then rhs (if we are asked to continue), if not return the result from the lhs visit.
        If continue then we always return the result of the evaluation of fn on the rhs operand."""
        r, c = fn(self._lhs)
        if not c:
            return r
        r, c = fn(self._rhs)
        return r

    def __transform__(self, fn=lambda x: x):
        """
        Returns a new instance of this class (with this priority, this op and this format) with the results
        of applying ``fn`` to the ``lhs`` and ``rhs`` operands.
        """
        return self.__class__(self._priority, fn(self._lhs), fn(self._rhs), self._op, self._format)


class BinaryOpSpecial(BinaryOp):
    """
    A special binary operator that overrides the format logic in the repr to support applying a formatter to the
    repr of the lhs and rhs operators.

    TDOO: can we rather just use the parse functionality in the Format object to detect if there are captures ({})
          and use that instead of the special instance of Op?
    """
    def __repr__(self):
        if self._format:
            return self._format.format(repr(self._lhs), repr(self._rhs))
        else:
            return super().__repr__()


class BinaryOpReversible(BinaryOp):
    """
    Allows for the conversion of an operator into its reverse view.
    That is if the current operator is <, and it was selected from 1 < b, but we want to show this in the reverse,
    i.e. b > 1. This is logically the same but allows us to switch the operands around. This is currently
    used when cleaning up the representation of chained operators.
    """

    def __init__(self, _priority, _lhs, _rhs, _op, _format=None, _reversed=None):
        super().__init__(_priority, _lhs, _rhs, _op, _format)
        self._reversed = _reversed

    def __reverse__(self):
        """
        Does the work of reversing when requested.
        """
        return self._reversed(self)

    def __bool__(self):
        """
        In order to implement chained comparison operators (i.e. a < op < b) we need to mark an operator
        as being involved in a comparison operation. We only do this if we are a comparison operation,
        then at a later stage we can extract the chained operation.
        This done when we do the second comparison operation by detecting that the lhs has been involved in a
        comparison.

        NOTE: Only reversible operators are supported when implementing chained comparison operators.
        """
        if self.__priority__() == COMPARISON_OPERATOR_PRIORITY:
            # NOTE: This is a weak check as == and != also have the same priority, but we don't expect to experience
            # too many side effects here.
            self._lhs.__compared__ = self
            self._rhs.__compared__ = self
            # We return True to ensure the next statement is evaluated (avoid short-circuit logic)
            return True

        return FailedOp("__bool__ is not supported on Op")

    def __transform__(self, fn=lambda x: x):
        return self.__class__(self._priority, fn(self._lhs), fn(self._rhs), self._op, self._format,
                              self._reversed)

    def __clear__compared__(self):
        """
        Resets the compared state.
        This is only called once we have identified a chained operator scenario. In all other cases the state will
        not be cleared.
        """
        self._lhs.__compared__ = None
        self._rhs.__compared__ = None


class ChainCompareOp(Op):
    """
    This is the representation of the chained boolean operators.
    When we have two operations next to each other that are comparisons which share a common operator, then we can
    replace the two operands with a single operand (chained compare).

    The shared parameter should only be evaluated once. ``_obj`` represents the shared operand. This is wrapped into
    a ``ParameterOp`` which can be used to replace the shared operand in both the ``lhs`` and ``rhs`` ops. The
    parameter op ensures that the ``_obj`` is only evaluated once in the comparison operations as expected.
    """
    def __init__(self, _obj, _lhs: Op, _rhs: Op):
        super().__init__(_priority=COMPARISON_OPERATOR_PRIORITY)
        _lhs.__clear__compared__()
        self._obj = _obj
        self._parameter = ParameterOp(_name='chain_op_parameter' + str(id(self)))
        self._lhs = _lhs.__transform__(lambda x: self._parameter if self._obj is x else x)
        self._rhs = _rhs.__transform__(lambda x: self._parameter if self._obj is x else x)

    def __invoke__(self, *args, **kwargs):
        """
        Computes the _obj operand (the shared operand),
        then we invoke the lhs and rhs using the result of invoking _obj bound to the parameter name.
        """
        obj = self._obj.__invoke__(*args, **kwargs)
        if isinstance(obj, FailedOp):
            return obj

        lhs = self._lhs.__invoke__(*args, **kwargs, **{self._parameter._name: obj})
        if isinstance(lhs, FailedOp):
            return lhs
        if bool(lhs) is False:
            return lhs

        return self._rhs.__invoke__(*args, **kwargs, **{self._parameter._name: obj})

    def __repr__(self):
        lhs = repr(self._lhs if self._lhs._rhs is self._parameter else self._lhs.__reverse__())
        rhs = repr(self._rhs if self._rhs._lhs is self._parameter else self._rhs.__reverse__())
        param = repr(self._parameter)

        return lhs.split(param)[0] + repr(self._obj) + rhs.split(param)[1]

    def __visit_operands__(self, fn):
        r, c = fn(self._obj)
        if not c: return r
        r, c = fn(self._lhs)
        if not c: return r
        r, c = fn(self._rhs)
        return r

    def __transform__(self, fn=lambda x: x):
        return self.__class__(fn(self._obj), fn(self._lhs), fn(self._rhs))


class Item:
    __expression__ = None


class GetitemOp(BinaryOpSpecial):
    def __init__(self, _obj: Op, _item):
        super().__init__(_priority=16, _lhs=_obj, _rhs=_item, _op=operator.getitem, _format="{}[{}]")

    def __invoke__(self, *args, **kwargs):
        lhs = self._lhs.__invoke__(*args, **kwargs)
        if isinstance(lhs, FailedOp):
            return lhs
        rhs = self._rhs.__invoke__(*args, **kwargs)
        if isinstance(rhs, FailedOp):
            return rhs

        # if isinstance(rhs, Op) and is_iterator(rhs):
        #     return ConstOp(lhs)[rhs]

        return self._op(lhs, rhs)

    def __transform__(self, fn=lambda x: x):
        return self.__class__(fn(self._lhs), fn(self._rhs))


class CallOp(Op):
    def __init__(self, fn, args, kwargs):
        super().__init__(_priority=16)
        self._fn = make_op(fn)
        self._args = args
        self._kwargs = kwargs

    def __repr__(self):
        args = ', '.join(
            itertools.chain(
                (repr(a) for a in self._args),
                (f'{k}={v}' for k, v in self._kwargs.items())))

        return f"{repr_inner(self, self._fn)}({args})"

    def __invoke__(self, *args, **kwargs):
        call_args = []
        for a in self._args:
            a = a.__invoke__(*args, **kwargs) if isinstance(a, Op) else a
            if isinstance(a, FailedOp):
                return a
            call_args.append(a)

        call_kwargs = {}
        for k, v in self._kwargs.items():
            v = v.__invoke__(*args, **kwargs) if isinstance(v, Op) else v
            if isinstance(v, FailedOp):
                return v
            call_kwargs[k] = v

        fn: Callable = self._fn.__invoke__(*args, **kwargs)
        if isinstance(fn, FailedOp):
            return fn

        if any(isinstance(a, Op) for a in call_args) or any(isinstance(v, Op) for v in call_kwargs.values()):
            return CallOp(fn, call_args, call_kwargs)

        return fn(*call_args, **call_kwargs)

    def __visit_operands__(self, fn):
        r, c = fn(self._fn)
        if not c: return r
        for a in self._args:
            r, c = fn(a)
            if not c: return r
        for _, a in self._kwargs:
            r, c = fn(a)
            if not c: return r
        return r

    def __transform__(self, fn=lambda x: x):
        return self.__class__(fn(self._fn), tuple(fn(a) for a in self._args),
                              {k: fn(v) for k, v in self._kwargs.items()})


class IterOp(Op):
    def __init__(self, _obj):
        super().__init__(19)
        self._obj = _obj
        self._exhausted = False

    def __next__(self):
        if self._exhausted:
            raise StopIteration

        self._exhausted = True
        return self

    def __invoke__(self, *args, **kwargs):
        obj = self._obj.__invoke__(*args, **kwargs)
        if isinstance(obj, FailedOp):
            return obj

        return Iterator(obj)

    def __repr__(self):
        return f"iter({repr(self._obj)})"

    def __visit_operands__(self, fn):
        r, c = fn(self._obj)
        return r

    def __transform__(self, fn=lambda x: x):
        return self.__class__(fn(self._obj))


class Iterator(Op):
    def __init__(self, _obj):
        super().__init__(19)
        self._obj = _obj
        self._iter = None

    def __invoke__(self, *args, **kwargs):
        if self._iter is None:
            obj = self._obj if not isinstance(self._obj, Op) else self._obj.__invoke__(*args, **kwargs)
            if isinstance(obj, FailedOp):
                return obj
            self._iter = iter(obj)

    def __iter__(self):
        return self

    def __next__(self):
        r = next(self._iter, StopIteration())
        if isinstance(r, StopIteration):
            self._iter = None
            raise r
        return r

    def __repr__(self):
        return f"next({repr(self._obj)})"

    def __visit_operands__(self, fn):
        r, c = fn(self._obj)
        return r

    def __transform__(self, fn=lambda x: x):
        return self.__class__(fn(self._obj))


class ParameterOp(Op):
    """
    This represents a parameter to a function, this can be either expressed as the positions the parameter should
    be applied to the callable (i.e. it's position in the args) or as a key word parameter, in which case the
    name of the parameter this will represent.
    """
    def __init__(self, _index=None, _name=None, _type=None):
        super().__init__(_priority=18)
        self._index = _index
        self._name = _name
        self._type = _type  # Not used yet, preparation for type inference at some later date.

    def __repr__(self):
        return self._name if self._name else f"_{self._index}"

    def __invoke__(self, *args, **kwargs):
        if self._name is not None and self._name in kwargs:
            return kwargs[self._name]
        elif self._index is not None and len(args) > self._index:
            return args[self._index]
        elif '__partial__' in kwargs:
            return self
        else:
            return FailedOp(f"missing argument with {'name ' + self._name if self._name else ''}"
                            f"{' or ' if self._name and self._index is not None else ''}"
                            f"{'index ' + str(self._index) if self._index is not None else ''}")

    def __visit_operands__(self, fn):
        return None

    def __transform__(self, fn=lambda x: x):
        return self.__class__(_index=self._index, _name=self._name, _type=self._type)


class SequenceOp(Op):
    def __init__(self, _items):
        super().__init__(_priority=17)
        self._tp = type(_items)
        self._items = [make_op(a) for a in _items] if self._tp is not dict \
            else [KeyValueOp(i) for i in _items.items()]

    def __repr__(self):
        f = "({})" if self._tp is tuple else "[{}]" if self._tp is list else "{{{}}}"
        return f.format(', '.join(repr(i) for i in self._items))

    def __invoke__(self, *args, **kwargs):
        items = []
        for i in self._items:
            if find_op(i, IterOp, skip=ComprehensionOp):
                i = ComprehensionOp(self._tp, i)
                r = i.__invoke__(*args, **kwargs)
                if any(isinstance(f := x, FailedOp) for x in r):
                    return f
                items.extend(r if not self._tp is dict else r.items())
            else:
                r = i.__invoke__(*args, **kwargs)
                if isinstance(r, FailedOp):
                    return r
                items.append(r)

        return self._tp(items) if not any(isinstance(i, Op) for i in items) else SequenceOp(items)

    def __visit_operands__(self, fn):
        for i in self._items:
            r, c = fn(i)
            if not c:
                return r
        return r

    def __transform__(self, fn=lambda x: x):
        return self.__class__(self._tp(fn(i) for i in self._items))


class KeyValueOp(SequenceOp):
    def __init__(self, _items):
        assert len(_items) == 2
        super().__init__(_items)

    def __repr__(self):
        return f"{repr(self._items[0])}: {repr(self._items[1])}"


class ComprehensionOp(Op):
    def __init__(self, _tp, _item):
        super().__init__(_priority=17)
        self._tp = _tp
        self._item = _item

    def __repr__(self):
        layers, iterators = find_iterators(self._item, tp=IterOp)
        iterators = {it: ParameterOp(_name="ijklmn"[i]) for i, it in enumerate(iterators)}
        item = replace(self._item, iterators)
        f = "{{{} {}}}" if self._tp is dict and isinstance(self._item,
                                                           KeyValueOp) else "[{} {}]" if self._tp is list else "tuple({})"
        return f.format(repr(item), ' '.join(f"for {iterators[i]._name} in {repr(i)}" for i in iterators))

    def __invoke__(self, *args, **kwargs):
        return self._tp(i for i in self._generate(self._item, *args, **kwargs))

    def __visit_operands__(self, fn):
        r, c = fn(self._item)
        return r

    def __transform__(self, fn=lambda x: x):
        return self.__class__(self._tp, fn(self._item))

    @staticmethod
    def _generate(expr, *args, **kwargs):
        layers, iterators = find_iterators(expr, tp=IterOp)
        assert len(iterators) <= 6, "Comprehensions with more than 6 iterators are not supported"
        iterators = {it: ParameterOp(_name="ijklmn"[i]) for i, it in enumerate(iterators)}
        replacer = lambda x: y if ((y := iterators.get(x, None) if isinstance(x, Op) else x) is not None
                                   ) else x.__transform__(replacer)
        expr = replacer(expr)

        def gen(remaining_layers):
            ti = {iterators[i]._name: i.__transform__(replacer) for i in remaining_layers[0]}
            ti = {n: i.__invoke__(*args, **kwargs, **{it._name: it for it in iterators.values()}) for n, i in
                  ti.items()}
            for values in (gen(remaining_layers[1:]) if len(remaining_layers) > 1 else [{}]):
                for k, v in ti.items():
                    v.__invoke__(**values)
                for vals in itertools.product(*ti.values()):
                    yield {**values, **{k: v for k, v in zip(ti.keys(), vals)}}

        for values in gen(layers):
            yield expr.__invoke__(**values)


class FailedOp(Exception):
    def __init__(self, _message, _cause=None):
        self._message: str = _message
        self._cause: Exception = _cause

    def __repr__(self):
        return f"Failure: {self._message}" + (f", caused by {self._cause}" if self._cause else "")


def repr_inner(outer_op, inner_op):
    if outer_op.__priority__() > inner_op.__priority__():
        return f"({repr(inner_op)})"
    return repr(inner_op)


def find_op(op, tp, skip=None):
    def f(op):
        if isinstance(op, Op):
            if skip and isinstance(op, skip):
                return False, True
            if isinstance(op, tp):
                return True, False
            found = op.__visit_operands__(f)
            return found, not found
        return False, True

    return f(op)[0]


def find_iterators(op, tp=Iterator):
    iterators = defaultdict(list)
    stack = []

    def f(op):
        if isinstance(op, Op):
            if isinstance(op, tp):
                stack.append(op)
                iterators.setdefault(op, [])
                op.__visit_operands__(f)
                stack.pop()
                for i in stack:
                    iterators[i].append(op)
            else:
                op.__visit_operands__(f)
        return False, True

    f(op)
    layers = [list() for _ in range(max(len(l) for l in iterators.values()) + 1)]
    for i, l in iterators.items():
        layers[-1 - len(l)].append(i)
    return layers, iterators


def find_parameters(op, tp=ParameterOp):
    parameters = defaultdict(int)

    def f(op):
        if isinstance(op, Op):
            if isinstance(op, tp):
                parameters[op] += 1
            else:
                op.__visit_operands__(f)
        return False, True

    f(op)
    return tuple(parameters.keys())


def replace(op, mapping):
    def replacer(x):
        return y if ((y := mapping.get(x, None) if isinstance(x, Op) else x) is not None
                     ) else x.__transform__(replacer)

    return replacer(op)


def calc(expr: Union[Op, Sequence[Op], Mapping], *args, raise_=True, **kwargs):
    expr = make_op(expr)
    r = expr.__invoke__(*args, **kwargs)
    if isinstance(r, FailedOp) and raise_:
        raise r

    return r


class Expression:
    def __init__(self, op: Op):
        self._op = op

    def __call__(self, *args, **kwargs):
        return calc(self._op, *args, **kwargs)

    def __repr__(self):
        return repr(self._op)

    @property
    def __signature__(self):
        i_parameters = {}
        kw_parameters = []
        for p in find_parameters(self._op):
            if p._name is not None and p._index is not None:
                i_parameters[p._index] = inspect.Parameter(p._name, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            elif p._index is not None:
                i_parameters[p._index] = inspect.Parameter(f'i{p._index}', inspect.Parameter.POSITIONAL_OR_KEYWORD)
            elif p._name is not None:
                kw_parameters.append(inspect.Parameter(p._name, inspect.Parameter.KEYWORD_ONLY))

        last_index = max(i_parameters.keys(), default=-1)
        parametes = []
        for i in range(last_index + 1):
            if i in i_parameters:
                parametes.append(i_parameters[i])
            else:
                parametes.append(inspect.Parameter(f'i{i}', inspect.Parameter.POSITIONAL_OR_KEYWORD))

        parametes.extend(kw_parameters)
        return inspect.Signature(parametes)

    def __class_getitem__(cls, params):
        from typing import _SpecialGenericAlias
        args, result = params
        if isinstance(args, list):
            params = tuple(args) + (result,)
        else:
            params = args + (result,)
        return _SpecialGenericAlias(cls, 2)[params]
