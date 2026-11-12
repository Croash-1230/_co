import sys
import os

class Assembler:
    def __init__(self, filepath):
        self.filepath = filepath
        # 初始化符號表，包含內建符號
        self.symbol_table = {
            "SP": 0, "LCL": 1, "ARG": 2, "THIS": 3, "THAT": 4,
            "SCREEN": 16384, "KBD": 24576
        }
        for i in range(16):
            self.symbol_table[f"R{i}"] = i
            
        # 機器碼對照表
        self.dest_table = {
            None: "000", "M": "001", "D": "010", "MD": "011",
            "A": "100", "AM": "101", "AD": "110", "AMD": "111"
        }
        self.jump_table = {
            None: "000", "JGT": "001", "JEQ": "010", "JGE": "011",
            "JLT": "100", "JNE": "101", "JLE": "110", "JMP": "111"
        }
        self.comp_table = {
            "0": "0101010", "1": "0111111", "-1": "0111010",
            "D": "0001100", "A": "0110000", "!D": "0001101",
            "!A": "0110001", "-D": "0001111", "-A": "0110011",
            "D+1": "0011111", "A+1": "0110111", "D-1": "0001110",
            "A-1": "0110010", "D+A": "0000010", "D-A": "0010011",
            "A-D": "0000111", "D&A": "0000000", "D|A": "0010101",
            # 以 M 開頭的對照 (a=1)
            "M": "1110000", "!M": "1110001", "-M": "1110011",
            "M+1": "1110111", "M-1": "1110010", "D+M": "1000010",
            "D-M": "1010011", "M-D": "1000111", "D&M": "1000000",
            "D|M": "1010101"
        }

    def clean_lines(self, raw_lines):
        """清除註解與前後空白"""
        cleaned = []
        for line in raw_lines:
            # 移除註解
            line = line.split("//")[0].strip()
            if line:
                cleaned.append(line)
        return cleaned

    def first_pass(self, lines):
        """第一階段：掃描所有標籤 (Labels) 並加入符號表"""
        rom_address = 0
        for line in lines:
            if line.startswith("(") and line.endswith(")"):
                label = line[1:-1]
                if label not in self.symbol_table:
                    self.symbol_table[label] = rom_address
            else:
                rom_address += 1

    def second_pass(self, lines):
        """第二階段：翻譯指令並分配變數記憶體位址"""
        machine_code = []
        variable_address = 16  # 變數從 RAM 位址 16 開始配置

        for line in lines:
            if line.startswith("(") and line.endswith(")"):
                continue  # 跳過標籤宣告行

            if line.startswith("@"):
                # A-指令處理
                symbol = line[1:]
                if symbol.isdigit():
                    val = int(symbol)
                else:
                    if symbol not in self.symbol_table:
                        self.symbol_table[symbol] = variable_address
                        variable_address += 1
                    val = self.symbol_table[symbol]
                
                # 轉為 15 位元二進位並加上開頭的 0
                binary_code = format(val, '016b')
                machine_code.append(binary_code)

            else:
                # C-指令處理 (dest=comp;jump)
                dest, comp, jump = None, None, None
                
                if "=" in line:
                    dest_part, rest = line.split("=")
                    dest = dest_part.strip()
                else:
                    rest = line

                if ";" in rest:
                    comp_part, jump_part = rest.split(";")
                    comp = comp_part.strip()
                    jump = jump_part.strip()
                else:
                    comp = rest.strip()

                c_bits = self.comp_table.get(comp, "0000000")
                d_bits = self.dest_table.get(dest, "000")
                j_bits = self.jump_table.get(jump, "000")

                # C指令格式：111 + comp(7) + dest(3) + jump(3)
                binary_code = f"111{c_bits}{d_bits}{j_bits}"
                machine_code.append(binary_code)

        return machine_code

    def assemble(self):
        with open(self.filepath, 'r', encoding='utf-8') as f:
            raw_lines = f.readlines()

        lines = self.clean_lines(raw_lines)
        self.first_pass(lines)
        machine_code = self.second_pass(lines)

        # 輸出 .hack 檔案
        output_path = os.path.splitext(self.filepath)[0] + ".hack"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(machine_code) + "\n")
        
        print(f"組譯完成！輸出檔案至：{output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python assembler.py <filename.asm>")
    else:
        Assembler(sys.argv[1]).assemble()
