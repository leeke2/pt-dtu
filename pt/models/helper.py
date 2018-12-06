from itertools import product

idx_vars_offset = 0


class Helper(object):

    """A collection of helper functions to facilitate variables and
    constraints generation.
    """

    __cp = None

    @property
    def cp(self):
        return self.__cp

    @cp.setter
    def __cp(self, val):
        self.__cp = val

    @staticmethod
    def __checkcp():
        if Helper.cp is None:
            raise RuntimeError('')

    @staticmethod
    def g(varname_template, vartype, obj, *dims):
        """Short-hand alias to generate_variables() function."""
        return Helper.generate_variables(varname_template, vartype, obj, *dims)

    @staticmethod
    def generate_variables(varname_template, vartype, obj, *dims):
        """Generates variables to the specified dimensions.

        The function generates variables to the specifications and
        add them to the Cplex problem.

        Args:
            varname_template (str): Names of the variables.
                Fields to be populated by the generator should be replaced
                by appropriate %-format identifiers (e.g. %s, %d).
            vartype ('B' or 'I'): Binary/integer variable.
            obj (float or list): Coefficient in the objective function.
            *dims (int or list): Dimensions of the variable.

        Returns:
            list/dict : Indices to the variables with
                the specified dimensions.

        >>> generate_variables('d_r0,s%d,k%d', 'I', 0.0, 4, 2)
        [[0,1],[2,3],[4,5],[6,7]]

        >>> generate_variables('c_r%d,s%s',rp%d', 'B', 0.0, 3, ['A', 'B'], 2)
        [{'A':[0,1], 'B':[2,3]}, {'A':[4,5], 'B':[6,7]}]
        """
        Helper.__checkcp()

        def generate_list(d, c):
            idx = idx_vars_offset
            while True:
                yield [next(c) if c is not None else idx+i for i in range(d)]
                idx += d

        def generate_dict(d, c):
            idx = idx_vars_offset
            while True:
                yield {k: next(c) if c is not None else idx+i
                       for i, k in enumerate(d)}
                idx += len(d)

        variables = None
        varnames = []
        generators = []

        for dim in reversed(dims):
            if len(generators) == 0:
                generators.append(generate_list(dim, None)
                                  if isinstance(dim, int)
                                  else generate_dict(dim, None))
            else:
                generators.append(generate_list(dim, generators[-1])
                                  if isinstance(dim, int)
                                  else generate_dict(dim, generators[-1]))

        variables = next(generators[-1])

        dims_expanded = [dim if type(dim) == list else range(dim)
                         for dim in dims]
        for keys in product(*dims_expanded):
            varnames.append(varname_template.format(*keys))

        global idx_vars_offset
        idx_first = idx_vars_offset
        idx_vars_offset += len(varnames)

        Helper.cp.variables.add(obj=(obj
                                     if isinstance(obj, list)
                                     else [obj] * len(varnames)),
                                types=([vartype] * len(varnames)))
        Helper.cp.variables.set_names([(idx_first+i, vn)
                                       for i, vn in enumerate(varnames)])

        return variables

    @staticmethod
    def initialize_nested_dict(*dims):
        def generate_dict(d, c):
            while True:
                yield {k: next(c) if c is not None else {} for k in d}

        generators = []

        for dim in reversed(dims):
            if type(dim) is int:
                dim = range(dim)

            if len(generators) == 0:
                generators.append(generate_dict(dim, None))
            else:
                generators.append(generate_dict(dim, generators[-1]))

        return next(generators[-1])


def linex(c):
    return map(list, zip(*c))