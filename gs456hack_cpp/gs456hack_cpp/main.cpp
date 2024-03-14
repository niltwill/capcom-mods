#include "pch.h"

//
// Global variables
//

// declare instance to use public stuff from gs456hack.h
GS456Hack& gs456hack = GS456Hack::instance();

// for the process ID
DWORD pid;

// the game's process name
const char* processName = "GS456.exe";

// memory addresses (64-bit)
uintptr_t gameFPS = 0x2000080837C; // float
uintptr_t animSpd = 0x20000808378; // float
//uintptr_t textSpd = 0x20001909860; // [not valid]

// variable to temporarily store the (float) values
float floatValue;

// to be used in KeyPressThread()
float currentVal;

// to be used in ProcessNextValue()
unsigned short int currentFPS = 0;
unsigned short int currentAnimSpd = 0;

// this is to be used in KeyPressThread(), related to earlier variables
bool skipFirstElementFPS = false;
bool skipFirstElementAnimSpd = false;

// will be used in KeyPressThread()
bool wasFPSKeyPressedLastFrame = false;
bool wasAnimSpeedKeyPressedLastFrame = false;

// will be used by ControllerPressThread()
std::unordered_set<WORD> pressedButtons;
std::unordered_set<WORD> pressedTriggers;

// this is only used to quit from the main thread's loop after all memhacks have been applied
// (that thread no longer serves any purpose after that)
unsigned char operationSuccess = 0;


///
/// helper functions (begin)
///

// to find processes by name
HWND FindWindowByProcessName(const char* processName) {
    // Convert the process name to a wide character string
    int wideCharLength = MultiByteToWideChar(CP_UTF8, 0, processName, -1, nullptr, 0);
    if (wideCharLength == 0) {
        // Error handling
        gs456hack.Log("Error: MultiByteToWideChar failed. Error code: ", GetLastError());
        return nullptr;
    }

    wchar_t* wideProcessName = new wchar_t[wideCharLength];
    MultiByteToWideChar(CP_UTF8, 0, processName, -1, wideProcessName, wideCharLength);

    // Step 1: Enumerate processes to find the process ID (PID) of the target process
    PROCESSENTRY32 processEntry;
    processEntry.dwSize = sizeof(PROCESSENTRY32);

    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (Process32First(snapshot, &processEntry)) {
        do {
            if (_wcsicmp(processEntry.szExeFile, wideProcessName) == 0) {
                // Found the process ID (PID) of the target process
                DWORD targetPID = processEntry.th32ProcessID;

                // Step 2: Obtain the main window handle of the process
                HWND hWnd = nullptr;
                do {
                    hWnd = FindWindowEx(nullptr, hWnd, nullptr, nullptr);
                    DWORD processID;
                    GetWindowThreadProcessId(hWnd, &processID);

                    if (processID == targetPID) {
                        // Step 3: Check if the main window belongs to the desired process
                        delete[] wideProcessName;  // clean up allocated memory
                        return hWnd;
                    }
                } while (hWnd != nullptr);
            }
        } while (Process32Next(snapshot, &processEntry));
    }

    CloseHandle(snapshot);

    delete[] wideProcessName;  // clean up allocated memory
    return nullptr; // window was not found
}

// to read a float value from a memory address
bool ReadFloatValue(HANDLE pHandle, uintptr_t memAddress, float& result) {
    SIZE_T bytesRead;
    if (ReadProcessMemory(pHandle, reinterpret_cast<LPCVOID>(memAddress), &result, sizeof(result), &bytesRead) && bytesRead == sizeof(result)) {
        return true;
    }
    else {
        // Handle the error
        gs456hack.Log("Error: ReadProcessMemory failed. Error code : ", GetLastError());
        return false;
    }
}

// to write a float value into a memory address
bool WriteFloatValue(HANDLE pHandle, uintptr_t memAddress, float value) {
    if (WriteProcessMemory(pHandle, reinterpret_cast<LPVOID>(memAddress), &value, sizeof(value), nullptr)) {
        return true;
    }
    else {
        // Handle the error
        gs456hack.Log("Error: WriteProcessMemory operation failed. Error code: ", GetLastError());
        return false;
    }
}

