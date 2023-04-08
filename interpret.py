import sys
from antlr4 import *
from stella.stellaParser import stellaParser
from stella.stellaLexer import stellaLexer


def compare_types(expected: str, actual: str):
    """
    helps to compare two types by removing parenthesis.
    return True if strings that represent types are identical, False otherwise.
    """

    if expected is None or actual is None:
        return False

    expected = expected.replace('(', '').replace(')', '').replace(' ', '')
    actual = actual.replace('(', '').replace(')', '').replace(' ', '')

    return expected == actual


class Handler:

    def __init__(self):
        self.variables = {'0': 'Nat', '1': 'Nat'}
        self.functions = {}

    def handle_expr_context(
            self,
            ctx: stellaParser.ExprContext,
    ):
        """
        handles expression context, checks type consistency of expression.
        passes: stellaParser.ExprContext instance.
        returns: actual type of expression.
        """

        if isinstance(ctx, stellaParser.ConstTrueContext):
            """
            returns Bool type if expression is 'true'.
            """
            return 'Bool'

        elif isinstance(ctx, stellaParser.ConstFalseContext):
            """
            returns Bool type if expression is 'false'.
            """
            return 'Bool'

        elif isinstance(ctx, stellaParser.ConstUnitContext):
            return 'Unit'

        elif isinstance(ctx, stellaParser.ConsListContext):
            """
            handles cons of list.
            returns [<type_of_created_list>] if type of head and type of elements in tail are same.
            raises RuntimeError otherwise.
            """

            type_of_tail = self.handle_expr_context(ctx.tail)
            type_of_head = self.handle_expr_context(ctx.head)

            if compare_types(f'[{type_of_head}]', type_of_tail):
                return type_of_tail
            else:
                raise RuntimeError(f'in cons expression: head have type {type_of_head}, while type of tail is {type_of_tail}')

        elif isinstance(ctx, stellaParser.SuccContext):
            """
            handles succ expression context.
            returns Nat if argument is Nat.
            raises RuntimeError otherwise.
            """

            if self.handle_expr_context(ctx.n) == 'Nat':
                return 'Nat'
            else:
                raise RuntimeError(f'in "{ctx.getText()}": Nat expected, got {self.handle_expr_context(ctx.n)}')

        elif isinstance(ctx, stellaParser.IfContext):
            """
            handles if a then b else c expression context.
            return type of b, if types of b and c are same and a is Bool.
            if types of b and c are different, returns sum type <b_type>+<c_type>
            raises RuntimeError otherwise.
            """

            condition_type = self.handle_expr_context(ctx.condition)
            then_type = self.handle_expr_context(ctx.thenExpr)
            else_type = self.handle_expr_context(ctx.elseExpr)

            if condition_type == 'Bool' and then_type == else_type:
                return then_type
            else:
                if condition_type != 'Bool':
                    raise RuntimeError(f'in condition expression "{ctx.condition.getText()}": Bool expected, got '
                                       f'{self.handle_expr_context(ctx.condition)}')
                else:
                    return f'{then_type}+{else_type}'

        elif isinstance(ctx, stellaParser.VarContext):
            """
            handles var context.
            returns type of variable.
            """

            if ctx.name.text in self.variables:
                return self.variables[ctx.name.text]
            else:
                return None

        elif isinstance(ctx, stellaParser.NatRecContext):
            """
            handles Nat::rec(n, z, s) context.
            return type of z (initial value), if type of Nat::rec is fn(Nat) -> (fn(T) -> T),
                where T is type of z.
            raises RuntmeError otherwise .
            """

            t = self.variables[ctx.initial.getText()]
            expected_type = f'fn(Nat)->(fn({t})->({t}))'
            actual_type = self.handle_expr_context(ctx.step)

            if self.variables[ctx.n.getText()] == 'Nat' and compare_types(expected_type, actual_type):
                return t
            else:
                if self.variables[ctx.n.getText()] != 'Nat':
                    raise RuntimeError(f'in Nat::rec expression in input value {ctx.n.getText()}: Nat expected, '
                                       f'got {self.handle_expr_context(ctx.n)}')
                else:
                    raise RuntimeError(f'in Nat::rec expression in function: {expected_type} expected, '
                                       f'got {actual_type}')

        elif isinstance(ctx, stellaParser.AbstractionContext):
            """
            handles abstractions.
            returns type of abstract function.
            """

            local_params = {
                param.name.text: param.paramType.getText()
                for param in ctx.paramDecls
            }

            local_type = None

            for param in local_params:
                local_type = local_params[param]

            self.variables.update(local_params)
            return f'fn({local_type})->({self.handle_expr_context(ctx.returnExpr)})'

        elif isinstance(ctx, stellaParser.ApplicationContext):
            """
            handles application.
            returns type of applied function.
            """

            function_name = ctx.fun.getText().split('(')[0]

            if function_name not in self.functions:
                return None

            if isinstance(ctx.fun, stellaParser.VarContext):
                expected_type = self.functions[function_name]['return_type']
                actual_type = self.handle_expr_context(ctx.args[0])

                if compare_types(expected_type, actual_type):
                    return expected_type
                else:
                    raise RuntimeError(f'in "{ctx.fun.getText()}" expected {expected_type}, actual type is {actual_type}')
            else:
                return self.handle_expr_context(ctx.args[0])

        elif isinstance(ctx, stellaParser.InlContext):
            return self.handle_expr_context(ctx.expr())

        elif isinstance(ctx, stellaParser.InrContext):
            return self.handle_expr_context(ctx.expr())

        elif isinstance(ctx, stellaParser.PatternVarContext):

            if ctx.name.text not in self.variables:
                return None

            return self.variables[ctx.name.text]

        elif isinstance(ctx, stellaParser.PatternTrueContext):
            return 'Bool'

        elif isinstance(ctx, stellaParser.PatternFalseContext):
            return 'Bool'

        elif isinstance(ctx, stellaParser.PatternUnitContext):
            return 'Unit'

        elif isinstance(ctx, stellaParser.PatternInlContext):
            return self.handle_expr_context(ctx.pattern())

        elif isinstance(ctx, stellaParser.PatternInrContext):
            return self.handle_expr_context(ctx.pattern())

        elif isinstance(ctx, stellaParser.MatchContext):

            match_types = []

            for case in ctx.cases:

                pattern = self.handle_expr_context(case.pattern())

                expr = self.handle_expr_context(case.expr())

                match_types.append((pattern, expr))

            return match_types

        elif isinstance(ctx, stellaParser.ListContext):
            """
            handles lists.
            returns [<type of elements>] if all of elements in list have same type.
            raises RuntimeError otherwise.
            """

            types_of_elements = {}

            for expr in ctx.exprs:

                type_of_element = self.handle_expr_context(expr).replace('(', '').replace(')', '')

                if type_of_element not in types_of_elements:
                    types_of_elements[type_of_element] = [expr.getText()]
                else:
                    types_of_elements[type_of_element].append(expr.getText())

            if len(types_of_elements) == 1:
                return f'[{list(types_of_elements.keys())[0]}]'
            else:
                raise RuntimeError(f'in "{ctx.getText()}" list: {types_of_elements}')

        elif isinstance(ctx, stellaParser.DotTupleContext):
            """
            """

            type_of_tuple = self.handle_expr_context(ctx.expr()
                                                     ).replace('{', '').replace('}', '').replace(' ', '').split(',')
            return type_of_tuple[int(ctx.index.text) - 1]

        elif isinstance(ctx, stellaParser.TupleContext):
            """
            """

            type_of_tuple = '{'

            for expr in ctx.exprs:
                type_of_tuple += self.handle_expr_context(expr) + ','

            type_of_tuple = type_of_tuple[:-1] + '}'

            return type_of_tuple

        elif isinstance(ctx, stellaParser.ConstIntContext):
            """
            handles constant integers context.
            returns 'Nat' string corresponding to Nat type.
            """
            return 'Nat'

        else:
            print(type(ctx))
            raise RuntimeError("unsupported syntax")

    def handle_decl_context(self, ctx: stellaParser.DeclContext):
        """
        handles declaration context, checks type consistency of declaration and its return expression.
        passes: stellaParser.DeclContext instance.
        returns nothing if typecheck is successfully passed, raises corresponding log message otherwise.
        """

        if isinstance(ctx, stellaParser.DeclFunContext):

            local_params = {
                param.name.text: param.paramType.getText()
                for param in ctx.paramDecls
            }

            local_type = None

            for param in local_params:
                local_type = local_params[param]

            self.variables.update(local_params)
            expected_return_type = ctx.returnType.getText()

            self.functions.update({
                ctx.name.text: {
                    'param_type': local_type,
                    'return_type': expected_return_type,
                }
            })

            if isinstance(ctx.returnExpr, stellaParser.ExprContext):

                try:
                    return_type = self.handle_expr_context(ctx.returnExpr)

                    if isinstance(ctx.returnExpr, stellaParser.MatchContext):

                        expected_types = [ex_type.replace('(', '').replace(')', '').replace(' ', '')
                              for ex_type in expected_return_type.split('+')]

                        local_types = [loc_type.replace('(', '').replace(')', '').replace(' ', '')
                              for loc_type in local_type.split('+')]

                        for ret_type in return_type:
                            if (ret_type[0] is None or ret_type[0] in local_types) or (
                                    ret_type[1] is None or ret_type[1] in expected_types):
                                continue
                            else:
                                raise RuntimeError('aboba')

                    elif isinstance(ctx.returnExpr, stellaParser.ApplicationContext):

                        declaration_name = ctx.name.text
                        application_name = ctx.returnExpr.getText().split('(')[0]

                        declaration_param_type = self.handle_expr_context(ctx.returnExpr.args[0])
                        application_param_type = self.functions[application_name]['param_type']

                        if not compare_types(declaration_param_type, application_param_type):
                            raise RuntimeError(f'declaration param type is {declaration_param_type}, while '
                                               f'application param type is {application_param_type}')

                        declaration_return_type = self.functions[declaration_name]['return_type']
                        application_return_type = self.handle_expr_context(ctx.returnExpr)

                        if not compare_types(declaration_return_type, application_return_type):
                            raise RuntimeError(f'declaration return type is {declaration_return_type}, while '
                                               f'application return type is {application_return_type}')

                    elif isinstance(ctx.returnExpr, stellaParser.AbstractionContext):

                        declaration_name = ctx.name.text
                        declaration_return_type = self.functions[declaration_name]['return_type']

                        # print(ctx.returnExpr.paramDecls[0].paramType.getText())
                        # print(self.handle_expr_context(ctx.returnExpr))

                        if not compare_types(declaration_return_type, return_type):
                            raise RuntimeError(f'declaration return type is {declaration_return_type}, while '
                                               f'abstraction return type is {return_type}')

                    elif not compare_types(expected_return_type, return_type):
                        raise RuntimeError(f'declaration return type is {expected_return_type}, while '
                                           f'return type is {return_type}')

                except RuntimeError as error:
                    print(f'[TYPE ERROR] "{ctx.name.text}": {error}')

        elif isinstance(ctx, stellaParser.DeclTypeAliasContext):
            raise RuntimeError("\t\tunsupported syntax")

        else:
            raise RuntimeError("\t\tunsupported syntax")

    def handle_program_context(self, ctx: stellaParser.ProgramContext):
        """
        handles program context.
        passes: stellaParser.ProgramContext instance.
        """

        for decl in ctx.decls:
            self.handle_decl_context(decl)


def main(argv):

    if len(argv) > 1:
        input_stream = FileStream(argv[1])
    else:
        input_stream = StdinStream()

    lexer = stellaLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = stellaParser(stream)

    program = parser.program()
    handler = Handler()
    handler.handle_program_context(program)


if __name__ == '__main__':
    main(sys.argv)
