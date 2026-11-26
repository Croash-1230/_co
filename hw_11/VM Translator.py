import os
import sys


class Parser:
    """解析單一 .vm 檔案，將每行指令拆解為詞法元素"""

    ARITHMETIC_COMMANDS = {'add', 'sub', 'neg', 'eq', 'gt', 'lt', 'and', 'or', 'not'}

    def __init__(self, input_path: str):
        with open(input_path, 'r', encoding='utf-8') as f:
            raw_lines = f.readlines()

        self.commands = []
        for line in raw_lines:
            # 移除 // 註解與前後空白
            clean = line.split('//')[0].strip()
            if clean:
                self.commands.append(clean)

        self.current_idx = -1
        self.current_tokens = []

    def has_more_lines(self) -> bool:
        return self.current_idx + 1 < len(self.commands)

    def advance(self):
        self.current_idx += 1
        self.current_tokens = self.commands[self.current_idx].split()

    def command_type(self) -> str:
        op = self.current_tokens[0]
        if op in self.ARITHMETIC_COMMANDS:
            return 'C_ARITHMETIC'
        mapping = {
            'push': 'C_PUSH',
            'pop': 'C_POP',
            'label': 'C_LABEL',
            'goto': 'C_GOTO',
            'if-goto': 'C_IF',
            'function': 'C_FUNCTION',
            'return': 'C_RETURN',
            'call': 'C_CALL',
        }
        return mapping[op]

    def arg1(self) -> str:
        if self.command_type() == 'C_ARITHMETIC':
            return self.current_tokens[0]
        return self.current_tokens[1]

    def arg2(self) -> int:
        return int(self.current_tokens[2])


