import sys
import os
import re

# =====================================================================
# 1. JackTokenizer: 詞法分析器
# =====================================================================
class JackTokenizer:
    KEYWORDS = {
        'class', 'constructor', 'function', 'method', 'field', 'static',
        'var', 'int', 'char', 'boolean', 'void', 'true', 'false', 'null',
        'this', 'let', 'do', 'if', 'else', 'while', 'return'
    }
    SYMBOLS = {
        '{', '}', '(', ')', '[', ']', '.', ',', ';', '+', '-', '*', '/',
        '&', '|', '<', '>', '=', '~'
    }

    def __init__(self, input_file):
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        content = self._remove_comments(content)
        self.tokens = self._tokenize(content)
        self.current_idx = -1
        self.current_token = None
        self.current_type = None

    def _remove_comments(self, text):
        # 同時匹配字串常數、多行註解、單行註解，避免誤刪字串內的 // 或 /*
        pattern = r'(".*?"|//[^\r\n]*|/\*[\s\S]*?\*/)'
        def replacer(match):
            s = match.group(0)
            return s if s.startswith('"') else ' '
        return re.sub(pattern, replacer, text)

    def _tokenize(self, text):
        # 匹配字串、符號、數字、識別字
        token_pattern = r'"[^"\r\n]*"|[{}()\[\].,;+\-*/&|<>=~]|[0-9]+|[A-Za-z_][A-Za-z0-9_]*'
        raw_tokens = re.findall(token_pattern, text)
        tokens = []
        for tok in raw_tokens:
            if tok in self.KEYWORDS:
                tokens.append(('KEYWORD', tok))
            elif tok in self.SYMBOLS:
                tokens.append(('SYMBOL', tok))
            elif tok.isdigit():
                tokens.append(('INT_CONST', int(tok)))
            elif tok.startswith('"'):
                tokens.append(('STRING_CONST', tok[1:-1]))
            else:
                tokens.append(('IDENTIFIER', tok))
        return tokens

    def has_more_tokens(self):
        return self.current_idx + 1 < len(self.tokens)

    def advance(self):
        if self.has_more_tokens():
            self.current_idx += 1
            self.current_type, self.current_token = self.tokens[self.current_idx]

    def peek(self):
        if self.has_more_tokens():
            return self.tokens[self.current_idx + 1]
        return None, None

    def token_type(self):
        return self.current_type

    def key_word(self):
        return self.current_token

    def symbol(self):
        return self.current_token

    def identifier(self):
        return self.current_token

    def int_val(self):
        return self.current_token

    def string_val(self):
        return self.current_token


# =====================================================================
# 2. SymbolTable: 符號表
# =====================================================================
class SymbolTable:
    def __init__(self):
        self.class_scope = {}
        self.subroutine_scope = {}
        self.counts = {'STATIC': 0, 'FIELD': 0, 'ARG': 0, 'VAR': 0}

    def start_subroutine(self):
        self.subroutine_scope.clear()
        self.counts['ARG'] = 0
        self.counts['VAR'] = 0

    def define(self, name, var_type, kind):
        kind = kind.upper()
        idx = self.counts[kind]
        self.counts[kind] += 1
        if kind in ('STATIC', 'FIELD'):
            self.class_scope[name] = (var_type, kind, idx)
        elif kind in ('ARG', 'VAR'):
            self.subroutine_scope[name] = (var_type, kind, idx)

    def var_count(self, kind):
        return self.counts[kind.upper()]

    def kind_of(self, name):
        if name in self.subroutine_scope:
            return self.subroutine_scope[name][1]
        if name in self.class_scope:
            return self.class_scope[name][1]
        return None

    def type_of(self, name):
        if name in self.subroutine_scope:
            return self.subroutine_scope[name][0]
        if name in self.class_scope:
            return self.class_scope[name][0]
        return None

    def index_of(self, name):
        if name in self.subroutine_scope:
            return self.subroutine_scope[name][2]
        if name in self.class_scope:
            return self.class_scope[name][2]
        return None


