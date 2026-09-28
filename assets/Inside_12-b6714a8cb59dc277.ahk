;Persistent ; Keep the script running
SetTitleMatchMode, 2 ; Allow for partial matching of window titles

; Read the minimal_string from file
FileRead, sequence, section_12.txt

pressDuration := 1 ; For example, hold each key for 50ms
delayBetweenPresses := 270 ; For example, wait 100ms between presses

; Use F9 to start the sequence
F9::
    Sleep, 1000 ; Wait for 1 second before starting
    Send, {RCtrl down} ; Hold right Ctrl key down

    ; Loop through each character in the sequence
    Loop, % StrLen(sequence)
    {
        char := SubStr(sequence, A_Index, 1)
        
        ; Translate U, R, L to corresponding arrow keys
        if (char = "U")
            key := "Up"
        else if (char = "R")
            key := "Right"
        else if (char = "L")
            key := "Left"
        
        Send, {%key% down}
        Sleep, %pressDuration%
        Send, {%key% up}
        ; Don't add a delay after the last key press
        if (A_Index < StrLen(sequence))
        {
            Sleep, %delayBetweenPresses%
        }
    }

    Sleep, 1000 ; Wait for 1 second after the sequence
    Send, {RCtrl up} ; Release right Ctrl key
return