class CodeWriter:
    """將 VM 指令轉譯為 Hack 組合語言並寫入輸出檔"""

    SEGMENT_POINTERS = {
        'local': 'LCL',
        'argument': 'ARG',
        'this': 'THIS',
        'that': 'THAT',
    }

    def __init__(self, output_path: str):
        self.out = open(output_path, 'w', encoding='utf-8')
        self.file_name = ''
        self.current_function = ''
        self.label_counter = 0

    def set_file_name(self, file_name: str):
        """切換正在處理的 .vm 檔名（用於 static 變數命名 Xxx.i）"""
        self.file_name = os.path.splitext(os.path.basename(file_name))[0]

    def _write(self, lines: list[str]):
        for line in lines:
            self.out.write(line + '\n')

    def write_init(self):
        """第 8 章：寫入 Bootstrap 啟動碼 (SP=256, call Sys.init)"""
        self._write([
            '// Bootstrap code',
            '@256',
            'D=A',
            '@SP',
            'M=D',
        ])
        self.write_call('Sys.init', 0)

    def write_arithmetic(self, command: str):
        """第 7 章：算術與邏輯運算"""
        self._write([f'// {command}'])

        if command in ('neg', 'not'):
            op = '-' if command == 'neg' else '!'
            self._write([
                '@SP',
                'A=M-1',
                f'M={op}M',
            ])
            return

        # 二元運算：先 pop y 到 D，再指向 x (M)
        self._write([
            '@SP',
            'AM=M-1',
            'D=M',
            'A=A-1',
        ])

        if command in ('add', 'sub', 'and', 'or'):
            ops = {'add': 'M+D', 'sub': 'M-D', 'and': 'M&D', 'or': 'M|D'}
            self._write([f'M={ops[command]}'])
        elif command in ('eq', 'gt', 'lt'):
            jump = {'eq': 'JEQ', 'gt': 'JGT', 'lt': 'JLT'}[command]
            uid = self.label_counter
            self.label_counter += 1
            true_label = f'COMP_TRUE_{uid}'
            end_label = f'COMP_END_{uid}'
            self._write([
                'D=M-D',
                f'@{true_label}',
                f'D;{jump}',
                '@SP',
                'A=M-1',
                'M=0',          # false = 0
                f'@{end_label}',
                '0;JMP',
                f'({true_label})',
                '@SP',
                'A=M-1',
                'M=-1',         # true = -1
                f'({end_label})',
            ])

    def write_push_pop(self, command: str, segment: str, index: int):
        """第 7 章：8 個記憶體區段的 push / pop"""
        self._write([f'// {command} {segment} {index}'])

        if command == 'C_PUSH':
            if segment == 'constant':
                self._write([f'@{index}', 'D=A'])
            elif segment in self.SEGMENT_POINTERS:
                base = self.SEGMENT_POINTERS[segment]
                self._write([f'@{base}', 'D=M', f'@{index}', 'A=D+A', 'D=M'])
            elif segment == 'temp':
                self._write([f'@{5 + index}', 'D=M'])
            elif segment == 'pointer':
                target = 'THIS' if index == 0 else 'THAT'
                self._write([f'@{target}', 'D=M'])
            elif segment == 'static':
                self._write([f'@{self.file_name}.{index}', 'D=M'])

            # 將 D 推入堆疊頂端並 SP++
            self._write([
                '@SP',
                'A=M',
                'M=D',
                '@SP',
                'M=M+1',
            ])

        elif command == 'C_POP':
            if segment in self.SEGMENT_POINTERS:
                base = self.SEGMENT_POINTERS[segment]
                # 計算目標位址暫存於 R13
                self._write([
                    f'@{base}',
                    'D=M',
                    f'@{index}',
                    'D=D+A',
                    '@R13',
                    'M=D',
                    '@SP',
                    'AM=M-1',
                    'D=M',
                    '@R13',
                    'A=M',
                    'M=D',
                ])
            elif segment == 'temp':
                self._write(['@SP', 'AM=M-1', 'D=M', f'@{5 + index}', 'M=D'])
            elif segment == 'pointer':
                target = 'THIS' if index == 0 else 'THAT'
                self._write(['@SP', 'AM=M-1', 'D=M', f'@{target}', 'M=D'])
            elif segment == 'static':
                self._write(['@SP', 'AM=M-1', 'D=M', f'@{self.file_name}.{index}', 'M=D'])

    def _scoped_label(self, label: str) -> str:
        """函式內區域標籤格式：functionName$label"""
        if self.current_function:
            return f'{self.current_function}${label}'
        return label

    def write_label(self, label: str):
        """第 8 章：label 指令"""
        self._write([
            f'// label {label}',
            f'({self._scoped_label(label)})',
        ])

    def write_goto(self, label: str):
        """第 8 章：goto 指令"""
        self._write([
            f'// goto {label}',
            f'@{self._scoped_label(label)}',
            '0;JMP',
        ])

    def write_if(self, label: str):
        """第 8 章：if-goto 指令（pop 條件值，非 0 則跳轉）"""
        self._write([
            f'// if-goto {label}',
            '@SP',
            'AM=M-1',
            'D=M',
            f'@{self._scoped_label(label)}',
            'D;JNE',
        ])

    def write_function(self, function_name: str, n_vars: int):
        """第 8 章：function 宣告與區域變數歸零"""
        self.current_function = function_name
        self._write([
            f'// function {function_name} {n_vars}',
            f'({function_name})',
        ])
        for _ in range(n_vars):
            self._write([
                '@SP',
                'A=M',
                'M=0',
                '@SP',
                'M=M+1',
            ])

    def write_call(self, function_name: str, n_args: int):
        """第 8 章：call 函式呼叫（保存 caller frame、重設 ARG/LCL、跳轉）"""
        uid = self.label_counter
        self.label_counter += 1
        caller = self.current_function if self.current_function else 'Bootstrap'
        ret_label = f'{caller}$ret.{uid}'

        self._write([f'// call {function_name} {n_args}'])

        # 1. push return-address
        self._write([
            f'@{ret_label}',
            'D=A',
            '@SP',
            'A=M',
            'M=D',
            '@SP',
            'M=M+1',
        ])

        # 2. push LCL, ARG, THIS, THAT
        for reg in ('LCL', 'ARG', 'THIS', 'THAT'):
            self._write([
                f'@{reg}',
                'D=M',
                '@SP',
                'A=M',
                'M=D',
                '@SP',
                'M=M+1',
            ])

        # 3. ARG = SP - 5 - nArgs
        self._write([
            '@SP',
            'D=M',
            f'@{5 + n_args}',
            'D=D-A',
            '@ARG',
            'M=D',
        ])

        # 4. LCL = SP
        self._write([
            '@SP',
            'D=M',
            '@LCL',
            'M=D',
        ])

        # 5. goto functionName & 宣告返回標籤
        self._write([
            f'@{function_name}',
            '0;JMP',
            f'({ret_label})',
        ])

    def write_return(self):
        """第 8 章：return 返回呼叫端並還原 caller frame"""
        self._write([
            '// return',
            # endFrame (R13) = LCL
            '@LCL',
            'D=M',
            '@R13',
            'M=D',
            # retAddr (R14) = *(endFrame - 5)
            '@5',
            'A=D-A',
            'D=M',
            '@R14',
            'M=D',
            # *ARG = pop()
            '@SP',
            'AM=M-1',
            'D=M',
            '@ARG',
            'A=M',
            'M=D',
            # SP = ARG + 1
            '@ARG',
            'D=M+1',
            '@SP',
            'M=D',
        ])

        # 依序還原 THAT, THIS, ARG, LCL
        for offset, reg in enumerate(('THAT', 'THIS', 'ARG', 'LCL'), start=1):
            self._write([
                '@R13',
                'D=M',
                f'@{offset}',
                'A=D-A',
                'D=M',
                f'@{reg}',
                'M=D',
            ])

        # goto retAddr
        self._write([
            '@R14',
            'A=M',
            '0;JMP',
        ])

    def close(self):
        self.out.close()


