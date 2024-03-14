#pragma once

class GS456Hack
{
/*protected:
    GS456Hack()
    {
    }
*/
public: // for this simple project, this sort of thing doesn't matter too much, at the moment

    // Trim leading and trailing whitespace from a string
    std::string trim(const std::string& str) {
        std::size_t first = str.find_first_not_of(" \t\n\r\f\v");
        std::size_t last = str.find_last_not_of(" \t\n\r\f\v");
        return (first != std::string::npos && last != std::string::npos) ? str.substr(first, last - first + 1) : "";
    }

    // Parse multiple values
    std::vector<int> parseMultipleValues(const std::string& value) {
        std::vector<int> values;

        // Find the opening and closing curly braces
        size_t openBrace = value.find('{');
        size_t closeBrace = value.find('}');

        if (openBrace != std::string::npos && closeBrace != std::string::npos) {
            // Extract the values between the curly braces
            std::string valuesString = value.substr(openBrace + 1, closeBrace - openBrace - 1);

            // Create a stringstream from the values string
            std::istringstream ss(valuesString);

            // Read values from the stringstream into the vector
            int tempValue;
            char discard;
            while (ss >> tempValue) { // Read values until failure
                if (tempValue > 0) {
                    values.push_back(tempValue);
                }

                // Consume the comma (if present)
                if (ss >> discard && discard != ',') {
                    break; // Stop if a non-comma character is encountered
                }
            }
        }

        return values;
    }

    // filenames
    const std::string cfname = "GS456_hacks.ini";
    const std::string lfname = "GS456_hacks.log";

    // config file status
    bool config_readable;

    // logging status (for some debugging or information)
    bool logging_enabled;

    // WaitTimeInMsBeforeHook
    int WaitBeforeMain;

    // FPS values
    float gs456_fpsSpeed;
    float gs456_animSpeed;

    //
    // Multiple values (function)
    //
    bool multipleValues_enabled;

    // skip the first value in the lists
    bool skipListFirstValues_enabled;

    // Hotkeys
    int key1 = 0x74; // FPS
    int key2 = 0x75; // AnimSpeed

    // FPS
    std::vector<int> FPS_Values;
    int FPS_keyCode;

    // AnimSpeed
    std::vector<int> AnimSpeed_Values;
    int AnimSpeed_keyCode;

    // This is for the trigger buttons (LT, RT)
    // Value: 0-255
    // 0 = fully released
    // 255 = fully pressed
    unsigned char triggerSensitivity;

    // button assignments
    unsigned char FPS_BUTTON;
    unsigned char ANIMSP_BUTTON;

    // max controllers for XInput
    const unsigned char MAX_CONTROLLERS = 4;

    // check buttons for Xbox controllers
    bool CheckButtonState(const char* buttonName, WORD buttonFlag, const XINPUT_STATE& state, DWORD controllerIndex, std::unordered_set<WORD>& pressedButtons) {
        if ((state.Gamepad.wButtons & buttonFlag) && pressedButtons.find(buttonFlag) == pressedButtons.end()) {
            pressedButtons.insert(buttonFlag);
            return true;
        }
        else if (!(state.Gamepad.wButtons & buttonFlag) && pressedButtons.find(buttonFlag) != pressedButtons.end()) {
            pressedButtons.erase(buttonFlag);
        }

        return false;
    }

    // check triggers for Xbox controllers
    bool CheckTriggerState(const char* triggerName, BYTE triggerValue, DWORD controllerIndex, std::unordered_set<WORD>& pressedTriggers) {
        if (triggerValue > triggerSensitivity && pressedTriggers.find(triggerValue) == pressedTriggers.end()) {
            pressedTriggers.insert(triggerValue);
            return true;
        }
        else if (triggerValue <= triggerSensitivity && pressedTriggers.find(triggerValue) != pressedTriggers.end()) {
            pressedTriggers.erase(triggerValue);
        }

        return false;
    }

    /// <summary>
    /// Gets the current 'GS456Hack' class instance
    /// </summary>
    static GS456Hack& instance() {
        static GS456Hack instance;
        return instance;
    }

    // Helper function to handle log entry
    template <typename... Args>
    void LogEntry(std::ostream& logStream, const Args&... args) {
        (logStream << ... << args);
    }

    // Main Log function
    template <typename... Args>
    void Log(const Args&... args) {
        if (!logging_enabled) {
            return;
        }

        std::ofstream logFile(lfname, std::ios::app);

        if (!logFile.is_open()) {
            std::string message = "Failed to open log file: " + lfname;
            MessageBoxA(NULL, message.c_str(), "Error", MB_ICONERROR | MB_OK);
            return;
        }

        std::time_t currentTime = std::time(nullptr);
        std::tm localTime;
        localtime_s(&localTime, &currentTime);

        char timeBuffer[80];
        std::strftime(timeBuffer, sizeof(timeBuffer), "%Y-%m-%d %H:%M:%S", &localTime);

        logFile << "[" << timeBuffer << "] ";

        LogEntry(logFile, args...);

        logFile << std::endl;
    }

