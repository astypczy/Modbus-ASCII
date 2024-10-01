import serial

arduinoData = serial.Serial('COM9',9600)

RxData = []

# Implementacja funkcji LRC
def Lrc_str(string) -> int:
    lrc = 0
    tmp_str = string[1:]
    lrc = 0
    index = 0
    for i in range(int(len(tmp_str)/2)):
        lrc += fromHex(tmp_str[index] + tmp_str[index+1])
        index += 2
    lrc = ((~lrc) + 1) & 0xff 
    return lrc

# Implementacja zamiany na reprezentację szesnastkową
def toHex(num):
    number = format(num,'02X')
    return number

# Implementacja zamiany ze szesnastkowego na liczbę całkowitą
def fromHex(string):
    if len(string) % 2 != 0:
        return -1
    return int(string, 16)

# Implementacja zamiany na reprezentację szesnastkową jako string
def toHex_str(number, bytes=2):    
    value = ""
    for i in range(bytes):
        ch = number % 16                    # obliczanie reszty z dzielenia przez 16 co odpowiada wartości pojedynczego heksadecymalnego znaku
        if ch > 9:                          # jeśli ch > 9 powinna być użyta litera A-F 
            ch = chr(ch + (ord('A') - 10))  # (ord('A') - 10) odpowiada 65 - 10 dodając resztę z dzielenia większą od 9 otrzymujemy wartości od A do F
        else: 
            ch = chr(ch + ord('0'))         # analogicznie do tego u góry z tą różnicą że gdy ch = 0 otrzymay 0, gdy ch = 1 to otrzymamy 1
        value = ch + value
        number = number // 16               # przechodzenie do kolejniej cyfry
        
    return value

# Implementacja pobierania SlaveID od użytkownika
def ReadSlaveID():
    SlaveID = input('Enter SlaveID (np. 1): ') 
    SlaveID = int(SlaveID)
    return SlaveID

# Implementacja pobierania adresu pierwszego rejestru od użytkownika
def ReadFirstReg():
    FirstReg = int(input('Enter First Register address (np. 4) : '))
    return FirstReg

# Implementacja pobierania liczby rejestrow do odczytu od użytkownika
def ReadNumberOFReg():
    NumberOFReg = 0
    while(NumberOFReg == 0):
        NumberOFReg = int(input('Enter NumberOFReg (np. 4): '))
    return NumberOFReg

# Implementacja pobierania kodu funkcji od użytkownika
def ReadFunctionCode():
    FunctionCode = input('Enter FunctionCode (np. 3): ')
    FunctionCode = int(FunctionCode)
    return FunctionCode

# Implementacja pobierania wartości do zapisu od użytkownika
def ReadValuesToWrite(NumberOFReg):
    ValuesToWrite = []
    for i in range(NumberOFReg):
        print("Enter " + str(i+1) + ". Value to Write: ")
        tmp = input() 
        tmp = int(tmp)
        ValuesToWrite.append(tmp)
    return ValuesToWrite

# Generowanie wiadomości na podstawie podanej funkcji
def function_operation(function, SlaveID):
    if function == 3:               # Function code for readHoldingRegs or Function code for readInputRegs
        message = ':'
        message += toHex(SlaveID)
        message += toHex(FunctionCode)
        first = ReadFirstReg()      # register adress
        message += toHex_str(first, 4)
        number = ReadNumberOFReg()
        message += toHex_str(number,4)
        lrc = Lrc_str(message)
        message += toHex(lrc)
        message += '\r\n'
        
        return message

    elif function == 16:
        ValuesToWrite = []
        message = ':'
        message += toHex(SlaveID)
        message += toHex(FunctionCode)
        first = ReadFirstReg()      # register adress
        message += toHex_str(first, 4)
        number = ReadNumberOFReg()
        message += toHex_str(number,4)
        ValuesToWrite = ReadValuesToWrite(number)
        for i in range(len(ValuesToWrite)):
            message += toHex_str(ValuesToWrite[i],4)
        lrc = Lrc_str(message)
        message += toHex(lrc)
        message += '\r\n'
        return message
    else:
        print("Invalid function")
        return True                 # zwraca true czyli error = true
    
# Implementacja operacji odbioru danych dla funkcji odczytu rejestrów
def recv_operation3(received_int, function):
    if function == 3:              
        segmented_received_int = [received_int[i:i+2] for i in range(0, len(received_int), 2)]
        for i in range(len(segmented_received_int)):
            RxData.append(segmented_received_int[i])
        number_of_bytes = fromHex(str(RxData[2]))
        # | COLON | SLAVE_ID | FUNCTION_CODE | DATA      | LRC     | CRLF  |
        # | 1 BYTE|  2 BYTES |  2 BYTES      | N*4 BYTES | 2 BYTES |2 BYTES|s

        print("Slave ID: 0x" + str(RxData[0]) + ", " + str(fromHex(RxData[0])))
        print("FUNCTION_CODE: 0x" + str(RxData[1]) + ", " + str(fromHex(RxData[1])))
        print("LRC: 0x" + str(RxData[len(RxData)-2]) + ", " + str(fromHex(RxData[len(RxData)-2])))  # -2 bo CR LF
        

        # ASCII na hex
        segmented_registers = segmented_received_int[3:len(segmented_received_int)-2]  # -2 bo CR LF
        string_register = []
        index = 0
        for i in range(int(number_of_bytes/2)):
            string_register.append(str(segmented_registers[index]) + str(segmented_registers[index+1]))
            index += 2
        for i in range(int(number_of_bytes/2)):
            print("Register "+str(i+1)+ ".value: " + str(fromHex(string_register[i])))

    else:
        print("Invalid function")
        return True