// Function to check if the active window belongs to a specific process (for the hotkeys)
bool IsTargetProcessActive() {
    HWND foregroundWindow = GetForegroundWindow();
    const char* targetProcessName = processName;

    DWORD processId;
    GetWindowThreadProcessId(foregroundWindow, &processId);

    HANDLE hProcess = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, FALSE, processId);
    if (hProcess) {
        char processName[MAX_PATH];
        GetModuleBaseNameA(hProcess, NULL, processName, sizeof(processName) / sizeof(char));

        CloseHandle(hProcess);

        // Compare the process name with the target process name
        return _stricmp(processName, targetProcessName) == 0;
    }

    return false;
}

// Function to cycle through given values
int ProcessNextValue(uintptr_t memAddress, GS456Hack& gs456hack, std::vector<int>& Values, const char* logMsg1, const char* logMsg2, const char* logMsg3,
    std::string source, unsigned short int current_Value = 0)
{
    // get the game's process
    HWND hWnd = FindWindowByProcessName(processName);
    if (hWnd != nullptr) {
        // window found
        GetWindowThreadProcessId(hWnd, &pid);
        HANDLE pHandle = OpenProcess(PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION, FALSE, pid);

        // make sure it is not empty without any values
        if (!Values.empty()) {
            // get current array element
            currentVal = static_cast<decltype(currentVal)>(Values[current_Value]);

            // read and write memory
            if (ReadFloatValue(pHandle, memAddress, floatValue)) {
                floatValue = currentVal;
                if (WriteFloatValue(pHandle, memAddress, floatValue)) {
                    gs456hack.Log(logMsg1, floatValue, " with ", source);
                }
                else {
                    gs456hack.Log(logMsg2, floatValue, " with ", source);
                }
            }
            else {
                gs456hack.Log(logMsg3, memAddress);
            }
        }

        CloseHandle(pHandle);

        // increase this if haven't reached the end
        if (current_Value + 1 > static_cast<unsigned short int>(Values.size()) - 1) {
            current_Value = 0; // if at the final element, restart from first element
        }
        else {
            current_Value++;
        }
        return current_Value;
    }
    return current_Value;
}

void ProcessNextFPSValue(int source, bool isHotkey) {
    // Change format if hotkey or controller
    std::ostringstream oss;
    if (isHotkey) {
        oss << "hotkey 0x" << std::hex << source << " (keyboard)";
    }
    else {
        oss << "button " << source << " (controller)";
    }
    std::string sourceString = oss.str();

    if (gs456hack.skipListFirstValues_enabled && !skipFirstElementFPS) {
        currentFPS++;
        skipFirstElementFPS = true;
    }

    // Change FPS
    currentFPS = ProcessNextValue(gameFPS, gs456hack, gs456hack.FPS_Values,
        "Process: FPS cap is set to ", "Error: Failed to set the game's FPS cap to: ", "Error: Failed to read the game's FPS cap at: ", sourceString, currentFPS);
}

void ProcessNextAnimSpeedValue(int source, bool isHotkey) {
    // Change format if hotkey or controller
    std::ostringstream oss;
    if (isHotkey) {
        oss << "hotkey 0x" << std::hex << source << " (keyboard)";
    }
    else {
        oss << "button " << source << " (controller)";
    }
    std::string sourceString = oss.str();

    if (gs456hack.skipListFirstValues_enabled && !skipFirstElementAnimSpd) {
        currentAnimSpd++;
        skipFirstElementAnimSpd = true;
    }

    // Change AnimSpeed
    currentAnimSpd = ProcessNextValue(animSpd, gs456hack, gs456hack.AnimSpeed_Values,
        "Process: Animation speed is set to ", "Error: Failed to set the game's animation speed to: ", "Error: Failed to read the game's animation speed at: ", sourceString, currentAnimSpd);
}

//
// helper functions (end)
//