    void ClearLogFile() {
        try {
            std::ofstream logFile(lfname, std::ios::trunc);
            if (!logFile.is_open()) {
                std::string message = "Failed to open log file: " + lfname;
                MessageBoxA(NULL, message.c_str(), "Error", MB_ICONERROR | MB_OK);
            }
            logFile.close();
        }
        catch (const std::ios_base::failure&) {
            // just go back
            return;
        }
    }


    //
    // Helper functions for processing different config key-value pairs
    //
    std::set<std::string> processedKeys;

    // Float values (FPS, AnimSpeed)
    void ProcessFloatConfig(const std::string& key, std::map<std::string, std::string>& keyValuePairs,
        std::set<std::string>& processedKeys, float& targetVariable, const std::string& configName) {
        auto it = keyValuePairs.find(key);
        if (it != keyValuePairs.end() && processedKeys.insert(key).second) {
            if (!it->second.empty()) {
                try {
                    size_t ldx;
                    auto value = std::stof(it->second, &ldx);

                    if (value > 0) {
                        targetVariable = value;
                    }
                    else {
                        targetVariable = 0;
                    }

                    if (targetVariable == 0) {
                        Log("Config: ", configName, " is set to ", targetVariable, " (not modified)");
                    }
                    else {
                        Log("Config: ", configName, " is set to ", targetVariable);
                    }
                }
                catch (const std::exception&) {
                    targetVariable = 30;
                    Log("Error: Couldn't get ", configName, ". Set to default: ", targetVariable);
                }
            }
        }
    }

    // Int values (WaitTimeInMsBeforeHook)
    void ProcessIntConfig(const std::string& key, std::map<std::string, std::string>& keyValuePairs,
        std::set<std::string>& processedKeys, int& targetVariable, const std::string& configName) {
        auto it = keyValuePairs.find(key);
        if (it != keyValuePairs.end() && processedKeys.insert(key).second) {
            if (!it->second.empty()) {
                try {
                    size_t ldx;
                    auto value = std::stoi(it->second, &ldx);

                    if (value > 0 && value <= 30000) {
                        targetVariable = value;
                    }
                    else {
                        targetVariable = 5000;
                    }

                    Log("Config: ", configName, " is set to ", targetVariable);
                }
                catch (const std::exception&) {
                    targetVariable = 5000;
                    Log("Error: Couldn't get ", configName, ". Set to default: ", targetVariable);
                }
            }
        }
    }

    // Boolean values (EnableMultipleValues) +LogFile (which is not logged)
    void ProcessBooleanConfig(const std::string& key, std::map<std::string, std::string>& keyValuePairs,
        std::set<std::string>& processedKeys, bool& targetVariable, const std::string& configName) {
        auto it = keyValuePairs.find(key);
        if (it != keyValuePairs.end() && processedKeys.insert(key).second) {
            if (!it->second.empty()) {
                try {
                    size_t ldx;
                    auto value = std::stoi(it->second, &ldx);
                    targetVariable = value;
                    Log("Config: ", configName, " is set to ", targetVariable);
                }
                catch (const std::exception&) {
                    targetVariable = false;
                    Log("Error: \"", configName, "\" is disabled");
                }
            }
        }
    }

    // Multiple values (FPS_Values, AnimSpeed_Values, TextSpeed_Values)
    void ProcessIntVectorConfig(const std::string& key, std::map<std::string, std::string>& keyValuePairs,
        std::set<std::string>& processedKeys, std::vector<int>& targetVariable, const std::string& configName) {
        std::string singleString;
        auto it = keyValuePairs.find(key);
        if (it != keyValuePairs.end() && processedKeys.insert(key).second) {
            if (!it->second.empty()) {
                try {
                    targetVariable = parseMultipleValues(it->second);

                    for (auto i = 0; i < targetVariable.size(); ++i) {
                        singleString += std::to_string(targetVariable[i]);
                        if (i < targetVariable.size() - 1) {
                            singleString += ", ";
                        }
                    }

                    Log("Config: ", configName, " multiple values set to {", singleString, "}");
                }
                catch (const std::exception&) {
                    if (targetVariable == FPS_Values) {
                        targetVariable = { 30, 40, 60, 120 };
                    }
                    else if (targetVariable == AnimSpeed_Values) {
                        targetVariable = { 30, 45, 60 };
                    }

                    for (auto i = 0; i < targetVariable.size(); ++i) {
                        singleString += std::to_string(targetVariable[i]);
                        if (i < targetVariable.size() - 1) {
                            singleString += ", ";
                        }
                    }

                    Log("Error: ", configName, " multiple values couldn't be read, set to default {", singleString, "}");

                }
            }
        }
    }

