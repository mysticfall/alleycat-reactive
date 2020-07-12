import dis


def take1(iterator):
    try:
        return next(iterator)
    except StopIteration:
        raise Exception("missing bytecode instruction") from None


def take(iterator, count):
    for x in range(count):
        yield take1(iterator)


def get_assigned_name(frame):
    """Takes a frame and returns a description of the name(s) to which the
    currently executing CALL_FUNCTION instruction's value will be assigned.

    fn()                    => None
    a = fn()                => "a"
    a, b = fn()             => ("a", "b")
    a.a2.a3, b, c* = fn()   => ("a.a2.a3", "b", Ellipsis)
    """

    iterator = iter(dis.get_instructions(frame.f_code))
    for instr in iterator:
        if instr.offset == frame.f_lasti:
            break
    else:
        assert False, "bytecode instruction missing"
    assert instr.opname.startswith('CALL_')
    instr = take1(iterator)
    if instr.opname == 'POP_TOP':
        raise ValueError("not assigned to variable")
    return instr_dispatch(instr, iterator)


def instr_dispatch(instr, iterator):
    opname = instr.opname
    if (opname == 'STORE_FAST'  # (co_varnames)
            or opname == 'STORE_GLOBAL'  # (co_names)
            or opname == 'STORE_NAME'  # (co_names)
            or opname == 'STORE_DEREF'):  # (co_cellvars++co_freevars)
        return instr.argval
    if opname == 'UNPACK_SEQUENCE':
        return tuple(instr_dispatch(instr, iterator)
                     for instr in take(iterator, instr.arg))
    if opname == 'UNPACK_EX':
        return (*tuple(instr_dispatch(instr, iterator)
                       for instr in take(iterator, instr.arg)),
                Ellipsis)
    # Note: 'STORE_SUBSCR' and 'STORE_ATTR' should not be possible here.
    # `lhs = rhs` in Python will evaluate `lhs` after `rhs`.
    # Thus `x.attr = rhs` will first evalute `rhs` then load `a` and finally
    # `STORE_ATTR` with `attr` as instruction argument. `a` can be any
    # complex expression, so full support for understanding what a
    # `STORE_ATTR` will target requires decoding the full range of expression-
    # related bytecode instructions. Even figuring out which `STORE_ATTR`
    # will use our return value requires non-trivial understanding of all
    # expression-related bytecode instructions.
    # Thus we limit ourselfs to loading a simply variable (of any kind)
    # and a arbitary number of LOAD_ATTR calls before the final STORE_ATTR.
    # We will represents simply a string like `my_var.loaded.loaded.assigned`
    if opname in {'LOAD_CONST', 'LOAD_DEREF', 'LOAD_FAST',
                  'LOAD_GLOBAL', 'LOAD_NAME'}:
        return instr.argval + "." + ".".join(
            instr_dispatch_for_load(iterator))
    raise NotImplementedError("assignment could not be parsed: "
                              "instruction {} not understood"
                              .format(instr))


def instr_dispatch_for_load(iterator):
    instr = take1(iterator)
    opname = instr.opname
    if opname == 'LOAD_ATTR':
        yield instr.argval
        yield from instr_dispatch_for_load(iterator)
    elif opname == 'STORE_ATTR':
        yield instr.argval
    else:
        raise NotImplementedError("assignment could not be parsed: "
                                  "instruction {} not understood"
                                  .format(instr))