# =====================================================================
# 3. VMWriter: VM 程式碼生成器
# =====================================================================
class VMWriter:
    KIND_TO_SEGMENT = {
        'STATIC': 'static',
        'FIELD': 'this',
        'ARG': 'argument',
        'VAR': 'local'
    }

    def __init__(self, output_file):
        self.f = open(output_file, 'w', encoding='utf-8')

    def write_push(self, segment, index):
        seg = self.KIND_TO_SEGMENT.get(segment.upper(), segment.lower())
        self.f.write(f"push {seg} {index}\n")

    def write_pop(self, segment, index):
        seg = self.KIND_TO_SEGMENT.get(segment.upper(), segment.lower())
        self.f.write(f"pop {seg} {index}\n")

    def write_arithmetic(self, command):
        self.f.write(f"{command.lower()}\n")

    def write_label(self, label):
        self.f.write(f"label {label}\n")

    def write_goto(self, label):
        self.f.write(f"goto {label}\n")

    def write_if(self, label):
        self.f.write(f"if-goto {label}\n")

    def write_call(self, name, n_args):
        self.f.write(f"call {name} {n_args}\n")

    def write_function(self, name, n_locals):
        self.f.write(f"function {name} {n_locals}\n")

    def write_return(self):
        self.f.write("return\n")

    def close(self):
        self.f.close()