    // Keyboard hotkeys (FPS_Hotkey, AnimSpeed_Hotkey, TextSpeed_Hotkey)
    void ProcessHotkeyConfig(const std::string& key, std::map<std::string, std::string>& keyValuePairs,
        std::set<std::string>& processedKeys, int& targetVariable, const std::string& configName) {
        auto it = keyValuePairs.find(key);
        if (it != keyValuePairs.end() && processedKeys.insert(key).second) {
            if (!it->second.empty()) {
                try {
                    size_t ldx;
                    auto value = std::stoul(it->second, &ldx, 16);  // Convert string to int from hexadecimal

                    // Check if conversion was successful
                    if (ldx == it->second.size()) {
                        targetVariable = static_cast<unsigned int>(value);
                        Log("Config: \"", configName, "\" changing hotkey is set to 0x", std::hex, targetVariable);
                    }
                    else {
                        // Use default if conversion failed
                        if (key == "FPS_Hotkey") {
                            targetVariable = key1;
                        }
                        else if (key == "AnimSpeed_Hotkey") {
                            targetVariable = key2;
                        }
                        Log("Error: Couldn't convert the \"", configName, "\" related hotkey. Set to default 0x", std::hex, targetVariable);
                    }
                }
                catch (const std::exception&) {
                    // Use default if conversion failed
                    if (key == "FPS_Hotkey") {
                        targetVariable = key1;
                    }
                    else if (key == "AnimSpeed_Hotkey") {
                        targetVariable = key2;
                    }
                    Log("Error: Couldn't get the \"", configName, "\" related hotkey. Set to default 0x", std::hex, targetVariable);
                }
            }
        }
    }

    // Button values (FPS_Button, AnimSpeed_Button, TextSpeed_Button)
    void ProcessButtonConfig(const std::string& key, std::map<std::string, std::string>& keyValuePairs,
        std::set<std::string>& processedKeys, unsigned char& targetVariable, const std::string& configName) {
        auto it = keyValuePairs.find(key);
        if (it != keyValuePairs.end() && processedKeys.insert(key).second) {
            if (!it->second.empty()) {
                std::string buttonStr = it->second;
                unsigned char ButtonVar;
                bool couldntSet = false;

                try {
                    if (buttonStr == "A") {
                        ButtonVar = 1;
                    }
                    else if (buttonStr == "B") {
                        ButtonVar = 2;
                    }
                    else if (buttonStr == "X") {
                        ButtonVar = 3;
                    }
                    else if (buttonStr == "Y") {
                        ButtonVar = 4;
                    }
                    else if (buttonStr == "LB") {
                        ButtonVar = 5;
                    }
                    else if (buttonStr == "RB") {
                        ButtonVar = 6;
                    }
                    else if (buttonStr == "Back") {
                        ButtonVar = 7;
                    }
                    else if (buttonStr == "Start") {
                        ButtonVar = 8;
                    }
                    else if (buttonStr == "LS") {
                        ButtonVar = 9;
                    }
                    else if (buttonStr == "RS") {
                        ButtonVar = 10;
                    }
                    else if (buttonStr == "DPadUp") {
                        ButtonVar = 11;
                    }
                    else if (buttonStr == "DPadDown") {
                        ButtonVar = 12;
                    }
                    else if (buttonStr == "DPadLeft") {
                        ButtonVar = 13;
                    }
                    else if (buttonStr == "DPadRight") {
                        ButtonVar = 14;
                    }
                    else if (buttonStr == "LT") {
                        ButtonVar = 15;
                    }
                    else if (buttonStr == "RT") {
                        ButtonVar = 16;
                    }
                    else {

                        // default values
                        if (key == "FPS_Button") {
                            ButtonVar = 15;
                        }
                        else if (key == "AnimSpeed_Button") {
                            ButtonVar = 16;
                        }

                        targetVariable = ButtonVar;
                        Log("Error: Couldn't get the \"", configName, "\" related button. Set to default ", static_cast<unsigned int>(targetVariable));
                        couldntSet = true;
                    }
                    if (!couldntSet) { // don't display this at error
                        targetVariable = ButtonVar;
                        Log("Config: \"", configName, "\" changing gamepad button is set to ", buttonStr);
                    }

                }
                catch (const std::exception&) {
                    // default values
                    if (key == "FPS_Button") {
                        ButtonVar = 15;
                    }
                    else if (key == "AnimSpeed_Button") {
                        ButtonVar = 16;
                    }

                    targetVariable = ButtonVar;
                    Log("Error: Couldn't get the \"", configName, "\" related button. Set to default ", static_cast<unsigned int>(targetVariable));
                }
            }
        }
    }

    // Char values (Trigger_Sensitivity)
    void ProcessCharConfig(const std::string& key, std::map<std::string, std::string>& keyValuePairs,
        std::set<std::string>& processedKeys, unsigned char& targetVariable, const std::string& configName) {
        auto it = keyValuePairs.find(key);
        if (it != keyValuePairs.end() && processedKeys.insert(key).second) {
            if (!it->second.empty()) {
                try {
                    size_t ldx;
                    unsigned char value = std::stoi(it->second, &ldx);

                    if (value >= 0 && value <= 255) {
                        targetVariable = value;
                    }
                    else {
                        targetVariable = 175;
                    }
                    Log("Config: ", configName, " is set to ", static_cast<unsigned int>(targetVariable));
                }
                catch (const std::exception&) {
                    targetVariable = 175;
                    Log("Error: Couldn't get ", configName, ". Set to default: ", static_cast<unsigned int>(targetVariable));
                }
            }
        }
    }

};