def translate(target_path: str, write_bootstrap: bool = True):
    target_path = os.path.normpath(target_path)

    if os.path.isdir(target_path):
        vm_files = sorted(
            os.path.join(target_path, f)
            for f in os.listdir(target_path)
            if f.endswith('.vm')
        )
        dir_name = os.path.basename(target_path)
        output_path = os.path.join(target_path, f'{dir_name}.asm')
    else:
        vm_files = [target_path]
        output_path = os.path.splitext(target_path)[0] + '.asm'

    writer = CodeWriter(output_path)

    # 依據第 8 章慣例：專案目錄包含 Sys.vm 時需寫入 Bootstrap code；
    # 單檔測試（如 BasicTest、SimpleFunction）若無 Sys.vm 則不應寫入以免干擾測試腳本
    has_sys = any(os.path.basename(f) == 'Sys.vm' for f in vm_files)
    if write_bootstrap and has_sys:
        writer.write_init()

    for vm_file in vm_files:
        writer.set_file_name(vm_file)
        parser = Parser(vm_file)
        while parser.has_more_lines():
            parser.advance()
            ctype = parser.command_type()
            if ctype == 'C_ARITHMETIC':
                writer.write_arithmetic(parser.arg1())
            elif ctype in ('C_PUSH', 'C_POP'):
                writer.write_push_pop(ctype, parser.arg1(), parser.arg2())
            elif ctype == 'C_LABEL':
                writer.write_label(parser.arg1())
            elif ctype == 'C_GOTO':
                writer.write_goto(parser.arg1())
            elif ctype == 'C_IF':
                writer.write_if(parser.arg1())
            elif ctype == 'C_FUNCTION':
                writer.write_function(parser.arg1(), parser.arg2())
            elif ctype == 'C_CALL':
                writer.write_call(parser.arg1(), parser.arg2())
            elif ctype == 'C_RETURN':
                writer.write_return()

    writer.close()
    print(f'Generated: {output_path}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python VMTranslator.py <file.vm | directory>')
        sys.exit(1)
    translate(sys.argv[1])
