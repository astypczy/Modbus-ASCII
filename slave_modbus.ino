#include <LiquidCrystal.h>
#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <Arduino.h>

#define SLAVE_ID 1

#define ILLEGAL_FUNCTION       1  //:0180017E
#define ILLEGAL_DATA_ADDRESS   2  //:0180027D
#define ILLEGAL_DATA_VALUE     3  //:0180037C
#define SLAVE_DEVICE_FAILURE   4

LiquidCrystal lcd(7, 8, 9, 10, 11, 12);

const int n = 255;            // Max msg length
char RxData[n] = { 0 };       // Input buffer
int dwBytesRead = 0;          // Number of received bytes

//Master is able to modify 
static uint16_t Holding_Registers_Database[50]={
    0,  1111,  2222,  3333,  4444,  5555,  6666,  7777,  8888,  9999,      // 0-9   40001-40010
    12345, 15432, 15535, 10234, 19876, 13579, 10293, 19827, 13456, 14567,  // 10-19 40011-40020
    21345, 22345, 24567, 25678, 26789, 24680, 20394, 29384, 26937, 0,      // 20-29 40021-40030
    1, 2, 3, 4, 5, 60, 7, 8, 9, 10,                                        // 30-39 40031-40040
    11, 23, 22, 343, 55, 86, 453, 22, 654, 1232,                           // 40-49 40041-40050
};

//Master is NOT able to modify 
static const uint16_t Input_Registers_Database[50]={
    0,  1111,  2222,  3333,  4444,  5555,  6666,  7777,  8888,  9999,      // 0-9   40001-40010
    12345, 15432, 15535, 10234, 19876, 13579, 10293, 19827, 13456, 14567,  // 10-19 40011-40020
    21345, 22345, 24567, 25678, 26789, 24680, 20394, 29384, 26937, 0,      // 20-29 40021-40030
    1, 2, 3, 4, 5, 60, 7, 8, 9, 10,                                        // 30-39 40031-40040
    11, 23, 22, 343, 55, 86, 453, 22, 654, 1232,                           // 40-49 40041-40050
};

//konwertowanie liczby na stringa
String toHex_str(int number, int bytes = 2) {  
  String value;
  for (int i = 0; i < bytes; ++i) {
    char ch = number % 16 + (((number % 16) > 9) ? ('A' - 10) : '0');
    value = String(ch) + value;
    number = (number / 16);
  }
  
  return value;
}

int fromHex(String str) {
    return (int)strtol(str.c_str(), NULL, 16);
}

int LRC(String str) {
  str = str.substring(1);
  int calculated_lrc = 0;
  
  for (int i = 0; i < str.length(); i += 2) {
    calculated_lrc = (calculated_lrc + fromHex(str.substring(i, i + 2))) & 255;
  }
  
  return (((calculated_lrc ^ 255) + 1) & 255);
}

String buildExceptionResponse(String query, int Exception) {
  String response;
  response = query.substring(0, 5);
  response.setCharAt(3, '8');
  response += toHex_str(Exception, 2);
  response += toHex_str(LRC(response));
  response += "\r\n";
  return response;
}

String readHoldingRegs(String message_str)
{
  String message_out;
  int number_of_registers;
  int first_register;
  int calculated_lrc;

  //| COLON | SLAVE_ID | FUNCTION_CODE | DATA      | LRC     | CRLF  |
  //| 1 BYTE|  2 BYTES |  2 BYTES      | N*4 BYTES | 2 BYTES |2 BYTES|s
  message_out += String(message_str.substring(0, 5));
  number_of_registers = fromHex(message_str.substring(9, 13));
  message_out += String(toHex_str(number_of_registers * 2));
  first_register = fromHex(message_str.substring(5, 9));
  for (int currentReg = 0; currentReg < number_of_registers; ++currentReg) {
      message_out += String(toHex_str(Input_Registers_Database[first_register + currentReg], 4));
  }
  calculated_lrc = LRC(message_out);
  message_out += String(toHex_str(calculated_lrc));
  message_out += String("\r\n");
  if (first_register + number_of_registers >= 50) { //tyle rejestrów
      lcd.print("ERR: Wrong Addreses");
      message_out = buildExceptionResponse(message_str, ILLEGAL_DATA_ADDRESS);
  }

  return message_out;
      
}

