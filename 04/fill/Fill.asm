// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// Put your code here.
(LISTEN)
    @KBD
    D=M
    @SET_BLACK
    D;JNE       // If key is pressed (D != 0), jump to set black
    @SET_WHITE
    D;JEQ       // If no key is pressed (D == 0), jump to set white

(SET_BLACK)
    @color
    M=-1        // color = -1 (all bits 1 / black)
    @APPLY_FILL
    0;JMP

(SET_WHITE)
    @color
    M=0         // color = 0 (all bits 0 / white)
    @APPLY_FILL
    0;JMP

(APPLY_FILL)
    @SCREEN
    D=A
    @addr
    M=D         // addr = base address of the screen (16384)

    @8192
    D=A
    @n
    M=D         // n = 8192 (total words in the screen map)

(LOOP)
    @n
    D=M
    @LISTEN
    D;JEQ       // If n == 0, finished filling, go back to listen to keyboard

    @color
    D=M
    @addr
    A=M
    M=D         // RAM[addr] = color

    @addr
    M=M+1       // Increment address to next screen word
    @n
    M=M-1       // Decrement remaining words counter
    
    @LOOP
    0;JMP       // Repeat loop