# Implementacja operacji odbioru danych dla funkcji zapisu wielu rejestrów
def recv_operation16(received_int, function):
    if function == 16:               
        segmented_received_int = [received_int[i:i+2] for i in range(0, len(received_int), 2)]
        for i in range(len(segmented_received_int)):
            RxData.append(segmented_received_int[i])
        registers_val = ""
        # | COLON | SLAVE_ID | FUNCTION_CODE | DATA      | LRC     | CRLF  |
        # | 1 BYTE|  2 BYTES |  2 BYTES      | N*4 BYTES | 2 BYTES |2 BYTES|s

        print("Slave ID: 0x" + str(RxData[0]) + ", " + str(fromHex(RxData[0])))
        print("FUNCTION_CODE: 0x" + str(RxData[1]) + ", " + str(fromHex(RxData[1])))
        print("LRC: 0x" + str(RxData[len(RxData)-2]) + ", " + str(fromHex(RxData[len(RxData)-2])))  # -2 bo CR LF
        print("Waiting for registers values...")
        while not registers_val:
            registers_val = arduinoData.readline().decode().strip()
        print(registers_val)

    else:
        print("Invalid function")
        return True

# | COLON | SLAVE_ID | FUNCTION_CODE | DATA      | LRC     | CRLF  |
# | 1 BYTE|  2 BYTES |  2 BYTES      | N*4 BYTES | 2 BYTES |2 BYTES|s

# static const uint16_t Input_Registers_Database[50]={
#     0,  1111,  2222,  3333,  4444,  5555,  6666,  7777,  8888,  9999,      // 0-9   40001-40010
#     12345, 15432, 15535, 10234, 19876, 13579, 10293, 19827, 13456, 14567,  // 10-19 40011-40020
#     21345, 22345, 24567, 25678, 26789, 24680, 20394, 29384, 26937, 0,      // 20-29 40021-40030
#     1, 2, 3, 4, 5, 60, 7, 8, 9, 10,                                        // 30-39 40031-40040
#     11, 23, 22, 343, 55, 86, 453, 22, 654, 1232,                           // 40-49 40041-40050
# };
SlaveID = ReadSlaveID() # Inicjalizacja zmiennej SlaveID poprzez wywołanie funkcji ReadSlaveID(), która pobiera identyfikator SlaveID od użytkownika
FunctionCode = ReadFunctionCode() # Inicjalizacja zmiennej FunctionCode poprzez wywołanie funkcji ReadFunctionCode(), która pobiera kod funkcji od użytkownika

message = function_operation(FunctionCode, SlaveID) # Generowanie wiadomości do wysłania poprzez wywołanie funkcji function_operation(FunctionCode, SlaveID)

if(message != True):
    print(f"Send message-> {message}")

    arduinoData.write(message.encode()) # Zapisanie wygenerowanej wiadomości do Arduino
    received_int = arduinoData.readline().decode() # Oczekiwanie i odebranie danych z Arduino poprzez arduinoData.readline().decode() i zapisanie ich do zmiennej received_int
    print(f"Received message-> {received_int}")

    received_int = received_int[1:] # usuwanie : 
    if(received_int[2] == "8"): # Sprawdzenie, czy trzeci znak received_int to "8". Jeśli tak, oznacza to wystąpienie błędu w odpowiedzi slave. Następnie sprawdzane są konkretne kody błędów i wyświetlane odpowiednie komunikaty
        print("Error detected by slave")
        if(fromHex(received_int[4]+received_int[5]) == 1):
            print("ILLEGAL_FUNCTION")
        elif(fromHex(received_int[4]+received_int[5]) == 2):
            print("ILLEGAL_DATA_ADDRESS")
        elif(fromHex(received_int[4]+received_int[5]) == 3):
            print("ILLEGAL_DATA_VALUE")
        elif(fromHex(received_int[4]+received_int[5]) == 4):
            print("SLAVE_DEVICE_FAILURE")
    else:
        if(FunctionCode == 3):
            recv_operation3(received_int, FunctionCode)  
        elif(FunctionCode == 16):
            recv_operation16(received_int, FunctionCode)  
            
        else:
            print("ILLEGAL_FUNCTION")
