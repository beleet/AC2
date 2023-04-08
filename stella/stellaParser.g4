parser grammar stellaParser;

options {
    tokenVocab = stellaLexer;
}

start_Program: x = program EOF;
start_Expr: x = expr EOF;
start_Type: x = stellatype EOF;

program:
    languageDecl (extensions += extension)* (decls += decl)*;

languageDecl: 'language' 'core' ';' # LanguageCore;

extension:
    'extend' 'with' extensionNames += ExtensionName (
        ',' extensionNames += ExtensionName
    )* ';' # AnExtension;

decl: (annotations += annotation)* 'fn' name = StellaIdent '(' (
        paramDecls += paramDecl (',' paramDecls += paramDecl)*
    )? ')' ('->' returnType = stellatype)? (
        'throws' throwTypes+= stellatype (',' throwTypes+=stellatype)*
    )? '{' (localDecls += decl)* 'return' returnExpr = expr '}' # DeclFun
    | 'type' name = StellaIdent '=' atype = stellatype          # DeclTypeAlias;

annotation: 'inline' # InlineAnnotation;
paramDecl: name = StellaIdent ':' paramType = stellatype;

expr:
    // expr6
    expr_ = expr '.' label = StellaIdent # DotRecord
    | expr_ = expr '.' index = INTEGER   # DotTuple
    | 'true'                             # ConstTrue
    | 'false'                            # ConstFalse
    | 'unit'                             # ConstUnit
    | n = INTEGER                        # ConstInt
    | name = StellaIdent                 # Var
    // expr
    | 'inl' '(' expr_=expr ')'                     # Inl
    | 'inr' '(' expr_=expr ')'                     # Inr
    | 'cons' '(' head = expr ',' tail = expr ')'                     # ConsList
    | 'List::head' '(' lst = expr ')'                               # Head
    | 'List::isempty' '(' lst = expr ')'                            # IsEmpty
    | 'List::tail' '(' lst = expr ')'                               # Tail
    | 'succ' '(' n = expr ')'                                        # Succ
    | 'not' '(' expr_ = expr ')'                                     # LogicNot
    | 'Nat::pred' '(' n = expr ')'                                   # Pred
    | 'Nat::iszero' '(' n = expr ')'                                 # IsZero
    | 'fix' '(' expr_ = expr ')'                                     # Fix
    | 'Nat::rec' '(' n = expr ',' initial = expr ',' step = expr ')' # NatRec
    | 'fold' '[' type_ = stellatype ']' expr_ = expr                 # Fold
    | 'unfold' '[' type_ = stellatype ']' expr_ = expr               # Unfold
    // expr
    | fun = expr '(' (args += expr (',' args += expr)*)? ')' # Application
    // expr
    | expr '*' expr   # Multiply
    | expr '/' expr   # Divide
    | expr 'and' expr # LogicAnd
    // expr
    | expr '+' expr                        # Add
    | expr '-' expr                        # Subtract
    | expr 'or' expr                       # LogicOr
    | expr_ = expr 'as' type_ = stellatype # TypeAsc
    | 'fn' '(' (
        paramDecls += paramDecl (',' paramDecls += paramDecl)*
    )? ')' '{' 'return' returnExpr = expr '}'       # Abstraction
    | '{' (exprs += expr (',' exprs += expr)*)? '}' # Tuple
    | '{' bindings += binding (',' bindings += binding)* '}' # Record
    | '<|' label = StellaIdent ('=' rhs = expr)? '|>' # Variant
    | 'match' expr '{' (
        cases += match_case ('|' cases += match_case)*
    )? '}'                                         # match
    | '[' (exprs += expr (',' exprs += expr)*)? ']' # List
    // expr
    | left = expr '<' right = expr  # LessThan
    | left = expr '<=' right = expr # LessThanOrEqual
    | left = expr '>' right = expr  # GreaterThan
    | left = expr '>=' right = expr # GreaterThanOrEqual
    | left = expr '==' right = expr # Equal
    | left = expr '!=' right = expr # NotEqual
    // expr
    | 'if' condition = expr 'then' thenExpr = expr 'else' elseExpr = expr # If
    | 'let' patternBindings+=patternBinding (',' patternBindings+=patternBinding)* 'in' body = expr           # Let
    | 'letrec' patternBindings+=patternBinding (',' patternBindings+=patternBinding)* 'in' body = expr           # Let
    | '(' expr_ = expr ')'                                                        # ParenthesisedExpr
    | expr1 = expr ';' expr2 = expr # Sequence
    | expr_ = expr ';' # TerminatingSemicolon;

patternBinding: pat=pattern '=' rhs=expr ;

binding: name = StellaIdent '=' rhs = expr;

match_case: pattern_ = pattern '=>' expr_ = expr;

pattern:
    '<|' label = StellaIdent ('=' pattern_ = pattern)? '|>'                # PatternVariant
    | 'inl' '(' pattern_ = pattern ')' # PatternInl
    | 'inr' '(' pattern_ = pattern ')' # PatternInr
    | '{' (patterns += pattern (',' patterns += pattern)*)? '}' # PatternTuple
    | '{' (
        patterns += labelledPattern (
            ',' patterns += labelledPattern
        )*
    )? '}'                                                      # PatternRecord
    | '[' (patterns += pattern (',' patterns += pattern)*)? ']' # PatternList
    | 'cons' '(' head = pattern ',' tail = pattern ')'          # PatternCons
    | 'false'                                                   # PatternFalse
    | 'true'                                                    # PatternTrue
    | 'unit'                                                    # PatternUnit
    | n = INTEGER                                               # PatternInt
    | 'succ' '(' pattern_ = pattern ')'                                # PatternSucc
    | name = StellaIdent                                        # PatternVar
    | '(' pattern_ = pattern ')'                                           # ParenthesisedPattern;

labelledPattern: label = StellaIdent '=' pattern;

stellatype:
    'Bool'  # TypeBool
    | 'Nat' # TypeNat
    | 'fn' '(' (
        paramTypes += stellatype (',' paramTypes += stellatype)*
    )? ')' '->' returnType = stellatype                        # TypeFun
    | 'µ' var = StellaIdent '.' type_ = stellatype             # TypeRec
    | left = stellatype '+' right = stellatype                 # TypeSum
    | '{' (types += stellatype (',' types += stellatype)*)? '}' # TypeTuple
    | '{'
        fieldTypes += recordFieldType (
            ',' fieldTypes += recordFieldType
        )*
     '}' # TypeRecord
    | '{' (
        fieldTypes += variantFieldType (
            ',' fieldTypes += variantFieldType
        )*
    )? '}'                                                      # TypeVariant
    | '[' (types += stellatype (',' types += stellatype)*)? ']' # TypeList
    | 'Unit'                                                    # TypeUnit
    | name = StellaIdent                                        # TypeVar
    | '(' type_ = stellatype ')' # TypeParens;

recordFieldType: label = StellaIdent ':' type_ = stellatype;
variantFieldType: label = StellaIdent (':' type_ = stellatype)?;