# =====================================================================
# 4. CompilationEngine: 語法分析與編譯引擎
# =====================================================================
class CompilationEngine:
    OP_MAP = {
        '+': 'add', '-': 'sub', '&': 'and', '|': 'or',
        '<': 'lt', '>': 'gt', '=': 'eq'
    }

    def __init__(self, input_file, output_file):
        self.tokenizer = JackTokenizer(input_file)
        self.vm = VMWriter(output_file)
        self.symbols = SymbolTable()
        self.class_name = ""
        self.label_counter = 0

        if self.tokenizer.has_more_tokens():
            self.tokenizer.advance()
            self.compile_class()
        self.vm.close()

    def _new_label(self, prefix):
        label = f"{prefix}_{self.label_counter}"
        self.label_counter += 1
        return label

    def _eat(self, expected=None):
        val = self.tokenizer.current_token
        if expected is not None and val != expected:
            raise SyntaxError(f"Expected '{expected}', got '{val}'")
        self.tokenizer.advance()
        return val

    def compile_class(self):
        self._eat('class')
        self.class_name = self._eat()
        self._eat('{')

        while self.tokenizer.current_token in ('static', 'field'):
            self.compile_class_var_dec()

        while self.tokenizer.current_token in ('constructor', 'function', 'method'):
            self.compile_subroutine()

        self._eat('}')

    def compile_class_var_dec(self):
        kind = self._eat()  # 'static' or 'field'
        var_type = self._eat()
        name = self._eat()
        self.symbols.define(name, var_type, kind)

        while self.tokenizer.current_token == ',':
            self._eat(',')
            name = self._eat()
            self.symbols.define(name, var_type, kind)

        self._eat(';')

    def compile_subroutine(self):
        self.symbols.start_subroutine()
        sub_kind = self._eat()  # 'constructor', 'function', 'method'
        self._eat()             # return type ('void' or type)
        sub_name = self._eat()

        if sub_kind == 'method':
            self.symbols.define('this', self.class_name, 'ARG')

        self._eat('(')
        self.compile_parameter_list()
        self._eat(')')

        # SubroutineBody
        self._eat('{')
        while self.tokenizer.current_token == 'var':
            self.compile_var_dec()

        n_locals = self.symbols.var_count('VAR')
        self.vm.write_function(f"{self.class_name}.{sub_name}", n_locals)

        if sub_kind == 'constructor':
            n_fields = self.symbols.var_count('FIELD')
            self.vm.write_push('constant', n_fields)
            self.vm.write_call('Memory.alloc', 1)
            self.vm.write_pop('pointer', 0)
        elif sub_kind == 'method':
            self.vm.write_push('argument', 0)
            self.vm.write_pop('pointer', 0)

        self.compile_statements()
        self._eat('}')

    def compile_parameter_list(self):
        if self.tokenizer.current_token != ')':
            var_type = self._eat()
            name = self._eat()
            self.symbols.define(name, var_type, 'ARG')
            while self.tokenizer.current_token == ',':
                self._eat(',')
                var_type = self._eat()
                name = self._eat()
                self.symbols.define(name, var_type, 'ARG')

    def compile_var_dec(self):
        self._eat('var')
        var_type = self._eat()
        name = self._eat()
        self.symbols.define(name, var_type, 'VAR')

        while self.tokenizer.current_token == ',':
            self._eat(',')
            name = self._eat()
            self.symbols.define(name, var_type, 'VAR')

        self._eat(';')

    def compile_statements(self):
        while self.tokenizer.current_token in ('let', 'if', 'while', 'do', 'return'):
            stmt = self.tokenizer.current_token
            if stmt == 'let':
                self.compile_let()
            elif stmt == 'if':
                self.compile_if()
            elif stmt == 'while':
                self.compile_while()
            elif stmt == 'do':
                self.compile_do()
            elif stmt == 'return':
                self.compile_return()

    def compile_let(self):
        self._eat('let')
        var_name = self._eat()
        kind = self.symbols.kind_of(var_name)
        idx = self.symbols.index_of(var_name)

        is_array = False
        if self.tokenizer.current_token == '[':
            is_array = True
            self._eat('[')
            self.compile_expression()
            self._eat(']')
            self.vm.write_push(kind, idx)
            self.vm.write_arithmetic('add')

        self._eat('=')
        self.compile_expression()
        self._eat(';')

        if is_array:
            self.vm.write_pop('temp', 0)
            self.vm.write_pop('pointer', 1)
            self.vm.write_push('temp', 0)
            self.vm.write_pop('that', 0)
        else:
            self.vm.write_pop(kind, idx)

    def compile_if(self):
        else_label = self._new_label("IF_ELSE")
        end_label = self._new_label("IF_END")

        self._eat('if')
        self._eat('(')
        self.compile_expression()
        self._eat(')')

        self.vm.write_arithmetic('not')
        self.vm.write_if(else_label)

        self._eat('{')
        self.compile_statements()
        self._eat('}')
        self.vm.write_goto(end_label)

        self.vm.write_label(else_label)
        if self.tokenizer.current_token == 'else':
            self._eat('else')
            self._eat('{')
            self.compile_statements()
            self._eat('}')

        self.vm.write_label(end_label)

    def compile_while(self):
        start_label = self._new_label("WHILE_EXP")
        end_label = self._new_label("WHILE_END")

        self.vm.write_label(start_label)
        self._eat('while')
        self._eat('(')
        self.compile_expression()
        self._eat(')')

        self.vm.write_arithmetic('not')
        self.vm.write_if(end_label)

        self._eat('{')
        self.compile_statements()
        self._eat('}')
        self.vm.write_goto(start_label)

        self.vm.write_label(end_label)

    def compile_do(self):
        self._eat('do')
        self._compile_subroutine_call()
        self._eat(';')
        self.vm.write_pop('temp', 0)  # 丟棄 void 回傳值

    def compile_return(self):
        self._eat('return')
        if self.tokenizer.current_token != ';':
            self.compile_expression()
        else:
            self.vm.write_push('constant', 0)
        self._eat(';')
        self.vm.write_return()

    def compile_expression(self):
        self.compile_term()
        while self.tokenizer.current_token in ('+', '-', '*', '/', '&', '|', '<', '>', '='):
            op = self._eat()
            self.compile_term()
            if op == '*':
                self.vm.write_call('Math.multiply', 2)
            elif op == '/':
                self.vm.write_call('Math.divide', 2)
            else:
                self.vm.write_arithmetic(self.OP_MAP[op])

    def compile_term(self):
        t_type = self.tokenizer.token_type()
        tok = self.tokenizer.current_token

        if t_type == 'INT_CONST':
            self.vm.write_push('constant', self._eat())

        elif t_type == 'STRING_CONST':
            s = self._eat()
            self.vm.write_push('constant', len(s))
            self.vm.write_call('String.new', 1)
            for ch in s:
                self.vm.write_push('constant', ord(ch))
                self.vm.write_call('String.appendChar', 2)

        elif t_type == 'KEYWORD':
            kw = self._eat()
            if kw == 'true':
                self.vm.write_push('constant', 1)
                self.vm.write_arithmetic('neg')
            elif kw in ('false', 'null'):
                self.vm.write_push('constant', 0)
            elif kw == 'this':
                self.vm.write_push('pointer', 0)

        elif tok == '(':
            self._eat('(')
            self.compile_expression()
            self._eat(')')

        elif tok in ('-', '~'):
            op = self._eat()
            self.compile_term()
            self.vm.write_arithmetic('neg' if op == '-' else 'not')

        elif t_type == 'IDENTIFIER':
            next_type, next_tok = self.tokenizer.peek()
            if next_tok == '[':
                var_name = self._eat()
                self._eat('[')
                self.compile_expression()
                self._eat(']')
                self.vm.write_push(self.symbols.kind_of(var_name), self.symbols.index_of(var_name))
                self.vm.write_arithmetic('add')
                self.vm.write_pop('pointer', 1)
                self.vm.write_push('that', 0)
            elif next_tok in ('(', '.'):
                self._compile_subroutine_call()
            else:
                var_name = self._eat()
                self.vm.write_push(self.symbols.kind_of(var_name), self.symbols.index_of(var_name))

    def _compile_subroutine_call(self):
        ident = self._eat()
        n_args = 0

        if self.tokenizer.current_token == '.':
            self._eat('.')
            sub_name = self._eat()
            var_type = self.symbols.type_of(ident)
            if var_type is not None:
                # 物件方法呼叫: obj.method(...)
                self.vm.write_push(self.symbols.kind_of(ident), self.symbols.index_of(ident))
                full_name = f"{var_type}.{sub_name}"
                n_args = 1
            else:
                # 靜態函式或建構子呼叫: Class.func(...)
                full_name = f"{ident}.{sub_name}"
        else:
            # 同類別內的方法呼叫: method(...)
            self.vm.write_push('pointer', 0)
            full_name = f"{self.class_name}.{ident}"
            n_args = 1

        self._eat('(')
        n_args += self.compile_expression_list()
        self._eat(')')
        self.vm.write_call(full_name, n_args)

    def compile_expression_list(self):
        count = 0
        if self.tokenizer.current_token != ')':
            self.compile_expression()
            count += 1
            while self.tokenizer.current_token == ',':
                self._eat(',')
                self.compile_expression()
                count += 1
        return count


# =====================================================================
# 主程式進入點
# =====================================================================
def compile_path(target_path):
    if os.path.isfile(target_path):
        if target_path.endswith('.jack'):
            out_path = target_path[:-5] + '.vm'
            CompilationEngine(target_path, out_path)
            print(f"Compiled: {target_path} -> {out_path}")
    elif os.path.isdir(target_path):
        for root, _, files in os.walk(target_path):
            for file in files:
                if file.endswith('.jack'):
                    in_path = os.path.join(root, file)
                    out_path = in_path[:-5] + '.vm'
                    CompilationEngine(in_path, out_path)
                    print(f"Compiled: {in_path} -> {out_path}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python JackCompiler.py <file.jack | directory>")
        sys.exit(1)
    compile_path(sys.argv[1])
