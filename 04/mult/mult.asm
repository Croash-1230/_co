// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)

// Put your code here.
// Initialize R2 to 0
    @R2
    M=0

    // Set counter i = R1
    @R1
    D=M
    @i
    M=D

(LOOP)
    // If i == 0, we are done
    @i
    D=M
    @END
    D;JEQ

    // R2 = R2 + R0
    @R0
    D=M
    @R2
    M=D+M

    // i = i - 1
    @i
    M=M-1

    // Jump back to loop
    @LOOP
    0;JMP

(END)
    // Infinite loop to halt the program cleanly
    @END
    0;JMP
