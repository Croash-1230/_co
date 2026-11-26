#Nand2Tetris VM Translator (Chapters 7 & 8)
本專案實作 Nand2Tetris（《計算機系統要素》第 2 版）第 7 章與第 8 章的虛擬機轉譯器（VM Translator），將堆疊導向的虛擬機指令（.vm）轉譯為 Hack 平台組合語言（.asm）。

#專案架構
Parser：讀取單一 .vm 檔案，移除 // 註解與多餘空白，拆解指令類型（C_ARITHMETIC、C_PUSH、C_POP、C_LABEL、C_GOTO、C_IF、C_FUNCTION、C_RETURN、C_CALL）與參數。

CodeWriter：依 Hack 標準記憶體映射產生組合語言，管理目前函式名稱、唯一標籤計數器、啟動碼（Bootstrap code）與呼叫堆疊框架。

translate（主驅動程式）：支援轉譯單一 .vm 檔案或整個專案資料夾（合併輸出為 <資料夾名稱>.asm），並在目錄包含 Sys.vm 時自動插入啟動碼。

支援的 VM 指令集
第 7 章：算術、邏輯與記憶體存取
算術與邏輯：add、sub、neg、eq、gt、lt、and、or、not（布林真值為 -1、假值為 0）。

記憶體區段（push / pop）：constant、local、argument、this、that、static（命名為 檔名.i）、temp（RAM[5..12]）、pointer（0 對應 THIS，1 對應 THAT）。

第 8 章：流程控制與函式呼叫
流程控制：label、goto、if-goto（函式內標籤自動加上 函式名稱$ 前綴避免衝突）。

函式呼叫：function、call、return（完整保存與還原 LCL、ARG、THIS、THAT 與返回位址）。

使用方式
1. 轉譯單一 .vm 檔案
適用於第 7 章測試（如 SimpleAdd、StackTest、BasicTest、PointerTest、StaticTest）與第 8 章單檔測試（如 BasicLoop、FibonacciSeries、SimpleFunction）：

Bash
python VMTranslator.py path/to/BasicTest.vm
執行後會在同目錄產生 BasicTest.asm。

2. 轉譯整個專案資料夾
適用於第 8 章多檔專案（如 FibonacciElement、StaticsTest）：

Bash
python VMTranslator.py path/to/FibonacciElement
執行後會在資料夾內產生 FibonacciElement.asm。若資料夾中包含 Sys.vm，轉譯器會自動在最前方寫入 Bootstrap 啟動碼（設定 SP = 256 並呼叫 Sys.init）。

測試建議
在 Nand2Tetris 的 CPU Emulator 中載入產生的 .asm 檔案。

載入對應的 .tst 測試腳本並執行，將輸出的 .out 結果與官方 .cmp 比對。