// Function to continuously check for key presses in a separate thread
DWORD WINAPI KeyPressThread(LPVOID hModule) {

    // if config file did not process yet or multipleValues is disabled, don't do much
    while (!gs456hack.config_readable) {
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }

    if (!gs456hack.multipleValues_enabled) {
        return 0;
    }

    // Some sleep is needed first of all, otherwise this will not load properly, if at all
    std::this_thread::sleep_for(std::chrono::milliseconds(gs456hack.WaitBeforeMain));

    while (true) {

        // Check if the active window belongs to the target process
        if (IsTargetProcessActive()) {

            // Check if FPS key is pressed
            if ((GetAsyncKeyState(gs456hack.FPS_keyCode) & 0x8001) && !wasFPSKeyPressedLastFrame) {
                // FPS key is pressed for the first time, process the next value
                ProcessNextFPSValue(gs456hack.FPS_keyCode, true);

                // Set the flag to indicate that the key was pressed in this frame
                wasFPSKeyPressedLastFrame = true;
            }
            else if (!(GetAsyncKeyState(gs456hack.FPS_keyCode) & 0x8001)) {
                // FPS hotkey is not pressed, reset the flag
                wasFPSKeyPressedLastFrame = false;
            }

            // Check if AnimSpeed key is pressed
            if ((GetAsyncKeyState(gs456hack.AnimSpeed_keyCode) & 0x8001) && !wasAnimSpeedKeyPressedLastFrame) {
                // AnimSpeed hotkey is pressed for the first time, process the next value
                ProcessNextAnimSpeedValue(gs456hack.AnimSpeed_keyCode, true);

                // Set the flag to indicate that the key was pressed in this frame
                wasAnimSpeedKeyPressedLastFrame = true;
            }
            else if (!(GetAsyncKeyState(gs456hack.AnimSpeed_keyCode) & 0x8001)) {
                // AnimSpeed hotkey is not pressed, reset the flag
                wasAnimSpeedKeyPressedLastFrame = false;
            }

        }

        // Add a delay to avoid high CPU usage
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
    return 0;
}

// Function to continuously check for gamepad button presses in a separate thread
DWORD WINAPI ControllerPressThread(LPVOID hModule) {

    // if config file did not process yet or multipleValues is disabled, don't do much
    while (!gs456hack.config_readable) {
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }

    if (!gs456hack.multipleValues_enabled) {
        return 0;
    }

    // Some sleep is needed first of all, otherwise this will not load properly, if at all
    std::this_thread::sleep_for(std::chrono::milliseconds(gs456hack.WaitBeforeMain));

    while (true) {

        // Check if the active window belongs to the target process
        if (IsTargetProcessActive()) {

            for (DWORD controllerIndex = 0; controllerIndex < gs456hack.MAX_CONTROLLERS; ++controllerIndex) {
                XINPUT_STATE state;
                ZeroMemory(&state, sizeof(XINPUT_STATE));

                // Get the state of the controller
                if (XInputGetState(controllerIndex, &state) == ERROR_SUCCESS) {

                    // Check all buttons and react like with the keyboard hotkeys earlier

                    // if A was pressed
                    if (gs456hack.CheckButtonState("A", XINPUT_GAMEPAD_A, state, controllerIndex, pressedButtons)) {
                        if (gs456hack.FPS_BUTTON == 1 && gs456hack.ANIMSP_BUTTON != 1) {
                            ProcessNextFPSValue(1, false);
                        }
                        else if (gs456hack.FPS_BUTTON != 1 && gs456hack.ANIMSP_BUTTON == 1) {
                            ProcessNextAnimSpeedValue(1, false);
                        }
                    }

                    // if B was pressed
                    if (gs456hack.CheckButtonState("B", XINPUT_GAMEPAD_B, state, controllerIndex, pressedButtons)) {
                        if (gs456hack.FPS_BUTTON == 2 && gs456hack.ANIMSP_BUTTON != 2) {
                            ProcessNextFPSValue(2, false);
                        }
                        else if (gs456hack.FPS_BUTTON != 2 && gs456hack.ANIMSP_BUTTON == 2) {
                            ProcessNextAnimSpeedValue(2, false);
                        }
                    }

                    // if X was pressed
                    if (gs456hack.CheckButtonState("X", XINPUT_GAMEPAD_X, state, controllerIndex, pressedButtons)) {
                        if (gs456hack.FPS_BUTTON == 3 && gs456hack.ANIMSP_BUTTON != 3) {
                            ProcessNextFPSValue(3, false);
                        }
                        else if (gs456hack.FPS_BUTTON != 3 && gs456hack.ANIMSP_BUTTON == 3) {
                            ProcessNextAnimSpeedValue(3, false);
                        }
                    }

                    // if Y was pressed
                    if (gs456hack.CheckButtonState("Y", XINPUT_GAMEPAD_Y, state, controllerIndex, pressedButtons)) {
                        if (gs456hack.FPS_BUTTON == 4 && gs456hack.ANIMSP_BUTTON != 4) {
                            ProcessNextFPSValue(4, false);
                        }
                        else if (gs456hack.FPS_BUTTON != 4 && gs456hack.ANIMSP_BUTTON == 4) {
                            ProcessNextAnimSpeedValue(4, false);
                        }
                    }

                    // if LB was pressed
                    if (gs456hack.CheckButtonState("LB", XINPUT_GAMEPAD_LEFT_SHOULDER, state, controllerIndex, pressedButtons)) {
                        if (gs456hack.FPS_BUTTON == 5 && gs456hack.ANIMSP_BUTTON != 5) {
                            ProcessNextFPSValue(5, false);
                        }
                        else if (gs456hack.FPS_BUTTON != 5 && gs456hack.ANIMSP_BUTTON == 5) {
                            ProcessNextAnimSpeedValue(5, false);
                        }
                    }

                    // if RB was pressed
                    if (gs456hack.CheckButtonState("RB", XINPUT_GAMEPAD_RIGHT_SHOULDER, state, controllerIndex, pressedButtons)) {
                        if (gs456hack.FPS_BUTTON == 6 && gs456hack.ANIMSP_BUTTON != 6) {
                            ProcessNextFPSValue(6, false);
                        }
                        else if (gs456hack.FPS_BUTTON != 6 && gs456hack.ANIMSP_BUTTON == 6) {
                            ProcessNextAnimSpeedValue(6, false);
                        }
                    }

                    // if Back was pressed
                    if (gs456hack.CheckButtonState("Back", XINPUT_GAMEPAD_BACK, state, controllerIndex, pressedButtons)) {
                        if (gs456hack.FPS_BUTTON == 7 && gs456hack.ANIMSP_BUTTON != 7) {
                            ProcessNextFPSValue(7, false);
                        }
                        else if (gs456hack.FPS_BUTTON != 7 && gs456hack.ANIMSP_BUTTON == 7) {
                            ProcessNextAnimSpeedValue(7, false);
                        }
                    }

                    // if Start was pressed
                    if (gs456hack.CheckButtonState("Start", XINPUT_GAMEPAD_START, state, controllerIndex, pressedButtons)) {
                        if (gs456hack.FPS_BUTTON == 8 && gs456hack.ANIMSP_BUTTON != 8) {
                            ProcessNextFPSValue(8, false);
                        }
                        else if (gs456hack.FPS_BUTTON != 8 && gs456hack.ANIMSP_BUTTON == 8) {
                            ProcessNextAnimSpeedValue(8, false);
                        }
                    }

                    // if LS was pressed
                    if (gs456hack.CheckButtonState("LS", XINPUT_GAMEPAD_LEFT_THUMB, state, controllerIndex, pressedButtons)) {
                        if (gs456hack.FPS_BUTTON == 9 && gs456hack.ANIMSP_BUTTON != 9) {
                            ProcessNextFPSValue(9, false);
                        }
                        else if (gs456hack.FPS_BUTTON != 9 && gs456hack.ANIMSP_BUTTON == 9) {
                            ProcessNextAnimSpeedValue(9, false);
                        }
                    }

                    // if RS was pressed
                    if (gs456hack.CheckButtonState("RS", XINPUT_GAMEPAD_RIGHT_THUMB, state, controllerIndex, pressedButtons)) {
                        if (gs456hack.FPS_BUTTON == 10 && gs456hack.ANIMSP_BUTTON != 10) {
                            ProcessNextFPSValue(10, false);
                        }
                        else if (gs456hack.FPS_BUTTON != 10 && gs456hack.ANIMSP_BUTTON == 10) {
                            ProcessNextAnimSpeedValue(10, false);
                        }
                    }

                    // if DPad Up was pressed
                    if (gs456hack.CheckButtonState("DPad Up", XINPUT_GAMEPAD_DPAD_UP, state, controllerIndex, pressedButtons)) {
                        if (gs456hack.FPS_BUTTON == 11 && gs456hack.ANIMSP_BUTTON != 11) {
                            ProcessNextFPSValue(11, false);
                        }
                        else if (gs456hack.FPS_BUTTON != 11 && gs456hack.ANIMSP_BUTTON == 11) {
                            ProcessNextAnimSpeedValue(11, false);
                        }
                    }

                    // if DPad Down was pressed
                    if (gs456hack.CheckButtonState("DPad Down", XINPUT_GAMEPAD_DPAD_DOWN, state, controllerIndex, pressedButtons)) {
                        if (gs456hack.FPS_BUTTON == 12 && gs456hack.ANIMSP_BUTTON != 12) {
                            ProcessNextFPSValue(12, false);
                        }
                        else if (gs456hack.FPS_BUTTON != 12 && gs456hack.ANIMSP_BUTTON == 12) {
                            ProcessNextAnimSpeedValue(12, false);
                        }
                    }

                    // if DPad Left was pressed
                    if (gs456hack.CheckButtonState("DPad Left", XINPUT_GAMEPAD_DPAD_LEFT, state, controllerIndex, pressedButtons)) {
                        if (gs456hack.FPS_BUTTON == 13 && gs456hack.ANIMSP_BUTTON != 13) {
                            ProcessNextFPSValue(13, false);
                        }
                        else if (gs456hack.FPS_BUTTON != 13 && gs456hack.ANIMSP_BUTTON == 13) {
                            ProcessNextAnimSpeedValue(13, false);
                        }
                    }

                    // if DPad Right was pressed
                    if (gs456hack.CheckButtonState("DPad Right", XINPUT_GAMEPAD_DPAD_RIGHT, state, controllerIndex, pressedButtons)) {
                        if (gs456hack.FPS_BUTTON == 14 && gs456hack.ANIMSP_BUTTON != 14) {
                            ProcessNextFPSValue(14, false);
                        }
                        else if (gs456hack.FPS_BUTTON != 14 && gs456hack.ANIMSP_BUTTON == 14) {
                            ProcessNextAnimSpeedValue(14, false);
                        }
                    }

                    // if LT was pressed
                    if (gs456hack.CheckTriggerState("LT", state.Gamepad.bLeftTrigger, controllerIndex, pressedTriggers)) {
                        if (gs456hack.FPS_BUTTON == 15 && gs456hack.ANIMSP_BUTTON != 15) {
                            ProcessNextFPSValue(15, false);
                        }
                        else if (gs456hack.FPS_BUTTON != 15 && gs456hack.ANIMSP_BUTTON == 15) {
                            ProcessNextAnimSpeedValue(15, false);
                        }
                    }

                    // if RT was pressed
                    if (gs456hack.CheckTriggerState("RT", state.Gamepad.bRightTrigger, controllerIndex, pressedTriggers)) {
                        if (gs456hack.FPS_BUTTON == 16 && gs456hack.ANIMSP_BUTTON != 16) {
                            ProcessNextFPSValue(16, false);
                        }
                        else if (gs456hack.FPS_BUTTON != 16 && gs456hack.ANIMSP_BUTTON == 16) {
                            ProcessNextAnimSpeedValue(16, false);
                        }
                    }

                }
            }
        }

        // Add a delay to avoid high CPU usage
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
    return 0;
}

int SetInitialAddress(intptr_t memAddress, GS456Hack& gs456hack, float& new_Value, const char* logMsg1, const char* logMsg2, const char* logMsg3, const char* logMsg4) {
    // It's probably better to grab this app by its process name, as the title and class can change in the future
    // (or it might trigger different language/localization issues)
    //const char* windowTitle = "Apollo Justice: Ace Attorney Trilogy";
    //const char* className = "via";

    // find the window
    //HWND hWnd = FindWindowA(className, windowTitle);
    HWND hWnd = FindWindowByProcessName(processName);

    if (hWnd != nullptr) {
        // window found!
        GetWindowThreadProcessId(hWnd, &pid);
        HANDLE pHandle = OpenProcess(PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION, FALSE, pid);

        if (pHandle == nullptr) {
            gs456hack.Log("Error: Failed to open the game's process");
            return 1;
        }

        if (ReadFloatValue(pHandle, memAddress, floatValue)) {
            floatValue = new_Value;
            if (floatValue > 0) {
                if (WriteFloatValue(pHandle, memAddress, floatValue)) {
                    gs456hack.Log(logMsg1, floatValue);
                    operationSuccess++;
                }
                else {
                    gs456hack.Log(logMsg2, floatValue);
                }
            }
            else {
                gs456hack.Log(logMsg3);
                operationSuccess++;
            }
        }
        else {
            gs456hack.Log(logMsg4, memAddress);
        }

        CloseHandle(pHandle);
    }
    else {
        gs456hack.Log("Error: The \"Apollo Justice: Ace Attorney Trilogy\" process could not be found");
        return 1;
    }
    return 0;
}

// Quickly read only the log status
void ReadLogStatus()
{
    // Try reading the 'GS456_hacks.ini' to obtain data
    std::ifstream stream(CProxyStub::instance().m_proxy_path / gs456hack.cfname);

    if (stream.good() || !stream.fail())
    {
        // Create an unordered_map to store key-value pairs
        std::unordered_map<std::string, std::string> keyValuePairs;

        // Read lines until the end of the file
        std::string line;
        while (std::getline(stream, line)) {
            // Skip empty lines and lines starting with '#'
            if (line.empty() || line[0] == '#') {
                continue;
            }

            // get rid of whitespaces
            gs456hack.trim(line);

            // Find the position of '=' in the line
            size_t equalPos = line.find('=');

            // If '=' is found, treat the line as a key-value pair
            if (equalPos != std::string::npos) {
                std::string key = line.substr(0, equalPos);
                std::string value = line.substr(equalPos + 1);

                // Store the key-value pair in the map
                keyValuePairs[key] = value;
            }
        }

        for (const auto& pair : keyValuePairs) {
            //LOGGING
            if (pair.first == "LogFile") {
                if (!pair.second.empty()) {
                    try
                    {
                        size_t ldx;
                        auto logfile_status = std::stoi(pair.second, &ldx);
                        gs456hack.logging_enabled = logfile_status;
                        break;
                    }
                    catch (const std::exception&)
                    {
                        gs456hack.logging_enabled = false;
                        break;
                    }
                }
            }
        }
    }
}

void ReadConfig()
{
    // Try reading the 'GS456_hacks.ini' to obtain data
    std::ifstream stream(CProxyStub::instance().m_proxy_path / gs456hack.cfname);

    if (stream.good() || !stream.fail())
    {
        // Create a map to store key-value pairs
        std::map<std::string, std::string> keyValuePairs;

        // Define the default order to process the keys
        std::vector<std::string> order = { "WaitTimeInMsBeforeHook", "FPS", "AnimSpeed", "TextSpeed", "EnableMultipleValues",
            "FPS_Values", "AnimSpeed_Values", "TextSpeed_Values", "SkipFirstValueInLists",
            "FPS_Hotkey", "AnimSpeed_Hotkey", "TextSpeed_Hotkey",
            "FPS_Button", "AnimSpeed_Button", "TextSpeed_Button", "Trigger_Sensitivity"};

        // Read lines until the end of the file
        std::string line;
        while (std::getline(stream, line)) {
            // Skip empty lines and lines starting with '#'
            if (line.empty() || line[0] == '#') {
                continue;
            }

            // get rid of whitespaces
            gs456hack.trim(line);

            // Find the position of '=' in the line
            size_t equalPos = line.find('=');

            // If '=' is found, treat the line as a key-value pair
            if (equalPos != std::string::npos) {
                std::string key = line.substr(0, equalPos);
                std::string value = line.substr(equalPos + 1);

                // Store the key-value pair in the map
                keyValuePairs[key] = value;
            }
        }

        for (const auto& key : order) {
            // Process key-value pairs
            gs456hack.ProcessIntConfig("WaitTimeInMsBeforeHook", keyValuePairs, gs456hack.processedKeys, gs456hack.WaitBeforeMain, "WaitTimeInMsBeforeHook");
            gs456hack.ProcessFloatConfig("FPS", keyValuePairs, gs456hack.processedKeys, gs456hack.gs456_fpsSpeed, "FPS cap");
            gs456hack.ProcessFloatConfig("AnimSpeed", keyValuePairs, gs456hack.processedKeys, gs456hack.gs456_animSpeed, "Animation speed");
            gs456hack.ProcessBooleanConfig("EnableMultipleValues", keyValuePairs, gs456hack.processedKeys, gs456hack.multipleValues_enabled, "EnableMultipleValues");
            gs456hack.ProcessIntVectorConfig("FPS_Values", keyValuePairs, gs456hack.processedKeys, gs456hack.FPS_Values, "FPS_Values");
            gs456hack.ProcessIntVectorConfig("AnimSpeed_Values", keyValuePairs, gs456hack.processedKeys, gs456hack.AnimSpeed_Values, "AnimSpeed_Values");
            gs456hack.ProcessBooleanConfig("SkipFirstValueInLists", keyValuePairs, gs456hack.processedKeys, gs456hack.skipListFirstValues_enabled, "SkipFirstValueInLists");
            gs456hack.ProcessHotkeyConfig("FPS_Hotkey", keyValuePairs, gs456hack.processedKeys, gs456hack.FPS_keyCode, "FPS");
            gs456hack.ProcessHotkeyConfig("AnimSpeed_Hotkey", keyValuePairs, gs456hack.processedKeys, gs456hack.AnimSpeed_keyCode, "AnimSpeed");
            gs456hack.ProcessButtonConfig("FPS_Button", keyValuePairs, gs456hack.processedKeys, gs456hack.FPS_BUTTON, "FPS_Button");
            gs456hack.ProcessButtonConfig("AnimSpeed_Button", keyValuePairs, gs456hack.processedKeys, gs456hack.ANIMSP_BUTTON, "AnimSpeed_Button");
            gs456hack.ProcessCharConfig("Trigger_Sensitivity", keyValuePairs, gs456hack.processedKeys, gs456hack.triggerSensitivity, "Trigger sensitivity");
        }
        gs456hack.config_readable = true;
    }
    else {
        std::string message = "The config file cannot be read/found: " + gs456hack.cfname;
        MessageBoxA(NULL, message.c_str(), "Error", MB_ICONERROR | MB_OK);
        message = "The game will use its default values.";
        MessageBoxA(NULL, message.c_str(), "Information", MB_ICONINFORMATION | MB_OK);
        gs456hack.config_readable = false;
    }
}

// Main thread
DWORD WINAPI MainCycle(LPVOID hModule) {
    // read if logging is enabled or not
    ReadLogStatus();

    // nullify log file at every game start (so that it doesn't bloat up to huge size over time), if it is enabled
    if (gs456hack.logging_enabled) {
        gs456hack.ClearLogFile();
    }

    // read the INI config file
    ReadConfig();

    // if config file didn't go through, don't do anything unnecessarily
    if (!gs456hack.config_readable) {
        return 1;
    }

    // Some sleep is needed first of all, otherwise this will not load properly, if at all
    std::this_thread::sleep_for(std::chrono::milliseconds(gs456hack.WaitBeforeMain));

    // 1. GAME FPS
    SetInitialAddress(gameFPS, gs456hack, gs456hack.gs456_fpsSpeed,
        "Process: FPS cap is set to ", "Error: Failed to set the game's FPS cap to: ",
        "Process: FPS cap was not changed", "Error: Failed to read the game's FPS cap at: ");

    // 2. ANIMATION SPEED
    SetInitialAddress(animSpd, gs456hack, gs456hack.gs456_animSpeed,
        "Process: Animation speed is set to ", "Error: Failed to set the game's animation speed to: ",
        "Process: Animation speed was not changed", "Error: Failed to read the game's animation speed at: ");

    //check if all operations succeeded and quit this thread if so
    if (operationSuccess == 2) {
        gs456hack.Log("*SUCCESS* All initial memory hacks have been applied");
        return 0;
    }

    if (operationSuccess == 0) {
        gs456hack.Log("*FAILURE* Initial memory hacks have not been applied");
        return 1;
    }

    return 0;
}


// Entry point for the DLL
BOOL WINAPI DllMain(HINSTANCE hModule, DWORD ul_reason_for_call, LPVOID lpReserved)
{
    switch (ul_reason_for_call)
    {
        case DLL_PROCESS_ATTACH:
        {
            // This is needed to be able to inject the DLL
            auto result = CProxyStub::instance().resolve(hModule);
            if (!result)
                return FALSE;

            // This is used for the main thread
            result = CreateThread(nullptr, 0x1000, &MainCycle, nullptr, 0, nullptr);
            if (!result)
                return FALSE;

            // This is used for the hotkeys, with "MultipleValues"
            result = CreateThread(nullptr, 0x1000, &KeyPressThread, nullptr, 0, nullptr);
            if (!result)
                return FALSE;

            // This is used for the XInput supported controllers/gamepads, with "MultipleValues"
            result = CreateThread(nullptr, 0x1000, &ControllerPressThread, nullptr, 0, nullptr);
            if (!result)
                return FALSE;

            break;
        }

        case DLL_PROCESS_DETACH:
        {
            break;
        }
    }

    return TRUE;
}