String dataString = "";
String writeHoldingRegs(String message_str)
{
  String message_out;
  int number_of_registers;
  int first_register;
  int calculated_lrc;

  message_out += message_str.substring(0, 5);
  number_of_registers = fromHex(message_str.substring(9, 13));
  first_register = fromHex(message_str.substring(5, 9));
  message_out += toHex_str(first_register, 4);
  message_out += toHex_str(number_of_registers*2, 4);
  if (first_register + number_of_registers >= 50) {
      lcd.print("ERR: Wrong Addreses");
      message_out = buildExceptionResponse(message_str, ILLEGAL_DATA_ADDRESS);
  }
  for (int currentReg = 0; currentReg < number_of_registers; ++currentReg) {
      Holding_Registers_Database[first_register + currentReg] = fromHex(message_str.substring(13 + 4 * currentReg, 17 + 4 * currentReg));
      dataString += "Holding_Registers_Database[" +String(first_register + currentReg) + "]= " + String(Holding_Registers_Database[first_register + currentReg]) + ", ";
  }
  calculated_lrc = LRC(message_out);
  message_out += toHex_str(calculated_lrc);
  message_out += "\r\n";

  return message_out;  
}
void setup() {
  Serial.begin(9600);
  lcd.begin(16, 2);
}
 
 
void loop() 
{
  bool error = false;
  
  while (dwBytesRead == 0) // Polling the port for data
  {           
    dwBytesRead = Serial.readBytes(RxData, n);
  }
  lcd.clear();

  String message_str(RxData);
  String message_out = "";

  for (size_t i = 0; i < message_str.length(); ++i) 
  {
    if (message_str[i] == '\r') message_str.setCharAt(i, 'r');
    if (message_str[i] == '\n') message_str.setCharAt(i, 'n');
  }

  int slave_addr = fromHex(message_str.substring(1, 3));
  int function_number = fromHex(message_str.substring(3, 5));
  if (message_str[0] != ':') {
      lcd.setCursor(0, 0);
      lcd.print("ERR: Wrong, without :");
      error = true;
  }
  if (message_str.substring(message_str.length()-2) != "rn") {
      lcd.setCursor(0, 0);
      lcd.print("ERR: Wrong,");
      lcd.setCursor(0, 1);
      lcd.print("without \r\n");
      delay(2000);
      error = true;
  }
  if (error) {
      lcd.setCursor(0, 0);
      lcd.print("ERR: ERRORS ");
      lcd.setCursor(0, 1);
      lcd.print("Occured");
      delay(2000);
      message_out = buildExceptionResponse(message_str,SLAVE_DEVICE_FAILURE);
      
  }
  if (slave_addr != SLAVE_ID) {
    lcd.setCursor(0, 0);
    lcd.print("ERR: Wrong ID");
    delay(2000);
    message_out = buildExceptionResponse(message_str,ILLEGAL_DATA_VALUE);
    error = true;
  }
  
  if(error == false)
  {
     switch (function_number)
    {
      case 3:
        message_out = readHoldingRegs(message_str);
        break;
      case 16:
        message_out = writeHoldingRegs(message_str);
        break;
        
      default:
        lcd.print("ERR: Wrong Function");
        message_out = buildExceptionResponse(message_str, ILLEGAL_FUNCTION);
        break;
    }
  }
  Serial.println(message_out);
  if(function_number == 16)
  {
    delay(2000);
    Serial.println(dataString);
    
  }
  RxData[n + 1] = { 0 };    // Input buffer
  dwBytesRead = 0;          // Number of received bytes
  dataString = "";
}
